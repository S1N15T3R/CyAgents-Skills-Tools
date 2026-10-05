---
name: skill-evolve
description: >-
  Self-improvement layer for this toolkit's bug-bounty skills. Use when the user says "evolve", "improve
  the skills", "sharpen", "why is X missing bugs", "learn from this hunt", or after a batch of hunts /
  after /remember has logged outcomes. Measures each skill/technique's real success rate from hunt memory
  (journal.jsonl) and only promotes an improved or brand-new skill when it PROVABLY beats the incumbent
  (Wilson confidence intervals, minimum sample size, no rise in false positives). Never promotes on vibes.
---

# skill-evolve

For authorized security testing only. This skill makes the toolkit's other skills sharper over time —
but with a hard rule: **a change ships only when the numbers say it is better.** No promotion on
intuition, no silent drift.

## Why a gate exists

"Self-improving" prompts usually rot: they get rewritten on a hunch and quietly lose accuracy. Here,
every skill/technique has a measured **success rate** from real hunt outcomes, and a candidate must clear
a statistical bar before it can replace the incumbent or be added. If it can't, the incumbent stays.

## The data it uses

Everything is computed from hunt memory the toolkit already writes:

- `~/.hermes/hunt-memory/journal.jsonl` — one row per hunt action with `result`
  (`confirmed` / `rejected` / `partial` / `informational`), `vuln_class`, `technique`, `severity`,
  `payout`, `tags`. Written by `/remember` and the hunt tools.
- `~/.hermes/hunt-memory/skill_evolve.jsonl` — the evolution ledger this skill maintains: shadow trials,
  evaluations, and promotions/rejections with their numbers.

**Success rate** for a skill/technique = `confirmed / (confirmed + rejected + partial)`. `informational`
is excluded (neither a win nor a false positive). A high `rejected` share means false positives — the
thing most bug-bounty programs punish via validity ratio, so the gate watches it explicitly.

## The three evolution modes (borrowed from OpenSpace)

1. **FIX** — an existing skill underperforms (low success rate, or a rising rejected rate). Repair the
   specific instruction/payload/bypass that's failing.
2. **DERIVE** — a general skill does well on most surfaces but poorly on a niche (a tech stack, a program
   type). Specialize a child skill for that niche without touching the parent.
3. **CAPTURE** — a technique keeps working across hunts but isn't written down anywhere. Extract it into a
   new skill (or a new section of an existing one).

## The loop (always run the scripts — never eyeball it)

```bash
EV=~/.hermes/skills/security/skill-evolve/scripts        # or ~/BugBounty_toolkit/skills/skill-evolve/scripts

# 1. See where skills stand — success rate + Wilson interval + sample size, weakest first.
python3 "$EV/skill_stats.py" report

# 2. Pick a weak/gappy skill and draft a candidate (FIX/DERIVE/CAPTURE). Write the candidate SKILL.md
#    to a temp path — do NOT touch the live skill yet.

# 3. Run the candidate in SHADOW for a while: when hunting with the candidate's approach, log outcomes
#    tagged as the candidate variant.
python3 "$EV/skill_stats.py" record --skill hunter-idor --variant candidate \
        --result confirmed --vuln-class idor --target acme.com --technique "uuid-decode+replay"

# 4. Ask the gate whether the candidate may ship. Exit code 0 = PROMOTE, non-zero = HOLD/REJECT.
python3 "$EV/evolve_gate.py" --skill hunter-idor

# 5. Only if the gate says PROMOTE, apply it (archives the current version, writes the candidate, logs
#    the decision + numbers to the ledger). The script re-runs the gate itself and refuses otherwise.
python3 "$EV/promote.py" --skill hunter-idor --candidate /tmp/hunter-idor.candidate.md
```

After a promotion, re-run the toolkit installer so the change reaches `~/.claude`
(`bash ~/BugBounty_toolkit/install.sh --agent claude --global --no-burp`).

## The promotion gate (what "much better" means here)

`evolve_gate.py` returns PROMOTE only when **all** hold (defaults; tunable via flags):

| Check | Default | Why |
|---|---|---|
| Candidate trials | `n_cand ≥ 8` | Enough evidence to trust the candidate at all. |
| Baseline trials | `n_base ≥ 8` | A fair comparison needs a real incumbent baseline. |
| Absolute margin | `rate_cand − rate_base ≥ 0.15` | The improvement must be big, not cosmetic. |
| No CI overlap | `wilson_low(cand) > wilson_high(base)` | Even the pessimistic candidate beats the optimistic incumbent — this is the "much higher" guarantee. |
| No new false positives | `rejected_rate(cand) ≤ rejected_rate(base)` | Never trade accuracy for recall. |

If the candidate wins on point estimate but the intervals still overlap, the verdict is **HOLD — gather
more trials**, not promote. If it's worse or noisier, **REJECT**. This is deliberately strict: a bad
promotion poisons every future hunt, so the bar to change is high.

For adding a **brand-new** skill (CAPTURE with no incumbent), the gate treats the baseline as the toolkit's
overall success rate for that vuln class; the new skill must clear that baseline by the same margin before
it's added — so new skills also have to earn their place.

See `references/evolution-protocol.md` for the full protocol, the exact math, and worked examples.

## Guardrails
- Never edit a live skill directly for "improvement" — always draft → shadow → gate → promote.
- Never lower the gate thresholds just to force a promotion; if you must experiment, do it on a copy.
- Evolution operates on *skill quality*, not scope/safety rules — the always-active `rules/` and the
  scope-first stance are not subject to evolution.
