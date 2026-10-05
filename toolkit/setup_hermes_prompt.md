# Hermes Setup Prompt — sync BugBounty_toolkit into Hermes

Copy everything in the fenced block below and paste it to Hermes **from inside the
cloned repo directory** (`cd toolkit && hermes`). Hermes will synchronize
the whole toolkit into your Hermes install autonomously.

---

```
You are setting up the BugBounty_toolkit (this repo, your current working directory) as a
native Hermes integration. Do every step below, verify each, and give me a final report.
Authorized security testing only.

1. LOCATE. Confirm cwd is the toolkit root (has tools/, skills/, agents/, migrate_skills.py).
   If not, ask me for the path and cd there. Set TOOLKIT=$(pwd).

2. PYTHON DEPS. requirements.txt needs `requests` + `pyyaml`. Check if importable; if not,
   ASK me whether to install into a venv or with --break-system-packages, then install.

3. INSTALL SKILLS. Run `python3 migrate_skills.py`. It copies the 15 domain skills into
   ~/.hermes/skills/security/ (adding Hermes frontmatter + trimming 2 over-limit
   descriptions) and generates the bb-hunter-agents persona catalog from agents/*.md.
   Verify it prints "Total: 16 skills". Confirm `ls ~/.hermes/skills/security/` shows 16 dirs.

4. HUNT MEMORY. The toolkit stores cross-session hunt memory at ~/.hermes/hunt-memory
   (resolved by memory/paths.py, override via $BBHUNT_MEMORY_DIR). Create the dir:
   `mkdir -p ~/.hermes/hunt-memory`. Findings are tagged per-target (per-program isolation);
   patterns match across targets (global skill sharpening).

5. DELEGATION MODEL (optional). Parallel hunter subagents inherit the main model unless set.
   Ask me if I want a cheaper model for them; if yes, `hermes config set delegation.model <m>`
   and `... delegation.provider <p>`. Otherwise skip.

6. EXTERNAL TOOLS. Recon/scan tools (subfinder, httpx, nuclei, katana, dnsx, gau,
   waybackurls, ffuf, sqlmap, arjun, subzy, etc.) are optional — the scripts skip any that
   are missing. Run `python3 tools/hunt.py --status` and tell me which are present vs missing.
   Only install on my say-so; on Kali/PEP-668 ASK venv vs --break-system.

7. MCP SERVERS (optional, ask before doing). The repo documents three:
   - hackerone: a CLI, NOT an MCP server (mcp/hackerone-mcp/server.py has no MCP code) —
     use it as `python3 mcp/hackerone-mcp/server.py search|stats|policy`. Do not register it.
   - burp: real MCP. Needs PortSwigger's mcp-server extension built + loaded in Burp
     (see mcp/burp-mcp-client/README.md), which exposes SSE on 127.0.0.1:9876; Hermes runs
     the proxy jar. GUI steps are the user's.
   - stealth-browser: real MCP (nodriver+CDP). Needs the vibheksoni/stealth-browser-mcp repo
     cloned + a venv. GUI-free.
   If I want either, register by adding an `mcp_servers:` block to ~/.hermes/config.yaml with
   proper YAML lists (command/args/env) — NOT via `hermes config set` (it stringifies lists)
   and NOT via `hermes mcp add` (known asyncio crash). Show me the block before writing it.

8. PER-PROGRAM WORKFLOW. Tell me how to hunt: `bash tools/new_hunt.sh <program> [domain]`
   scaffolds a hunt dir (recon/ findings/ reports/ notes/ scope/ + .hermes.md + hunt.env).
   Then `cd <program> && source hunt.env && hermes` — data lands in that dir because
   hunt.py honors $BBHUNT_WORKSPACE. In-session I ask for: recon, full hunt, continue,
   targeted vuln/endpoint checks, validate, report.

9. VERIFY & REPORT. Confirm `ls ~/.hermes/skills/security/` shows 16 skill dirs, each with a
   SKILL.md. Then summarize: skills installed, memory path, tools present/missing, MCP status,
   and the exact commands I use to start a hunt. Note that a NEW Hermes session is needed for
   the skills to load (the loader caches at startup).

Do NOT run active scans, DoS, or touch any target during setup. This is install-only.
```

---

## What this sets up

- **16 Hermes skills** under `~/.hermes/skills/security/` (15 domain skills + `bb-hunter-agents`)
- **Cross-session hunt memory** at `~/.hermes/hunt-memory` (per-program isolation, global pattern learning)
- **Per-program workspaces** via `tools/new_hunt.sh` — open Hermes in a hunt dir, data saves there
- Optional: delegation model, external recon tools, Burp / stealth-browser MCP servers

## One-liner (if you just want the skills, no prompt)

```bash
cd toolkit
python3 -m pip install --user pyyaml requests   # or in a venv
python3 migrate_skills.py                        # → 16 skills into ~/.hermes/skills/security
mkdir -p ~/.hermes/hunt-memory
# start a fresh `hermes` session so the skills load
```

Full day-to-day usage: see `HERMES_USAGE.md`.
