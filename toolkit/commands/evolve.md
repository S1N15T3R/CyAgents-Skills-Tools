---
description: Measure skill success rates from hunt memory and evolve/add a skill only if it provably beats the incumbent
argument-hint: [report | gate --skill <name> | promote --skill <name>]
---

Run the self-improvement loop for this toolkit's skills: **$ARGUMENTS**

Use the `skill-evolve` skill. Never edit a live skill directly for "improvement" — always
draft → shadow → gate → promote, and let the gate decide.

Default flow when no clear sub-request is given:

1. **Measure.** Run `python3 ~/.claude/skills/skill-evolve/scripts/skill_stats.py report` to list skills
   weakest-first (success rate + Wilson interval + sample size). Summarize where the toolkit is missing
   bugs or producing false positives.
2. **Diagnose & draft.** For the weakest/gappiest skill, read the relevant rejected journal rows, decide
   FIX / DERIVE / CAPTURE, and draft a candidate `SKILL.md` to a temp path (do not touch the live skill).
3. **Shadow.** Use the candidate on real in-scope hunts and log outcomes with
   `skill_stats.py record --variant candidate ...` until there are enough trials.
4. **Gate.** Run `python3 ~/.claude/skills/skill-evolve/scripts/evolve_gate.py --skill <name>`.
   Report the verdict (PROMOTE / HOLD / REJECT) and the numbers.
5. **Promote only if PROMOTE.** Run `promote.py --skill <name> --candidate <temp>` (it re-checks the gate
   and archives the incumbent), then re-run `install.sh --agent claude --global --no-burp`.

The rule is strict on purpose: a skill is replaced or added only when its candidate's success rate is
*confidently and substantially* higher than the incumbent's, with no increase in false positives.
Otherwise the incumbent stays. Authorized testing only.
