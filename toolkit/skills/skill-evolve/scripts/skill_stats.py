#!/usr/bin/env python3
"""
skill_stats.py — measure bug-bounty skill/technique success rates from hunt memory.

Reads the hunt journal (~/.hermes/hunt-memory/journal.jsonl) and the evolution ledger
(~/.hermes/hunt-memory/skill_evolve.jsonl), computes per-skill / per-variant success rates with
Wilson score confidence intervals, and reports weakest-first.

Also records shadow trials for a candidate skill variant so evolve_gate.py can compare it against the
incumbent.

Success rate = confirmed / (confirmed + rejected + partial). `informational` is excluded.
Rejected rate = rejected / (confirmed + rejected + partial)  (proxy for false-positive rate).

Stdlib only. For authorized security testing only.

Usage:
  python3 skill_stats.py report [--journal PATH] [--min-samples N]
  python3 skill_stats.py show --skill hunter-idor
  python3 skill_stats.py record --skill hunter-idor --variant candidate|baseline \
          --result confirmed|rejected|partial|informational \
          [--vuln-class idor] [--technique "..."] [--target acme.com] [--notes "..."]
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
# Hermes-native default: ~/.hermes/hunt-memory, overridable via $BBHUNT_MEMORY_DIR.
# Falls back to legacy ~/.hermes/hunt-memory only if it exists and no Hermes dir does.
def _resolve_mem_dir() -> Path:
    env = os.environ.get("BBHUNT_MEMORY_DIR")
    if env:
        return Path(os.path.expanduser(env))
    hermes = HOME / ".hermes" / "hunt-memory"
    legacy = HOME / ".claude" / "hunt-memory"
    return hermes if (hermes.exists() or not legacy.exists()) else legacy

MEM_DIR = _resolve_mem_dir()
JOURNAL = MEM_DIR / "journal.jsonl"
LEDGER = MEM_DIR / "skill_evolve.jsonl"

SUCCESS = "confirmed"
FAILURE = "rejected"
PARTIAL = "partial"
INFO = "informational"
COUNTED = {SUCCESS, FAILURE, PARTIAL}  # informational is ignored in rates


# --------------------------------------------------------------------------- math
def wilson_interval(successes: int, n: int, z: float = 1.96):
    """Wilson score confidence interval for a binomial proportion.

    Returns (low, high). Robust for small n, unlike the normal approximation.
    z=1.96 -> ~95% confidence.
    """
    if n == 0:
        return (0.0, 1.0)  # no evidence -> widest possible interval
    p = successes / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    margin = (z * math.sqrt((p * (1 - p) + z2 / (4 * n)) / n)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


# --------------------------------------------------------------------------- io
def _read_jsonl(path: Path):
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"WARNING: {path.name} line {lineno} is not valid JSON (skipping): {e}",
                      file=sys.stderr)
    return rows


def _append_jsonl(path: Path, entry: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _now():
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- stats
class Tally:
    __slots__ = ("confirmed", "rejected", "partial", "informational")

    def __init__(self):
        self.confirmed = self.rejected = self.partial = self.informational = 0

    def add(self, result: str):
        if result == SUCCESS:
            self.confirmed += 1
        elif result == FAILURE:
            self.rejected += 1
        elif result == PARTIAL:
            self.partial += 1
        elif result == INFO:
            self.informational += 1

    @property
    def n(self):  # counted attempts (excludes informational)
        return self.confirmed + self.rejected + self.partial

    @property
    def rate(self):
        return (self.confirmed / self.n) if self.n else 0.0

    @property
    def rejected_rate(self):
        return (self.rejected / self.n) if self.n else 0.0

    def as_dict(self):
        low, high = wilson_interval(self.confirmed, self.n)
        return {
            "confirmed": self.confirmed,
            "rejected": self.rejected,
            "partial": self.partial,
            "informational": self.informational,
            "n": self.n,
            "success_rate": round(self.rate, 4),
            "rejected_rate": round(self.rejected_rate, 4),
            "wilson_low": round(low, 4),
            "wilson_high": round(high, 4),
        }


# map a journal row to a skill name. A row can carry an explicit `skill` tag
# (tags like "skill:hunter-idor"); otherwise we fall back to vuln_class.
VULN_TO_SKILL = {
    "idor": "hunter-idor", "access-control": "hunter-access-control", "bola": "hunter-idor",
    "xss": "hunter-xss", "ssrf": "hunter-ssrf", "sqli": "hunter-sqli", "ssti": "hunter-ssti",
    "xxe": "hunter-xxe", "auth": "hunter-auth", "csrf": "hunter-csrf", "cors": "hunter-cors",
    "open-redirect": "hunter-open-redirect", "subdomain-takeover": "hunter-subdomain-takeover",
    "race-condition": "hunter-race-condition", "business-logic": "hunter-business-logic",
    "rce": "hunter-rce", "file-upload": "hunter-file-upload",
}


def _skill_of(row: dict) -> str:
    for t in row.get("tags", []) or []:
        if isinstance(t, str) and t.startswith("skill:"):
            return t.split("skill:", 1)[1]
    vc = (row.get("vuln_class") or "").lower()
    return VULN_TO_SKILL.get(vc, vc or "unknown")


def _variant_of(row: dict) -> str:
    for t in row.get("tags", []) or []:
        if isinstance(t, str) and t.startswith("variant:"):
            return t.split("variant:", 1)[1]
    return "baseline"


def collect(journal_rows, ledger_rows):
    """Return {skill: {variant: Tally}} merging journal (baseline) + ledger shadow trials."""
    data = {}

    def bucket(skill, variant):
        return data.setdefault(skill, {}).setdefault(variant, Tally())

    for row in journal_rows:
        result = row.get("result")
        if result not in COUNTED and result != INFO:
            continue
        bucket(_skill_of(row), _variant_of(row)).add(result)

    # ledger shadow-trial rows: {"type":"trial","skill":..,"variant":..,"result":..}
    for row in ledger_rows:
        if row.get("type") != "trial":
            continue
        result = row.get("result")
        if result not in COUNTED and result != INFO:
            continue
        bucket(row.get("skill", "unknown"), row.get("variant", "baseline")).add(result)

    return data


def overall_rate_for_skill(data, skill):
    """Baseline success rate for a skill from its baseline variant (journal-derived)."""
    v = data.get(skill, {}).get("baseline")
    return v.rate if v else 0.0


# --------------------------------------------------------------------------- commands
def cmd_report(args):
    journal = _read_jsonl(Path(args.journal) if args.journal else JOURNAL)
    ledger = _read_jsonl(LEDGER)
    data = collect(journal, ledger)

    rows = []
    for skill, variants in data.items():
        for variant, tally in variants.items():
            d = tally.as_dict()
            d["skill"] = skill
            d["variant"] = variant
            rows.append(d)

    # weakest first: lowest success rate, then largest sample (more certain it's weak)
    rows.sort(key=lambda r: (r["success_rate"], -r["n"]))

    if args.json:
        print(json.dumps(rows, indent=2))
        return 0

    if not rows:
        print(f"No hunt outcomes found. Journal: {JOURNAL}")
        print("Log outcomes with /remember (or skill_stats.py record) first.")
        return 0

    print(f"Skill success rates  (journal: {JOURNAL})")
    print(f"{'skill':28} {'variant':10} {'n':>4} {'succ%':>6} {'rej%':>6} {'wilson[low..high]':>20}")
    print("-" * 80)
    for r in rows:
        flag = ""
        if r["n"] < args.min_samples:
            flag = "  (thin data)"
        print(f"{r['skill']:28} {r['variant']:10} {r['n']:>4} "
              f"{r['success_rate']*100:>5.1f}% {r['rejected_rate']*100:>5.1f}% "
              f"  {r['wilson_low']*100:>5.1f}..{r['wilson_high']*100:<5.1f}{flag}")
    print("-" * 80)
    print("Weakest skills are listed first. Candidates for FIX/DERIVE/CAPTURE. Run evolve_gate.py before "
          "changing anything.")
    return 0


def cmd_show(args):
    journal = _read_jsonl(JOURNAL)
    ledger = _read_jsonl(LEDGER)
    data = collect(journal, ledger)
    variants = data.get(args.skill)
    if not variants:
        print(f"No data for skill '{args.skill}'.")
        return 1
    out = {v: t.as_dict() for v, t in variants.items()}
    print(json.dumps({"skill": args.skill, "variants": out}, indent=2))
    return 0


def cmd_record(args):
    entry = {
        "type": "trial",
        "ts": _now(),
        "skill": args.skill,
        "variant": args.variant,
        "result": args.result,
        "vuln_class": args.vuln_class,
        "technique": args.technique,
        "target": args.target,
        "notes": args.notes,
    }
    _append_jsonl(LEDGER, entry)
    print(f"Recorded {args.variant} trial for {args.skill}: {args.result} -> {LEDGER}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Measure skill success rates from hunt memory.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("report", help="Table of all skills/variants, weakest first.")
    pr.add_argument("--journal", help="Path to journal.jsonl (default: ~/.hermes/hunt-memory/journal.jsonl)")
    pr.add_argument("--min-samples", type=int, default=8, help="Flag skills with fewer counted attempts.")
    pr.add_argument("--json", action="store_true")
    pr.set_defaults(func=cmd_report)

    ps = sub.add_parser("show", help="Detailed stats for one skill (JSON).")
    ps.add_argument("--skill", required=True)
    ps.set_defaults(func=cmd_show)

    pc = sub.add_parser("record", help="Record a shadow trial for a candidate/baseline variant.")
    pc.add_argument("--skill", required=True)
    pc.add_argument("--variant", required=True, choices=["baseline", "candidate"])
    pc.add_argument("--result", required=True, choices=[SUCCESS, FAILURE, PARTIAL, INFO])
    pc.add_argument("--vuln-class", default=None)
    pc.add_argument("--technique", default=None)
    pc.add_argument("--target", default=None)
    pc.add_argument("--notes", default=None)
    pc.set_defaults(func=cmd_record)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
