#!/usr/bin/env python3
"""Migrate BugBounty_toolkit skills into ~/.hermes/skills/security/ (Hermes-native).

- Copies each skills/<name>/ dir preserving references/ scripts/ subdirs.
- Adds version/author/license + metadata.hermes (tags, related_skills) to every SKILL.md.
- Trims the 2 descriptions that exceed Hermes' 1024-char hard limit.
"""
import re, shutil, pathlib, yaml

# Portable: SRC = the skills/ dir next to this script (no hardcoded home path).
SRC = pathlib.Path(__file__).resolve().parent / "skills"
DST = pathlib.Path.home() / ".hermes/skills/security"
DST.mkdir(parents=True, exist_ok=True)

ALL = [p.name for p in sorted(SRC.iterdir()) if (p / "SKILL.md").exists()]
TAGS = ["security", "bug-bounty", "pentest"]

# Trimmed trigger descriptions for the two over-limit skills.
TRIM = {
    "bug-bounty": (
        "Complete bug bounty workflow — recon to report for authorized programs. Covers "
        "subdomain enumeration, pre-hunt learning from disclosed reports, vulnerability hunting "
        "across all web2 classes (IDOR, SSRF, XSS, auth bypass, CSRF, race, SQLi, XXE, file "
        "upload, business logic, GraphQL, smuggling, cache poisoning, OAuth/OIDC, SSTI, takeover, "
        "cloud, ATO chains, agentic AI), LLM/AI security testing, A->B bug chaining, bypass tables, "
        "language-specific grep, and reporting via the 7-Question Gate + 4 validation gates. Use "
        "for ANY bug bounty task: new target, recon, specific vuln hunting, source review, AI "
        "feature testing, validating findings, or writing reports."
    ),
    "web2-vuln-classes": (
        "Reference for 24 web2 bug classes — root causes, detection patterns, bypass tables, "
        "exploit techniques, and real paid examples. Covers IDOR, auth bypass, XSS, SSRF (11 IP "
        "bypasses), SQLi, business logic, race conditions, OAuth/OIDC, file upload (10 bypasses), "
        "GraphQL, LLM/agentic AI (ASI01-ASI10), API misconfig (mass assignment, JWT, prototype "
        "pollution, CORS), ATO paths, SSTI, subdomain takeover, cloud misconfig, HTTP smuggling, "
        "cache poisoning, MFA bypass, SAML, error/debug endpoints, CSS injection, LFI/RCE, and "
        "insecure deserialization. Use when hunting a specific vuln class or studying what pays."
    ),
}

def split_fm(text):
    assert text.startswith("---"), "no frontmatter"
    m = re.search(r"\n---\s*\n", text[3:])
    fm = yaml.safe_load(text[3:m.start()+3])
    body = text[m.end()+3:]
    return fm, body

def serialize_fm(fm):
    block = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=10**9).strip()
    return f"---\n{block}\n---\n"

for name in ALL:
    # copy tree
    d = DST / name
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(SRC / name, d)

    sk = d / "SKILL.md"
    text = sk.read_text()
    fm, body = split_fm(text)

    # reformat over-limit descriptions
    if name in TRIM:
        fm["description"] = TRIM[name]
    assert len(fm["description"]) <= 1024, f"{name} description still over: {len(fm['description'])}"

    # add metadata block if missing
    if "version" not in fm:
        fm["version"] = "1.0.0"
    if "author" not in fm:
        fm["author"] = "BugBounty_toolkit (shuvonsec/claude-bug-bounty + local)"
    if "license" not in fm:
        fm["license"] = "MIT"
    if "metadata" not in fm:
        fm["metadata"] = {}
    meta = fm["metadata"]
    if "hermes" not in meta:
        meta["hermes"] = {}
    h = meta["hermes"]
    h["tags"] = TAGS
    # cross-link: every skill points at the hub + the common report/validate handoffs
    others = [n for n in ALL if n != name]
    h["related_skills"] = ["bb-methodology"] + [n for n in ("report-writing", "triage-validation") if n in others] + \
                          [n for n in others if n not in ("bb-methodology", "report-writing", "triage-validation")][:6]

    sk.write_text(serialize_fm(fm) + body)

    # verify with hermes validator expectations
    txt2 = sk.read_text()
    mm = re.search(r"\n---\s*\n", txt2[3:])
    fm2 = yaml.safe_load(txt2[3:mm.start()+3])
    ok = (txt2.startswith("---") and "name" in fm2 and "description" in fm2
          and len(fm2["description"]) <= 1024 and len(txt2) <= 100_000)
    print(f"{name:20} desc={len(fm2['description']):4}  valid={ok}  related={len(h['related_skills'])}")

print(f"\nMigrated {len(ALL)} skills -> {DST}")

# ── Generate the bb-hunter-agents persona-catalog skill from agents/*.md ──
# Claude-Code agent defs aren't a Hermes runtime; fold them into one skill whose
# body is the persona prompts, dispatched via delegate_task.
AGENTS = pathlib.Path(__file__).resolve().parent / "agents"
personas = []
for p in sorted(AGENTS.glob("*.md")):
    if p.stem == "README":
        continue
    t = p.read_text()
    if not t.startswith("---"):
        continue
    m = re.search(r"\n---\s*\n", t[3:])
    afm = yaml.safe_load(t[3:m.start()+3])
    personas.append((afm.get("name", p.stem), afm.get("description", ""), t[m.end()+3:].strip()))

cat = DST / "bb-hunter-agents"
cat.mkdir(parents=True, exist_ok=True)
head = f"""---
name: bb-hunter-agents
description: Persona catalog of {len(personas)} specialized bug-bounty hunters (recon, validation, chain-building, per-vuln-class specialists, web3/token auditors, scope gatekeeper, devils-advocate, credential-hunter). Use to dispatch focused parallel hunters via delegate_task — e.g. "run hunter-idor, hunter-ssrf and hunter-access-control on the P1 API endpoints."
version: 1.0.0
author: BugBounty_toolkit (shuvonsec/claude-bug-bounty + local)
license: MIT
metadata:
  hermes:
    tags: [security, bug-bounty, pentest, subagents]
    related_skills: [bb-methodology, bug-bounty, web2-vuln-classes, security-arsenal, triage-validation]
---

# Bug Bounty Hunter Agent Catalog

The {len(personas)} personas below were ported from the toolkit's Claude Code `agents/`
folder. Claude Code pins each to a model and a `tools:` allowlist — Hermes has no
persisted-sub-agent runtime, so these are used as **persona prompts** fed into
`delegate_task` (Hermes' subagent dispatcher). Children inherit the parent model
unless `delegation.model` is set.

## How to dispatch
- Batch up to 3 hunters per `delegate_task` call (parallel); more = multiple calls.
- Pass the persona body as `context`, plus the concrete target/surface/endpoint.
- Hunters route confirmed findings to validator -> chain-builder -> report-writer.

## Personas

"""
body = "\n".join(f"### {n}\n\n_{d}_\n\n{b}\n" for n, d, b in personas)
(cat / "SKILL.md").write_text(head + body)
print(f"Generated bb-hunter-agents ({len(personas)} personas) -> {cat}")
print(f"\nTotal: {len(ALL) + 1} skills installed under {DST}")

