"""
Central hunt-memory path resolver.

Single source of truth for WHERE hunt memory lives, so every writer/reader
agrees regardless of which harness (Hermes, Claude Code, OpenCode, standalone)
drives the toolkit.

Resolution order:
  1. $BBHUNT_MEMORY_DIR              — explicit override (per-session / per-program)
  2. ~/.hermes/hunt-memory          — Hermes-native default
  3. (legacy) ~/.claude/hunt-memory — only if it already exists AND no Hermes dir

Findings are tagged per-target inside this one store (journal/target profiles
stay bound to their program via the `target` field); patterns match ACROSS
targets by vuln_class + tech_stack for global skill sharpening. So a single
directory gives you both per-program isolation and global learning.
"""

import os
from pathlib import Path

HERMES_DEFAULT = Path.home() / ".hermes" / "hunt-memory"
LEGACY_CLAUDE = Path.home() / ".claude" / "hunt-memory"


def hunt_memory_dir(create: bool = False) -> Path:
    """Return the resolved hunt-memory directory.

    If ``create`` is True the directory (and parents) is created.
    """
    env = os.environ.get("BBHUNT_MEMORY_DIR")
    if env:
        d = Path(os.path.expanduser(env))
    elif HERMES_DEFAULT.exists() or not LEGACY_CLAUDE.exists():
        d = HERMES_DEFAULT
    else:
        d = LEGACY_CLAUDE
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


# Convenience file handles
def journal_path() -> Path:
    return hunt_memory_dir() / "journal.jsonl"


def patterns_path() -> Path:
    return hunt_memory_dir() / "patterns.jsonl"


def audit_path() -> Path:
    return hunt_memory_dir() / "audit.jsonl"


def ledger_path() -> Path:
    return hunt_memory_dir() / "skill_evolve.jsonl"


def targets_dir() -> Path:
    return hunt_memory_dir() / "targets"
