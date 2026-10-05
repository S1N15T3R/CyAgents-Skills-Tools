#!/usr/bin/env python3
"""
evolve_gate.py — the promotion gate. Decides whether a candidate skill variant may replace/become the
incumbent, based on measured success rates. This is the guardrail that makes "self-improvement" safe:
a change ships ONLY when it provably beats the incumbent.

Verdicts (exit codes):
  0  PROMOTE  — candidate cleared every check; safe to promote.
  2  HOLD     — candidate looks better but evidence is insufficient/overlapping; gather more trials.
  3  REJECT   — candidate is not better (or is noisier); keep the incumbent.
  1  ERROR    — bad input / no data.

Gate (all must hold for PROMOTE; defaults tunable via flags):
  n_cand  >= --min-trials (8)
  n_base  >= --min-trials (8)
  rate_cand - rate_base    >= --margin (0.15)          absolute improvement is meaningful
  wilson_low(cand) > wilson_high(base)                  confidence intervals do NOT overlap ("much higher")
  rejected_rate(cand) <= rejected_rate(base) + --fp-tol (0.0)   no rise in false positives

For a brand-new skill (CAPTURE, no baseline variant), pass --baseline-rate R to compare against the
toolkit's overall success rate for that vuln class; the new skill must clear R by --margin with a
wilson_low above R.

Stdlib only. For authorized security testing only.

Usage:
  python3 evolve_gate.py --skill hunter-idor
  python3 evolve_gate.py --skill new-graphql-idor --baseline-rate 0.30 --min-trials 8
  python3 evolve_gate.py --skill hunter-xss --json --margin 0.15 --min-trials 10
"""

import argparse
import json
import os
import sys
from pathlib import Path

# import the stats engine from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skill_stats as ss  # noqa: E402


def evaluate(skill, *, min_trials, margin, fp_tol, baseline_rate=None, journal=None):
    journal_rows = ss._read_jsonl(Path(journal) if journal else ss.JOURNAL)
    ledger_rows = ss._read_jsonl(ss.LEDGER)
    data = ss.collect(journal_rows, ledger_rows)

    variants = data.get(skill, {})
    cand = variants.get("candidate")

    if cand is None or cand.n == 0:
        return {
            "verdict": "ERROR",
            "reason": f"No candidate trials for '{skill}'. Record shadow trials with "
                      f"skill_stats.py record --variant candidate first.",
        }

    base = variants.get("baseline")
    new_skill = base is None or base.n == 0

    # Resolve baseline numbers
    if new_skill:
        if baseline_rate is None:
            return {
                "verdict": "ERROR",
                "reason": f"'{skill}' has no baseline variant. This looks like a NEW skill (CAPTURE): "
                          f"pass --baseline-rate R (e.g. the toolkit's overall success rate for this "
                          f"vuln class) so the new skill still has to earn its place.",
            }
        base_rate = float(baseline_rate)
        base_low, base_high = base_rate, base_rate  # a fixed reference line, no interval
        base_n = None
        # No incumbent FP rate to match. Allow the new skill's rejected rate up to the failure budget
        # implied by the reference success rate (1 - base_rate): it must not be noisier than the
        # reference itself would be. This still blocks a high-recall-but-sloppy new skill.
        base_rej = 1.0 - base_rate
    else:
        base_rate = base.rate
        base_low, base_high = ss.wilson_interval(base.confirmed, base.n)
        base_n = base.n
        base_rej = base.rejected_rate

    cand_low, cand_high = ss.wilson_interval(cand.confirmed, cand.n)

    checks = []

    def check(name, passed, detail):
        checks.append({"check": name, "pass": bool(passed), "detail": detail})
        return passed

    ok_cand_n = check("candidate_min_trials", cand.n >= min_trials,
                      f"n_cand={cand.n} (need >= {min_trials})")
    if new_skill:
        ok_base_n = check("baseline_reference", True,
                          f"new skill; baseline_rate reference = {base_rate:.3f}")
    else:
        ok_base_n = check("baseline_min_trials", base_n >= min_trials,
                          f"n_base={base_n} (need >= {min_trials})")

    margin_val = cand.rate - base_rate
    ok_margin = check("absolute_margin", margin_val >= margin,
                      f"rate_cand={cand.rate:.3f} - base={base_rate:.3f} = {margin_val:+.3f} "
                      f"(need >= {margin:.3f})")

    ok_no_overlap = check("ci_no_overlap", cand_low > base_high,
                          f"wilson_low(cand)={cand_low:.3f} must be > wilson_high(base)={base_high:.3f}")

    ok_fp = check("no_new_false_positives", cand.rejected_rate <= base_rej + fp_tol,
                  f"rejected_rate(cand)={cand.rejected_rate:.3f} must be <= "
                  f"base={base_rej:.3f} + tol {fp_tol:.3f}")

    all_pass = ok_cand_n and ok_base_n and ok_margin and ok_no_overlap and ok_fp

    if all_pass:
        verdict = "PROMOTE"
        reason = "Candidate beats the incumbent on every check."
    else:
        # HOLD only when more evidence could plausibly flip the verdict: the candidate is directionally
        # better, not noisier, and the failure is thin data / interval overlap WHILE the observed margin
        # clears the bar. REJECT when the gap is genuinely too small or the candidate is noisier.
        directionally_better = margin_val > 0 and cand.rejected_rate <= base_rej + fp_tol
        thin_or_overlap = (not ok_cand_n) or (not ok_base_n) or (not ok_no_overlap)
        # "ample data" = both sides already well-sampled; more trials won't rescue a small true gap.
        ample_data = (not new_skill) and cand.n >= 2 * min_trials and base_n >= 2 * min_trials
        margin_hopeless = (not ok_margin) and ample_data

        if directionally_better and ok_fp and ok_margin and thin_or_overlap:
            verdict = "HOLD"
            reason = ("Candidate's observed gain clears the margin but the evidence is insufficient or the "
                      "confidence intervals still overlap. Gather more shadow trials, then re-run the gate.")
        elif directionally_better and ok_fp and (not ok_margin) and not margin_hopeless:
            verdict = "HOLD"
            reason = ("Candidate is directionally better but below the required margin on limited data. "
                      "Gather more shadow trials, then re-run the gate.")
        else:
            verdict = "REJECT"
            if margin_hopeless:
                reason = ("Candidate's improvement is too small to matter despite ample data "
                          f"({margin_val:+.3f} < required {margin:.3f}). Keep the incumbent.")
            else:
                reason = ("Candidate is not provably better (or introduces more false positives). "
                          "Keep the incumbent.")

    return {
        "skill": skill,
        "verdict": verdict,
        "reason": reason,
        "new_skill": new_skill,
        "candidate": {**cand.as_dict(), "wilson_low": round(cand_low, 4), "wilson_high": round(cand_high, 4)},
        "baseline": ({"reference_rate": round(base_rate, 4)} if new_skill
                     else {**base.as_dict(), "wilson_low": round(base_low, 4),
                           "wilson_high": round(base_high, 4)}),
        "thresholds": {"min_trials": min_trials, "margin": margin, "fp_tol": fp_tol},
        "checks": checks,
    }


VERDICT_EXIT = {"PROMOTE": 0, "HOLD": 2, "REJECT": 3, "ERROR": 1}


def main(argv=None):
    p = argparse.ArgumentParser(description="Promotion gate for evolving a skill.")
    p.add_argument("--skill", required=True)
    p.add_argument("--min-trials", type=int, default=8)
    p.add_argument("--margin", type=float, default=0.15,
                   help="Required absolute success-rate improvement (default 0.15 = 15 points).")
    p.add_argument("--fp-tol", type=float, default=0.0,
                   help="Allowed increase in rejected/false-positive rate (default 0.0).")
    p.add_argument("--baseline-rate", type=float, default=None,
                   help="Reference rate for a brand-new skill with no baseline variant.")
    p.add_argument("--journal", default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    result = evaluate(args.skill, min_trials=args.min_trials, margin=args.margin,
                      fp_tol=args.fp_tol, baseline_rate=args.baseline_rate, journal=args.journal)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        v = result["verdict"]
        print(f"VERDICT: {v} — {result['reason']}")
        if "checks" in result:
            for c in result["checks"]:
                mark = "PASS" if c["pass"] else "FAIL"
                print(f"  [{mark}] {c['check']}: {c['detail']}")
            cand = result["candidate"]; base = result["baseline"]
            print(f"  candidate: n={cand['n']} succ={cand['success_rate']*100:.1f}% "
                  f"CI[{cand['wilson_low']*100:.1f}..{cand['wilson_high']*100:.1f}] "
                  f"rej={cand['rejected_rate']*100:.1f}%")
            if result["new_skill"]:
                print(f"  baseline:  reference_rate={base['reference_rate']*100:.1f}%")
            else:
                print(f"  baseline:  n={base['n']} succ={base['success_rate']*100:.1f}% "
                      f"CI[{base['wilson_low']*100:.1f}..{base['wilson_high']*100:.1f}] "
                      f"rej={base['rejected_rate']*100:.1f}%")

    return VERDICT_EXIT.get(result["verdict"], 1)


if __name__ == "__main__":
    sys.exit(main())
