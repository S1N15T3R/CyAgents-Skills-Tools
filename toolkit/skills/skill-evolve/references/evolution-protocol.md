# Evolution protocol — the full method

Authorized testing only. This is how `skill-evolve` sharpens the toolkit's skills without ever shipping a
regression. The golden rule: **draft → shadow → gate → promote**, and the gate is non-negotiable.

## 1. Measure (skill_stats.py)

Every hunt outcome is a data point. `/remember` writes journal rows; each row's `result` is one of
`confirmed`, `rejected`, `partial`, `informational`. For any skill/technique/variant:

- **success rate** = `confirmed / (confirmed + rejected + partial)`
- **rejected rate** (false-positive proxy) = `rejected / (confirmed + rejected + partial)`
- **Wilson 95% interval** around the success rate — the honest uncertainty band given the sample size.

We use Wilson (not the naive normal approximation) because bug-bounty samples are small, and Wilson stays
correct near 0% and 100% and for tiny `n`. A skill with 3/3 confirmed looks like 100% but its Wilson
interval is roughly 44%–100% — the gate will not let 3 samples beat a well-established incumbent.

Run `skill_stats.py report` to list skills weakest-first. The weak ones (low rate, or a rising rejected
rate) are your evolution candidates.

## 2. Choose a mode

- **FIX** — the skill is genuinely underperforming. Diagnose *which* instruction/payload/bypass fails
  (read the rejected journal rows and their notes), and repair exactly that. Don't rewrite the whole skill.
- **DERIVE** — the parent skill is fine overall but weak on a niche (a framework, a program type, an API
  style). Create a specialized child (e.g. `hunter-idor-graphql`) so the parent is untouched and the child
  competes only on its niche.
- **CAPTURE** — a technique keeps working in your journal but isn't written anywhere. Extract it into a new
  skill or a new section. New skills still face the gate (against a baseline reference rate).

## 3. Shadow (don't touch the live skill yet)

Write the candidate content to a temp path (e.g. `/tmp/hunter-idor.candidate.md`). Then *use it* on real,
in-scope hunts and log each outcome as the candidate variant:

```bash
python3 skill_stats.py record --skill hunter-idor --variant candidate \
        --result confirmed --vuln-class idor --target acme.com --technique "uuid-decode+replay"
```

Keep the incumbent's baseline numbers flowing too (normal `/remember` journal rows count as `baseline`).
Shadow until you have at least `--min-trials` (default 8) candidate outcomes. Small samples are the #1 way
self-improvement fools itself — resist promoting early.

## 4. Gate (evolve_gate.py)

The candidate ships only if **all** hold:

| Check | Meaning |
|---|---|
| `n_cand ≥ 8` and `n_base ≥ 8` | Both sides have real evidence. |
| `rate_cand − rate_base ≥ 0.15` | The gain is big, not cosmetic (15 points by default). |
| `wilson_low(cand) > wilson_high(base)` | **No interval overlap** — even the pessimistic candidate beats the optimistic incumbent. This is the "much higher success rate" guarantee. |
| `rejected_rate(cand) ≤ rejected_rate(base)` | It didn't buy recall with more false positives (validity ratio matters). |

Verdicts: **PROMOTE** (all pass), **HOLD** (better but thin/overlapping — gather more), **REJECT** (not
better or noisier). Exit codes 0/2/3 let you gate automation on it.

### Worked examples

- Incumbent 12/20 = 60% (CI ~39–78%). Candidate 9/10 = 90% (CI ~60–98%). Intervals overlap (candidate low
  60% is not > incumbent high 78%). → **HOLD**: promising, but run more candidate trials.
- Incumbent 30/60 = 50% (CI ~38–62%). Candidate 26/28 = 93% (CI ~77–98%). 93−50 = 43 pts ≥ 15, and
  77% > 62% (no overlap), rejected rate not worse. → **PROMOTE**.
- Incumbent 40/50 = 80%. Candidate 9/10 = 90% but with 3 rejected vs incumbent's low rejected rate. →
  **REJECT** on the false-positive check even though raw success looks higher.

## 5. Promote (promote.py)

`promote.py` re-runs the gate itself and refuses unless PROMOTE. On success it archives the incumbent to
`skills/<skill>/.versions/<timestamp>/` (full rollback available), writes the candidate over the live
`SKILL.md`, and appends a promotion record — with the gate's numbers — to the ledger. Then re-run the
installer to push the change to `~/.claude`.

## Rollback

Every promotion snapshots the previous version. To roll back, copy the archived version from
`skills/<skill>/.versions/<timestamp>/` back over the live files and re-run the installer. The ledger
(`~/.hermes/hunt-memory/skill_evolve.jsonl`) is the lineage: every trial, decision, and promotion in order.

## What is NOT subject to evolution
Scope and safety rules (`rules/`, `scope_checker.py`, the scope-first stance, the credential-spray hard
stop) are fixed. Evolution improves *how well we find bugs*, never *whether we're allowed to*.
