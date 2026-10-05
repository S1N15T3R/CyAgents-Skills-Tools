---
name: web-testing-browser
description: >-
  Drive a real Chrome browser from the CLI for authenticated, interactive web security testing —
  navigate, screenshot, enumerate interactive elements/forms, capture full network traffic, run in-page
  JavaScript, and fill/click, all reusing one persistent logged-in session. Use when testing needs a
  browser (DOM XSS confirmation, authenticated IDOR/access-control walking, capturing API traffic and
  tokens, verifying client-side PoCs) or the user says "open the browser", "log in and test", "capture
  requests", "check the DOM". Adapted from the Apache-2.0 chrome-devtools skill.
---

# Web testing browser

For authorized security testing only. Drive the browser only against in-scope targets you're permitted to
test. These scripts wrap Puppeteer; each does one thing and prints JSON so you can chain them and parse
with `jq`.

## Setup (once)

```bash
SKILL=~/.hermes/skills/security/web-testing-browser  # or toolkit/skills/web-testing-browser
cd "$SKILL/scripts"
bash install-deps.sh    # system libs (Linux/WSL); no-op notice elsewhere
npm install             # puppeteer, yargs
node navigate.js --url https://example.com --help
```

If `npm`/Chrome libs aren't available, the skill is inert until installed — scripts print a clear JSON
error rather than crashing.

## The persistent authenticated session (most useful for pentesting)

Log in by hand once, then every script reuses that session (cookies, localStorage) via a saved
`.browser-endpoint` file:

```bash
# 1. Launch a visible browser and log in manually to the target
node launch-persistent.js --headless false --url https://target/login
# ... complete login / MFA in the window ...

# 2. Now every command runs as the logged-in user
node snapshot.js  --url https://target/dashboard          # enumerate forms/links/inputs
node network.js   --url https://target/api/me --out me.json  # capture request/response + tokens
node evaluate.js  --url https://target/app --expr "document.cookie"

# 3. Done
node close-persistent.js
```

See `references/persistent-session.md` for details and two-account testing (run two persistent profiles to
diff responses for IDOR/access-control).

## Scripts (in `scripts/`)

| Script | Purpose |
|---|---|
| `navigate.js` | Load a URL; returns final URL, status, title. |
| `screenshot.js` | Capture PNG (full page or element); returns path. |
| `snapshot.js` | Enumerate interactive elements (links, buttons, inputs, forms) with selectors/XPath — attack-surface & form discovery. |
| `network.js` | Record all requests/responses (method, headers, postData, status) — capture APIs, tokens, hidden endpoints. Filter with `--types xhr,fetch`. |
| `evaluate.js` | Run arbitrary JS in the page and return the result — DOM XSS sink checks, read `document.cookie`/storage, probe client state. |
| `fill.js` | Fill a form field by selector. |
| `click.js` | Click an element by selector. |
| `launch-persistent.js` / `close-persistent.js` | Start/stop the shared logged-in browser. |

Shared flags: `--headless false`, `--close false` (reuse browser), `--timeout <ms>`, `--wait-until
networkidle2`. All output is JSON on stdout; errors as `{ "success": false, "error": "..." }` on stderr.

## Security-testing patterns
- **DOM XSS:** `snapshot.js` to find sinks/params → `evaluate.js` to inject a benign marker and confirm
  the sink fires → `network.js` to see resulting requests.
- **Authenticated IDOR / access control:** two persistent profiles (user A, user B); replay A's requests
  from B's session and diff (`references/persistent-session.md`).
- **Token / endpoint capture:** `network.js` on an authed flow reveals API endpoints, auth headers, and
  tokens the UI hides.
- **Client-side PoC proof:** confirm a payload executes in a real browser for the report (screenshot +
  network as evidence).

## Stealth / bot-protected targets
These scripts use vanilla Puppeteer (no evasion). For Cloudflare/Queue-It-protected targets, use the
stealth browser MCP instead (`toolkit/mcp/`). You can also add a stealth plugin in
`scripts/lib/browser.js` (see the comment there).

## Custom scripts
Build new one-off scripts on `lib/browser.js` (`getBrowser`, `getPage`, `parseArgs`, `outputJSON`,
`outputError`, `closeBrowser`). Keep one action per script, JSON out.
