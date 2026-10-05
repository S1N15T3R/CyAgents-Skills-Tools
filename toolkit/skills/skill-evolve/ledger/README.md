# Evolution ledger

The ledger is a JSONL file the `skill-evolve` scripts append to. It lives with the rest of hunt memory at:

```
~/.hermes/hunt-memory/skill_evolve.jsonl
```

(not in this repo — it's per-machine state, alongside `journal.jsonl`). This directory is a placeholder so
the layout is documented.

## Row types

- `{"type":"trial", ...}` — a shadow trial for a `baseline` or `candidate` variant (written by
  `skill_stats.py record`).
- `{"type":"promotion", ...}` — an applied promotion, including the archive path and the full gate result
  (written by `promote.py`).
- `{"type":"decision", ...}` — a non-applied gate decision (HOLD/REJECT) recorded when a promotion was
  refused.

Together these give the full lineage of how each skill evolved and why — every change is auditable and
reversible (each promotion snapshots the prior version under `skills/<skill>/.versions/<timestamp>/`).
