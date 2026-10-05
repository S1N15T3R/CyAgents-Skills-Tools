#!/usr/bin/env python3
"""
promote.py — apply a skill evolution, but ONLY if the gate says PROMOTE.

This is the sole path that mutates a live skill. It re-runs evolve_gate.py internally and refuses to do
anything unless the verdict is PROMOTE (override requires the explicit --force flag, which is logged as a
manual override in the ledger — use only for a brand-new skill you are adding by hand).

On PROMOTE it:
  1. Snapshots the current skill dir to skills/<skill>/.versions/<timestamp>/ (nothing is lost).
  2. Writes the candidate file over the live SKILL.md (or creates a new skill dir for a CAPTURE add).
  3. Appends a promotion record (with the gate's numbers) to ~/.hermes/hunt-memory/skill_evolve.jsonl.

After running this, re-run migrate_skills.py to push the change into ~/.hermes/skills/security:
  bash toolkit/install.sh --agent claude --global --no-burp

Stdlib only. For authorized security testing only.

Usage:
  python3 promote.py --skill hunter-idor --candidate /tmp/hunter-idor.candidate.md
  python3 promote.py --skill new-graphql-idor --candidate /tmp/new.md --baseline-rate 0.30 --new
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skill_stats as ss          # noqa: E402
import evolve_gate as gate        # noqa: E402

# skills/ root = two levels up from this scripts/ dir  (skills/skill-evolve/scripts/ -> skills/)
SKILLS_ROOT = Path(__file__).resolve().parents[2]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _ts_slug():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main(argv=None):
    p = argparse.ArgumentParser(description="Promote a skill evolution (gated).")
    p.add_argument("--skill", required=True, help="Skill name (dir under skills/).")
    p.add_argument("--candidate", required=True, help="Path to the candidate SKILL.md content.")
    p.add_argument("--new", action="store_true", help="This is a brand-new skill (CAPTURE add).")
    p.add_argument("--baseline-rate", type=float, default=None,
                   help="Reference rate for a new skill (passed to the gate).")
    p.add_argument("--min-trials", type=int, default=8)
    p.add_argument("--margin", type=float, default=0.15)
    p.add_argument("--fp-tol", type=float, default=0.0)
    p.add_argument("--force", action="store_true",
                   help="Override a non-PROMOTE verdict (logged as manual override). Discouraged.")
    p.add_argument("--journal", default=None)
    args = p.parse_args(argv)

    candidate_path = Path(args.candidate)
    if not candidate_path.is_file():
        print(f"ERROR: candidate file not found: {candidate_path}", file=sys.stderr)
        return 1

    # 1. Run the gate.
    result = gate.evaluate(args.skill, min_trials=args.min_trials, margin=args.margin,
                           fp_tol=args.fp_tol, baseline_rate=args.baseline_rate, journal=args.journal)
    verdict = result["verdict"]
    print(f"Gate verdict: {verdict} — {result['reason']}")

    if verdict != "PROMOTE" and not args.force:
        print("Refusing to promote. The incumbent stays. "
              "Gather more trials (HOLD) or keep the incumbent (REJECT).", file=sys.stderr)
        # record the rejection so the ledger tells the full story
        ss._append_jsonl(ss.LEDGER, {
            "type": "decision", "ts": _now(), "skill": args.skill,
            "verdict": verdict, "applied": False, "gate": result,
        })
        return gate.VERDICT_EXIT.get(verdict, 1)

    if verdict != "PROMOTE" and args.force:
        print("WARNING: --force overriding a non-PROMOTE verdict. Logging as manual override.",
              file=sys.stderr)

    skill_dir = SKILLS_ROOT / args.skill
    live_skill_md = skill_dir / "SKILL.md"

    # 2a. Snapshot the incumbent (if it exists).
    snapshot = None
    if skill_dir.exists():
        snapshot = skill_dir / ".versions" / _ts_slug()
        snapshot.mkdir(parents=True, exist_ok=True)
        for item in skill_dir.iterdir():
            if item.name == ".versions":
                continue
            dest = snapshot / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        print(f"Archived incumbent -> {snapshot}")
    elif not args.new:
        print(f"ERROR: skill dir {skill_dir} does not exist. Use --new to add a brand-new skill.",
              file=sys.stderr)
        return 1

    # 2b. Write the candidate over the live SKILL.md.
    skill_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidate_path, live_skill_md)
    print(f"Wrote candidate -> {live_skill_md}")

    # 3. Ledger record.
    ss._append_jsonl(ss.LEDGER, {
        "type": "promotion", "ts": _now(), "skill": args.skill,
        "verdict": verdict, "forced": bool(args.force and verdict != "PROMOTE"),
        "applied": True,
        "archived_to": str(snapshot) if snapshot else None,
        "candidate_source": str(candidate_path),
        "gate": result,
    })
    print(f"Logged promotion -> {ss.LEDGER}")
    print("\nNext: re-run migrate_skills.py so ~/.hermes/skills/security picks up the change:")
    print("  bash toolkit/install.sh --agent claude --global --no-burp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
