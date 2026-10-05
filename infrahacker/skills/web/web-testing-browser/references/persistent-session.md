# Persistent authenticated session & two-account testing

Authorized testing only. This is what makes the browser scripts useful for real web app testing: log in
once, reuse the session everywhere.

## How it works
`launch-persistent.js` starts a Chrome instance and writes its WebSocket endpoint to
`../.browser-endpoint`. Every other script's `getBrowser()` sees that file and **connects** to the running
browser instead of launching a fresh one, so cookies, localStorage, and the logged-in state persist across
commands. `close-persistent.js` closes it and deletes the file.

```bash
cd ~/BugBounty_toolkit/skills/web-testing-browser/scripts     # or ~/.hermes/skills/security/web-testing-browser/scripts

node launch-persistent.js --headless false --url https://target/login
#   -> a browser window opens; complete login + MFA by hand

node snapshot.js --url https://target/account            # runs as the logged-in user
node network.js  --url https://target/api/me --out me.json   # capture authed API traffic + tokens
node evaluate.js --url https://target/app --expr "JSON.stringify(Object.keys(localStorage))"

node close-persistent.js
```

If a command reports it can't connect, the session may have been closed — relaunch. A stale
`.browser-endpoint` is handled gracefully (scripts fall back to a fresh browser).

## Two-account testing (IDOR / broken access control)
Access-control bugs need two identities. Run two isolated sessions and diff responses.

**Option A — sequential, two endpoint files:** copy the scripts dir or override the endpoint file per
account. Simplest: run account A's capture, `close-persistent.js`, then account B, and compare.

**Option B — capture then replay:** log in as **user A**, use `network.js` to capture the exact request to
one of A's resources (URL, method, headers, body). Then log in as **user B** and replay A's request with
B's session cookie (via `curl` or `evaluate.js` `fetch(...)`), keeping A's object ID. If B receives A's
data → IDOR. Prove it with both responses side by side.

```bash
# As user A: capture the target request
node network.js --url https://target/api/orders/1001 --types xhr,fetch --out A-order.json

# As user B (after logging in as B via launch-persistent.js): replay A's object id with B's session
node evaluate.js --url https://target/app \
  --expr "fetch('/api/orders/1001',{credentials:'include'}).then(r=>r.text())"
# If this returns A's order for user B, that's a broken access control finding.
```

## Evidence for the report
- `screenshot.js` for a visual proof (e.g. DOM XSS marker firing, other user's data rendered).
- `network.js --out` for the request/response JSON showing the boundary crossed.
- Redact your own tokens/PII before attaching. Use only test accounts you created.

## Stealth
These scripts don't evade bot protection. For Cloudflare/Queue-It targets, use the stealth browser MCP
(`~/BugBounty_toolkit/mcp/`), or add `puppeteer-extra-plugin-stealth` in `lib/browser.js` (see the comment
in that file).
