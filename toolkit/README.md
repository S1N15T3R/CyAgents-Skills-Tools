# BugBounty_toolkit

**An AI-native bug-bounty & pentest toolkit for Claude Code — recon to report, in one disciplined loop.**

> **For authorized security testing only.** Use this only against assets covered by an active bug-bounty
> program scope, a signed engagement, or systems you own. Every workflow here is scope-first: confirm
> authorization before any active testing, stay in scope, never DoS or exfiltrate real user data beyond
> a minimal PoC.

It wires **skills** (loadable domain knowledge + runnable scanners), **agents** (focused sub-hunters you
can dispatch in parallel), and **slash commands** into Claude Code, backed by a cross-session **hunt
memory** and a self-improving **skill-evolve** layer. The whole thing enforces one loop:

```
        ┌──────────────────────── pivot / new surface / chain ───────────────────────┐
        ▼                                                                             │
   scope  ──▶  recon  ──▶  hunt  ──▶  validate  ──▶  report ───────────────────────┘
   /scope     /recon      /hunt      /validate       /report
```

## Using this with Hermes Agent

This toolkit also runs natively in [Hermes Agent](https://hermes-agent.nousresearch.com).
To sync everything (15 skills + a 28-persona hunter catalog, hunt memory, per-program
workspaces) into your Hermes install, open Hermes in this repo and paste the prompt from
**[`setup_hermes_prompt.md`](setup_hermes_prompt.md)** — Hermes does the rest.

Or just install the skills directly:

```bash
python3 migrate_skills.py       # → 16 skills into ~/.hermes/skills/security (needs pyyaml)
mkdir -p ~/.hermes/hunt-memory  # cross-session hunt memory
# start a fresh `hermes` session so the skills load
```

Per-program hunting: `bash tools/new_hunt.sh <program> [domain]` scaffolds a hunt dir,
then `cd <program> && source hunt.env && hermes`. Full guide: **[`HERMES_USAGE.md`](HERMES_USAGE.md)**.

---

## Features

### Skills (15) — domain playbooks Claude loads on demand
| Skill | What it gives you |
|---|---|
| `bb-methodology` | The master mindset + 5-phase non-linear workflow + tool routing + session discipline. Start here. |
| `bug-bounty` | End-to-end reference — recon, pre-hunt learning, every web2 vuln class, LLM/AI testing, A→B→C chaining, reporting. |
| `web2-recon` | Subdomain enum, live-host discovery, crawling, JS analysis, continuous monitoring. |
| `web2-vuln-classes` | 24 bug classes with root causes, detection patterns, bypass tables, and real paid examples. |
| `security-arsenal` | Payloads, bypass tables, `gf` patterns, and the always-rejected / conditionally-valid lists. |
| `triage-validation` | The 7-Question Gate + 4 validation gates + CVSS. Kills weak findings before they cost you N/A ratio. |
| `report-writing` | Impact-first templates for HackerOne / Bugcrowd / Intigriti / Immunefi, human tone, CVSS. |
| `web3-audit` | 10 smart-contract bug classes, pre-dive kill signals, Foundry PoC template. |
| `graphql-audit` | Introspection, clairvoyance field discovery, batching DoS, IDOR-via-aliasing, injection, depth bombs. |
| `credential-attack` | Password-spray methodology with legal guardrails and a hard stop before any live spray. |
| `cicd-security` | GitHub Actions injection, secret exfil, runner poisoning, OIDC abuse, supply-chain. |
| `mobile-pentest` | Android/iOS runtime-first proxy workflow, APK/IPA decompile, deeplink/WebView abuse, SSL-pinning bypass. |
| `meme-coin-audit` | Token rug-pull detection (EVM + Solana), authority checks, bonding-curve & LP attacks. |
| `web-testing-browser` | **Drive a real Chrome from the CLI** — persistent authenticated session, two-account IDOR diffing, DOM/network capture. |
| `skill-evolve` | **Self-improvement** — measures each skill/technique's real success rate from hunt memory and only promotes an improved or new skill when it *provably* beats the incumbent. |

### Agents (28) — dispatch focused hunters, in parallel
- **Workflow:** `recon-agent`, `recon-ranker`, `validator`, `chain-builder`, `autopilot`, `report-writer`,
  `web3-auditor`, `token-auditor`, `credential-hunter`.
- **Scope & analysis:** `scope-check` (conservative gatekeeper), `js-analyzer` (endpoints/secrets/DOM sinks),
  `devils-advocate` (tries to disprove/downgrade a finding before you submit).
- **16 `hunter-*` specialists:** access-control, idor, xss, ssrf, sqli, ssti, xxe, auth, csrf, cors,
  open-redirect, subdomain-takeover, race-condition, business-logic, rce, file-upload. Each reads
  `web2-vuln-classes` (payloads in `security-arsenal`) and routes findings to `validator` →
  `chain-builder` → `report-writer`.

### Commands (28) — one-line drivers
`/recon` `/hunt` `/validate` `/report` `/chain` `/scope` `/scope-aggregate` `/triage` `/surface`
`/pickup` `/autopilot` `/remember` `/intel` `/secrets-hunt` `/takeover` `/cloud-recon` `/param-discover`
`/bypass-403` `/scan-cves` `/graphql-audit` `/osint-employees` `/breach-check` `/wordlist-gen` `/spray`
`/token-scan` `/web3-audit` `/arsenal` `/memory-gc` `/evolve`.

### Tools (~40 scanners in `tools/`)
Python/shell pipeline that degrades gracefully — every tool checks whether its external dependency is
installed and skips (never errors) if not. Highlights: `hunt.py` (orchestrator), `recon_engine.sh`,
`vuln_scanner.sh`, `validate.py` (4-gate validator), `scope_checker.py` (deterministic scope safety on
every request), `secrets_hunter.sh`, `takeover_scanner.sh`, `cloud_recon.sh`, `graphql_audit.sh`,
`token_scanner.py`.

### Hunt memory (`memory/` → `~/.claude/hunt-memory/`)
Findings and successful techniques from one target carry to the next: `pattern_db.py` (cross-target
patterns), a `journal.jsonl` of every outcome (`confirmed`/`rejected`/`partial`) with vuln class,
technique, severity and payout, `audit_log.py` (request audit + rate limiter + circuit breaker), and
size-capped rotation. Manage with `/remember`, `/pickup`, `/memory-gc`. **This journal is also the fuel
for `skill-evolve`.**

### MCP integrations (`mcp/`)
`burp-mcp-client` and `caido-mcp-client` (proxy through Burp/Caido), `hackerone-mcp` (Hacktivity, program
stats, scope/policy), and `stealth-browser-mcp.json` (nodriver + CDP stealth browser for bot-protected
targets — pairs with the `web-testing-browser` skill).

### Web3 field guide (`web3/`) & standalone CLI
A 13-chapter smart-contract audit guide, plus a subscription-free standalone `bughunter` CLI
(`engine.py`/`brain.py`/`agent.py`) that runs the same pipeline outside Claude Code.

---

## Install

```bash
# 1. Claude Code (global) — copies skills, agents, commands into ~/.claude
bash toolkit/install.sh --agent claude --global --no-burp

# 2. (optional) external recon/scan tools — subfinder, httpx, nuclei, ffuf, sqlmap, ...
bash toolkit/install_tools.sh

# 3. (optional) browser skill deps — Puppeteer
cd toolkit/skills/web-testing-browser/scripts && bash install-deps.sh && npm install

# 4. (optional) standalone CLI, no Claude subscription needed
bash toolkit/install.sh --agent standalone   # then: bughunter recon target.com
```

The installer **copies** (does not symlink), so after editing any toolkit file, re-run step 1 to push the
change into `~/.claude`. Missing external tools are always skipped, never fatal. Uninstall with
`bash toolkit/uninstall.sh`. Restart Claude Code (or start a new session) after installing so
the skills, agents, and commands load.

> Other harnesses: `install.sh --agent opencode|pi|codex|agents|all` install for OpenCode, Pi, Codex, and
> the shared `~/.agents/skills` layout.

---

## Usage — the loop

```bash
claude
```

```text
/scope app.target.com            # confirm the asset is in an authorized scope (conservative gatekeeper)
/recon target.com                # full recon pipeline → recon/target.com/
/surface target.com              # rank the surface P1/P2/kill from recon + memory
/hunt target.com                 # active hunt; or dispatch a specialist directly (see below)
/validate                        # 7-Question Gate + 4 gates on the current finding
/chain                           # combine low/medium findings into a higher-impact chain
/report                          # write the submission-ready report (run after /validate passes)
/remember                        # log the confirmed finding/technique to hunt memory
```

**Dispatch specialists in parallel.** Ask Claude to run several hunters at once against ranked surface —
e.g. “run `hunter-idor`, `hunter-ssrf`, and `hunter-access-control` on the P1 API endpoints.” Each returns
a structured finding (title, endpoint, repro, impact, confidence) and self-routes to `validator`.

**Authenticated / interactive testing.** Use the `web-testing-browser` skill: log in once, then every
script reuses that session for DOM-XSS confirmation, two-account IDOR diffing, and API/token capture. For
Cloudflare/Queue-It-protected targets, use the stealth browser MCP (`mcp/`).

**Autonomy.** `/autopilot target.com --normal` runs the whole loop with checkpoints
(`--paranoid` / `--normal` / `--yolo`).

**Get sharper over time.** After a batch of hunts, run `/evolve` — it reads your hunt journal, finds
where a technique or skill is underperforming, proposes an improved or specialized version, and promotes
it **only if it provably beats the incumbent** (see below).

---

## Self-improvement: `skill-evolve`

Most "self-improving" setups drift — they rewrite prompts on vibes and quietly get worse. `skill-evolve`
refuses to promote anything that isn't measurably better:

- It scores each skill/technique/vuln-class from the hunt `journal.jsonl` — success rate =
  `confirmed / (confirmed + rejected + partial)` — with **Wilson confidence intervals** so small samples
  can't masquerade as signal.
- A candidate (a FIXed, DERIVEd, or CAPTUREd skill) is run in a labeled **shadow period**, then the
  **promotion gate** requires *all* of: enough samples on both sides, a meaningful absolute margin, the
  candidate's confidence-interval **lower** bound above the incumbent's **upper** bound (no overlap), and
  **no rise in the false-positive/rejected rate**.
- Only then is the incumbent version-archived and the new skill written, with the decision and the numbers
  appended to an evolution **ledger**. Otherwise the candidate is rejected (or kept in shadow to gather
  more data) — the incumbent stays.

See `skills/skill-evolve/SKILL.md` and `references/evolution-protocol.md`.

---

## Layout

```
toolkit/  (BugBounty_toolkit — vendored)
├── README.md  CLAUDE.md  AGENTS.md  install.sh  install_tools.sh  uninstall*.sh
├── skills/        15 skill domains (each a SKILL.md + optional scripts/references)
├── agents/        28 sub-agents (hunter-*, workflow, analysis)
├── commands/      28 slash commands
├── tools/         ~40 Python/shell scanners + hunt.py orchestrator
├── memory/        hunt-memory engine (pattern_db, journal, audit, rotation)
├── mcp/           burp / caido / hackerone clients + stealth-browser config
├── rules/         always-active hunting & reporting rules
├── hooks/         session hooks
├── web3/          13-chapter smart-contract audit guide
├── wordlists/     starter lists + references
├── engine.py brain.py agent.py    standalone `bughunter` CLI
└── docs/  tests/  scripts/  site/
```

---

## Safety & ethics

Authorized testing only. The toolkit bakes in: scope-first checks (`/scope`, `scope_checker.py`),
rate-limiting and no-DoS, a hard stop before any credential spray, minimal non-destructive PoCs, and a
"report only reproducible, in-scope, impactful findings" gate. You are responsible for staying within each
program's rules and safe-harbor terms.

---

## Credits

This toolkit is built on the outstanding work of the open-source security community. The **core**
(skills, agents, commands, tools, hunt memory, web3 guide, standalone CLI) is vendored from and credited to:

- **[shuvonsec/claude-bug-bounty](https://github.com/shuvonsec/claude-bug-bounty)** (BugHunter, MIT) —
  upstream commit `b2e9eb7`, 2026-06-21. The foundation of everything here.

Local additions layered on top, themselves drawing on:

- **[mrgoonie/claudekit-skills](https://github.com/mrgoonie/claudekit-skills)** (Apache-2.0) — the
  chrome-devtools Puppeteer scripts adapted into `web-testing-browser`.
- **[vibheksoni/stealth-browser-mcp](https://github.com/vibheksoni/stealth-browser-mcp)** (MIT) — the
  stealth browser MCP referenced in `mcp/`.
- **[six2dez/reconftw](https://github.com/six2dez/reconftw)** & **[hahwul/WebHackersWeapons](https://github.com/hahwul/WebHackersWeapons)** (MIT)
  — recon methodology and tool-arsenal references.
- **[anthropics/skills](https://github.com/anthropics/skills)** — the skill-authoring format and the
  success-gated evolution idea behind `skill-evolve`.

All trademarks and tools belong to their respective authors. See `LICENSE` for the upstream MIT license.
