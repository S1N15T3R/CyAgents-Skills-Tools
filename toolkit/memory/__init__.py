"""
Hunt memory system — persistent journal, pattern database, and schema validation.

Runtime data stored at $BBHUNT_MEMORY_DIR, else ~/.hermes/hunt-memory/
(legacy ~/.claude/hunt-memory is still read if it exists and no Hermes dir does).
Use memory.paths.hunt_memory_dir() to resolve the location.
This package contains the code (read/write/validate), not the data.
"""

from memory.paths import (
    hunt_memory_dir,
    journal_path,
    patterns_path,
    audit_path,
    ledger_path,
    targets_dir,
)

from memory.schemas import (
    validate_journal_entry,
    validate_target_profile,
    validate_pattern_entry,
    validate_audit_entry,
)
from memory.pattern_db import PatternDB
from memory.audit_log import AuditLog, RateLimiter, CircuitBreaker
from memory.rotation import (
    DEFAULT_KEEP,
    DEFAULT_MAX_BYTES,
    list_backups,
    purge_backups,
    rotate,
    rotate_if_needed,
    total_bytes,
)

__all__ = [
    "validate_journal_entry",
    "validate_target_profile",
    "validate_pattern_entry",
    "validate_audit_entry",
    "PatternDB",
    "AuditLog",
    "RateLimiter",
    "CircuitBreaker",
    "DEFAULT_KEEP",
    "DEFAULT_MAX_BYTES",
    "list_backups",
    "purge_backups",
    "rotate",
    "rotate_if_needed",
    "total_bytes",
]
