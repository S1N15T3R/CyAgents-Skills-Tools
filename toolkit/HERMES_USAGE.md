# BugBounty_toolkit on Hermes — Usage Guide

Authorized security testing only. Test only assets inside an active bug-bounty
program's scope (HackerOne / Bugcrowd / Intigri / Immunefi / self-hosted with
written safe-harbor terms). Everything here is scope-first.

The toolkit is integrated **natively into Hermes** — no Claude Code required.
This guide assumes the integration is already installed (skills under
`~/.hermes/skills/security/`, toolkit at `toolkit`).

---

## Per-program hunt directories (recommended workflow)

Hunt each program in its own directory so all data (recon/, findings/, reports/,
notes/, scope/) stays with that program. `hunt.py` honors `$BBHUNT_WORKSPACE` and
writes there instead of into the toolkit.

**Create a workspace:**
```bash
# from wherever you keep hunts, e.g. ~/hunts
bash toolkit/tools/new_hunt.sh acme-corp app.acme.com
#   → creates ./acme-corp/ with recon/ findings/ reports/ notes/ scope/,
#     a .hermes.md (auto-loads rules + workspace context for Hermes),
#     hunt.env (exports BBHUNT_WORKSPACE + PATH), scope/SCOPE.md, notes/SESSION.md
# Scaffold an existing dir instead:  new_hunt.sh --here acme-corp app.acme.com
```

**Then hunt:**
```bash
cd acme-corp
source hunt.env          # activates BBHUNT_WORKSPACE + go/bin PATH (or use direnv)
hermes                   # open Hermes HERE — .hermes.md auto-loads the rules
```
Now ask Hermes: "recon app.acme.com", "full hunt app.acme.com", "continue from
existing work", "check the API endpoints for IDOR", "validate", "report".
All output lands in this dir; hunt memory (cross-program learning) stays global
at `~/.hermes/hunt-memory` with per-target isolation.

> If you skip `source hunt.env`, hunt.py falls back to writing inside the toolkit
> (legacy behavior). Sourcing it (or opening Hermes in a `new_hunt`-scaffolded dir)
> is what routes data into the program folder.

---

## 0. Before you start any hunt

1. Read the program's **full scope** — in-scope domains, out-of-scope exclusions,
   excluded bug classes, and safe-harbor clause.
2. `cd toolkit` — this auto-loads the standing hunting
   rules (`AGENTS.md`) into Hermes every session.
3. Confirm the asset is in scope before any active request:
   ```bash
   python3 tools/scope_checker.py --asset <asset>
   ```
4. New Hermes session needed for skills to appear (`skills list` is cached at
   startup). Start fresh if you just installed.

---

## 1. The loop (recon → hunt → validate → report)

Just talk to Hermes in natural language from inside the toolkit directory.
Each phrase below maps to the underlying script (run from the toolkit root).

| Say / ask for            | What runs |
|---|---|
| `recon target.com`       | `python3 tools/hunt.py --target target.com` (recon phase) or `bash tools/recon_engine.sh target.com` |
| `hunt target.com`        | `python3 tools/hunt.py --target target.com` — full pipeline (recon → scan) |
| `hunt target.com --quick`| faster, fewer checks |
| `hunt target.com --scan-only` | scan only (recon already done) |
| `scope <asset>`          | `python3 tools/scope_checker.py --asset <asset>` |
| `surface target.com`     | ranked attack surface from recon + memory |
| `token-scan <contract>`  | `python3 tools/token_scanner.py <contract>` |
| `scan-cves <host>`       | `bash tools/cve_scan.sh <host>` |
| `bypass-403 <url>`       | `bash tools/bypass_403.sh "<url>"` |
| `cloud-recon --keyword <name>` | `bash tools/cloud_recon.sh --keyword <name>` |
| `takeover --recon <dir>` | `bash tools/takeover_scanner.sh --recon <dir>` |
| `param-discover <url>`   | `bash tools/param_discovery.sh <url>` |
| `secrets-hunt --js-bundle <dir>` | `bash tools/secrets_hunter.sh --js-bundle <dir>` |
| `graphql-audit <url>`    | `bash tools/graphql_audit.sh <url>` |
| `memory-gc`              | `python3 tools/memory_gc.py` (rotates `~/.hermes/hunt-memory`) |
| `evolve`                 | `python3 skills/skill-evolve/scripts/skill_stats.py report` then `evolve_gate.py` |

Analysis/dispatch workflows (no single script — follow the skill):
`validate`, `report`, `chain`, `triage`, `intel`, `pickup`, `remember`,
`scope-aggregate`, `autopilot`, `spray`, `osint-employees`, `breach-check`,
`wordlist-gen`, `web3-audit`, `arsenal`.

---

## 2. The skills (load on demand)

Tell Hermes which domain you're working in and the skill loads the full method.
Highest-value ones to know:

| Skill | Use it for |
|---|---|
| `bug-bounty` | The master workflow — recon to report, all vuln classes, chains |
| `bb-methodology` | Hunting mindset + 5-phase workflow + what to do next |
| `web2-recon` | Subdomain enum, live-host discovery, crawling, JS analysis |
| `web2-vuln-classes` | 24 bug classes with root causes, bypass tables, real paid examples |
| `security-arsenal` | Payloads, bypass tables, gf patterns, always-rejected list |
| `triage-validation` | 7-Question Gate + 4 validation gates — run BEFORE any report |
| `report-writing` | H1/Bugcrowd/Intigriti/Immunefi templates, CVSS, human tone |
| `web3-audit` | 10 DeFi bug classes, Foundry PoC template, kill signals |
| `meme-coin-audit` | Token rug-pull detection (EVM + Solana) |
| `graphql-audit` | Introspection, clairvoyance, batching DoS, IDOR-via-aliasing |
| `credential-attack` | Password-spray pipeline + legal guardrails (hard stop before spray) |
| `cicd-security` | GitHub Actions injection, secret exfil, runner poisoning, OIDC |
| `mobile-pentest` | Android/iOS proxy + decompile + WebView/SSL-pin bypass |
| `web-testing-browser` | Drive a real Chrome — authenticated DOM testing, IDOR diffing |
| `skill-evolve` | Self-improvement — only promotes a skill when it provably beats the incumbent |
| `bb-hunter-agents` | 28 specialist personas for parallel dispatch (see §4) |

Load one explicitly: `skill bug-bounty` (or just describe the task — Hermes
loads the matching skill from its description).

---

## 3. Validate & report (do this every time)

1. Before writing anything: **run the 7-Question Gate** — say `validate` and
   describe the finding. One wrong answer = kill it and move on.
2. After it passes: `report` to draft a submission-ready report (impact-first,
   human tone, no "could potentially").
3. Rules that save your validity ratio:
   - **Never hunt theoretical bugs** — "Can an attacker do this RIGHT NOW,
     against a real user, causing real harm?" If no → stop.
   - **5-minute rule** — nothing after 5 min on a surface → move on.
   - **Kill weak findings fast** — every minute on a weak lead is a minute not
     finding a real one.
   - **A→B signal** — confirm bug A, then hunt B and C (chains pay 3-10×).
   - **Sibling rule** — test every sibling endpoint (export/delete/share/print).

---

## 4. Parallel hunting with specialist agents

The 28 specialist personas live in the `bb-hunter-agents` skill. Dispatch them
in parallel via Hermes subagents (they inherit the free model by default).

Example: *"Using the bb-hunter-agents skill, run hunter-idor, hunter-ssrf, and
hunter-access-control on the P1 API endpoints from recon/target.com/, in
parallel. Two test accounts are mine; replay account A's requests as account B."*

Persona catalog (each reads its skill, routes findings to validator →
chain-builder → report-writer):

- **Workflow:** recon-agent, recon-ranker, validator, chain-builder, autopilot,
  report-writer, web3-auditor, token-auditor, credential-hunter
- **Analysis:** scope-check (conservative gatekeeper), js-analyzer (endpoints/
  secrets/DOM sinks), devils-advocate (tries to disprove your finding)
- **16 hunter-* specialists:** access-control, auth, business-logic, cors, csrf,
  file-upload, idor, open-redirect, race-condition, rce, sqli, ssti, xxe, ssrf,
  subdomain-takeover, xss

---

## 5. Hunt memory (cross-session, cross-program)

- Stored at **`~/.hermes/hunt-memory/`** (repointed from the old `~/.claude`).
- Findings are **tagged per target** (the `target` field) — `/pickup target.com`
  only sees that program. Patterns match **across targets** by vuln class +
  tech stack, so skills sharpen globally while findings stay scoped.
- Log a finding: `remember` (or it auto-logs at session end).
- Resume a program: `pickup target.com`.
- Inspect / rotate: `python3 tools/memory_gc.py`.
- For a specific program dir, set `BBHUNT_MEMORY_DIR=/path/to/dir` (overrides
  the default).

---

## 6. HackerOne intel (CLI, not MCP)

The HackerOne helper is a CLI, not an MCP server. Use it directly:

```bash
python3 mcp/hackerone-mcp/server.py search "ssrf" --program <handle> --limit 5
python3 mcp/hackerone-mcp/server.py stats  <program>
python3 mcp/hackerone-mcp/server.py policy <program>
```

(If a call errors on a GraphQL field, it's HackerOne's live schema drift in the
upstream script — re-run or use the web UI for that data.)

---

## 7. Available tooling (already installed)

Present: `subfinder httpx nuclei dnsx katana waybackurls gau ffuf sqlmap
subjack arjun`. Missing optional tools are **skipped gracefully** by the scripts
(`_have` checks) — runs still complete, just without that scanner.

To install more later (Kali/PEP 668 — always choose one and confirm first):
- venv: `python3 -m venv venv && venv/bin/pip install <pkg>`
- system: `pip install --break-system-packages <pkg>`

---

## 8. MCP servers (deferred — external deps absent)

These are real MCP servers but need their binaries first:
- **Burp** — needs `burp-mcp-server.jar` (set `BURP_API_KEY`).
- **Caido** — needs `npx @caido/mcp-server` (set `CAIDO_API_KEY`/`CAIDO_URL`).
- **Stealth browser** — needs the cloned `stealth-browser-mcp` repo + venv
  (nodriver + CDP) for bot-protected targets.

When installed, register via `hermes mcp add <name> --command ... --args ...`.
(Note: `hermes mcp add` has a known crash on "Event loop is closed" — if it
fails, the server config may need a manual `mcp_servers:` block in
`~/.hermes/config.yaml`.)

---

## 9. Quick-start cheat sheet

```bash
# one-time, per program
cd toolkit
python3 tools/scope_checker.py --asset target.com

# the loop
#  "recon target.com"   -> subdomains, live hosts, URLs, nuclei
#  "hunt target.com"    -> active scan
#  "surface target.com" -> ranked attack surface
#  "hunt target.com --quick"
#  "validate"           -> 7-Question Gate on the finding
#  "report"             -> draft submission
#  "remember"           -> log to memory
#  "pickup target.com"  -> resume next session

# parallel specialists
#  "run hunter-idor + hunter-ssrf on the P1 endpoints (bb-hunter-agents)"
```

**Hard limits, always:** never test out-of-scope assets; never exfiltrate or
persist real user data beyond the PoC; never DoS; never social-engineer real
employees; stay inside the safe-harbor clause. You are responsible for every
request the toolkit sends.
