# CyAgents Skills & Tools

A self-contained, agent-portable **bug-bounty / offensive-security toolkit**: skills, sub-agents,
slash commands, and the Python/shell scanners they call — all vendored into one repo so a fresh
clone works with **zero external setup**.

> **Authorized testing only.** Everything here is meant for assets inside an active bug-bounty
> program's scope (HackerOne / Bugcrowd / Intigriti / Immunefi / self-hosted with written
> safe-harbor terms), or your own systems. Scope first, always.

---

## Layout

```
CyAgents-Skills-Tools/
├── apihunter/        skills + tools — API / GraphQL / IDOR / OAuth / JWT / gRPC
├── webattack/        skills + tools — XSS, SQLi, SSTI, SSRF, CSRF, uploads, ATO, logic
├── infrahacker/      skills + tools — cloud, SSRF, CORS, k8s, CI/CD, host-header, takeover
├── vulnresearch/     skills + tools — RCE, deserialization, smuggling, cache poison, race, LLM/RAG
├── recon/            skills + tools — subdomain/URL recon, SPA/API discovery, arsenal
├── osint/            skills + tools — offensive OSINT, credential/leak hunting, supply chain
├── mobilehunter/     skills + tools — Android/iOS pentest, client reversing
├── reportwriter/     skills + tools — H1/Bugcrowd reporting, evidence hygiene
├── verifier/         skills + tools — triage / validation gates
├── orchestrator/     skills + tools — master methodology, scope triage, skill-evolve
│
├── toolkit/          ← vendored BugBounty_toolkit (the engine the skills call)
│   ├── tools/            ~40 scanners + hunt.py orchestrator
│   ├── skills/           15 skill domains
│   ├── agents/           28 sub-agents
│   ├── commands/         28 slash commands
│   ├── wordlists/        starter lists + references
│   ├── memory/           hunt-memory engine (pattern DB, audit log, rotation)
│   ├── mcp/              burp / caido / hackerone MCP clients
│   ├── rules/            always-active hunting & reporting rules
│   └── web3/             13-chapter smart-contract audit guide
│
├── mcp/              HackerOne MCP server (uses toolkit/ tools)
└── raw/              reference material (third-party skill repos)
```

Every `*/tools/` directory holds **real files** (not symlinks) — clone and run, nothing to repair.

---

## Quick start

### 1. Use the skills with an agent

Skills are plain `SKILL.md` files. Point your agent at the domain folder you need, e.g.
`webattack/skills/hunt-idor/SKILL.md`. Each skill is self-contained and references tools by
repo-relative path (`toolkit/tools/...`).

### 2. Run the tools directly

```bash
git clone https://github.com/S1N15T3R/CyAgents-Skills-Tools
cd CyAgents-Skills-Tools

python3 -m pip install -r toolkit/requirements.txt     # requests + pytest

# orchestrator
python3 toolkit/tools/hunt.py --help

# recon pipeline
bash toolkit/tools/recon_engine.sh target.com

# scope safety check (always run before touching an asset)
python3 toolkit/tools/scope_checker.py <asset>
```

### 3. Install the toolkit's skills into your harness

```bash
cd toolkit
./install.sh --agent claude --global --no-burp   # Claude Code
./install.sh --agent opencode                    # OpenCode
./install.sh --agent agents                      # ~/.agents/skills (shared)
./install.sh --agent all                         # every supported target
```

---

## External tools

Many scanners **wrap** well-known external tools (subfinder, httpx, nuclei, ffuf, katana, arjun,
dalfox, sqlmap, …) and degrade gracefully when one is missing. `toolkit/tools/external_arsenal.sh`
is the registry; run it to see what's installed and get install hints:

```bash
bash toolkit/tools/external_arsenal.sh          # list
bash toolkit/tools/external_arsenal.sh <tool>   # install hint
```

Wordlist and payload sources are listed in `toolkit/wordlists/REFERENCES.md`.

---

## Secrets

No credentials are committed. API keys are read from environment variables at runtime
(`BBHUNT_*`, `GITHUB_TOKEN`, provider keys, …) — see `toolkit/config.example.json`. Runtime
output (`findings/`, `reports/`, `recon/`, `hunt-memory/`, `.env`, `config.json`) is git-ignored.

---

## License

See `toolkit/LICENSE`. Third-party material under `raw/` keeps its own upstream license.
