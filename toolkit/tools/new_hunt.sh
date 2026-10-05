#!/usr/bin/env bash
# new_hunt — scaffold a per-program bug-bounty hunting directory for use with Hermes.
#
# Usage:
#   new_hunt <program-name> [target-domain]      # create ./<program-name>/ under cwd
#   new_hunt --here <program-name> [domain]      # scaffold the CURRENT directory
#
# What it does:
#   - Creates the hunt dir (recon/ findings/ reports/ notes/ scope/).
#   - Drops a .hermes.md that (a) loads the standing hunting rules and
#     (b) tells Hermes this is a hunt workspace, so `hunt.py` writes HERE.
#   - Drops a .envrc + hunt.env exporting BBHUNT_WORKSPACE + PATH so the
#     toolkit scripts find go/bin tools and save data in this dir.
#   - Seeds scope/SCOPE.md and notes/SESSION.md.
#
# Then: cd into the dir, `source hunt.env` (or use direnv), open Hermes, and hunt.
set -euo pipefail

# Toolkit root = parent of this script's tools/ dir (portable; no hardcoded path).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT="$(cd "$SCRIPT_DIR/.." && pwd)"
HERE=0
if [ "${1:-}" = "--here" ]; then HERE=1; shift; fi

PROGRAM="${1:-}"
DOMAIN="${2:-}"
if [ -z "$PROGRAM" ]; then
  echo "usage: new_hunt <program-name> [target-domain]"
  echo "       new_hunt --here <program-name> [target-domain]"
  exit 1
fi

if [ "$HERE" = "1" ]; then
  DIR="$(pwd)"
else
  DIR="$(pwd)/$PROGRAM"
  mkdir -p "$DIR"
fi

cd "$DIR"
mkdir -p recon findings reports notes scope

# --- hunt.env : source this (or use direnv) to activate the workspace ---
cat > hunt.env <<EOF
# Bug-bounty workspace env for program: $PROGRAM
# Activate:  source hunt.env    (or install direnv and 'direnv allow')
export BBHUNT_WORKSPACE="$DIR"
export BBHUNT_MEMORY_DIR="\${BBHUNT_MEMORY_DIR:-\$HOME/.hermes/hunt-memory}"
export PATH="\$HOME/go/bin:\$HOME/.local/bin:/usr/local/bin:\$PATH"
EOF

# direnv convenience (no-op if direnv not installed)
echo 'source ./hunt.env' > .envrc

# --- .hermes.md : Hermes auto-loads this when cwd is here (walks to git root) ---
cat > .hermes.md <<EOF
# Bug Bounty Hunt Workspace — $PROGRAM

This directory is an authorized bug-bounty hunt workspace. All program data
(recon/, findings/, reports/, notes/, scope/) is saved HERE.

## Session bootstrap (do this first every session)
- This is a HUNTING session. Load the \`bb-methodology\` skill and follow scope → recon → hunt → validate → report.
- Toolkit lives at $TOOLKIT. Run its scripts with the workspace env active so
  output lands in THIS dir: \`source hunt.env\` sets \$BBHUNT_WORKSPACE="$DIR".
- Hunt memory (cross-program learning) is at ~/.hermes/hunt-memory; findings are
  tagged per-target so this program stays isolated while patterns learn globally.

## Standing hunting rules (always active)
- READ FULL SCOPE FIRST — confirm every asset via \`python3 $TOOLKIT/tools/scope_checker.py --asset <asset>\` before any active request. Scope notes in scope/SCOPE.md.
- NEVER hunt theoretical bugs — "Can an attacker do this RIGHT NOW, real user, real harm?" If no, stop.
- KILL weak findings fast (7-Question Gate via triage-validation skill) before writing a report.
- 5-minute rule; automation for recon only; impact-first; A→B chaining; sibling-endpoint rule.
- Hard limits: in-scope only, no DoS, no real-user-data exfil beyond PoC, safe-harbor only.

## How I hunt here (commands)
- "recon $DOMAIN"            → \`BBHUNT_WORKSPACE="$DIR" python3 $TOOLKIT/tools/hunt.py --target $DOMAIN --recon-only\`
- "full hunt $DOMAIN"        → \`BBHUNT_WORKSPACE="$DIR" python3 $TOOLKIT/tools/hunt.py --target $DOMAIN\`
- "continue" / "pickup"      → read recon/ + findings/ + notes/SESSION.md, resume where left off
- "check <vuln/endpoint>"    → targeted hunt; load web2-vuln-classes + security-arsenal, or dispatch a hunter-* persona (bb-hunter-agents)
- "validate" / "report"      → triage-validation then report-writing skills
- One-liner arsenal: web2-recon skill → references/recon-oneliners.md

Full usage guide: $TOOLKIT/HERMES_USAGE.md
EOF

# --- seed scope + session notes ---
cat > scope/SCOPE.md <<EOF
# Scope — $PROGRAM
Target: ${DOMAIN:-<add primary domain>}

## In scope
- 

## Out of scope
- 

## Excluded bug classes
- 

## Safe-harbor / notes
- 
EOF

cat > notes/SESSION.md <<EOF
# $PROGRAM — Hunt Journal

## Crown jewels (what an attacker wants most)
- 

## Active leads (not confirmed)
- 

## Dead ends (don't revisit)
- 

## Confirmed findings
- 
EOF

# init a git repo so .hermes.md is bounded to this dir (walks stop at git root)
if [ ! -d .git ]; then git init -q 2>/dev/null || true; fi

echo "✓ Hunt workspace ready: $DIR"
echo "  next:  cd \"$DIR\" && source hunt.env   # then open Hermes and hunt"
echo "  scope: edit scope/SCOPE.md before any active testing"
