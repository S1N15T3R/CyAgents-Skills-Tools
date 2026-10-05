# MCP

MCP (Model Context Protocol) server integrations.

| Integration | Purpose |
|:---|:---|
| `burp-mcp-client/` | Burp Suite proxy integration — pipe Claude requests through Burp for interception |
| `caido-mcp-client/` | Caido proxy integration — alternative to Burp for request interception |
| `hackerone-mcp/` | HackerOne public API — Hacktivity, program stats, scope and policy lookup |
| `stealth-browser-mcp.json` | **(local add)** stealth browser MCP (nodriver + CDP, ~97 tools) for bot-protected targets (Cloudflare, Queue-It). Pairs with the `web-testing-browser` skill. |

Configure MCP servers in `~/.claude/mcp_servers.json` after install.

## Stealth browser MCP setup

Clone and install [vibheksoni/stealth-browser-mcp](https://github.com/vibheksoni/stealth-browser-mcp), then
register it (adjust absolute paths to your clone + venv):

```bash
git clone https://github.com/vibheksoni/stealth-browser-mcp.git toolkit/mcp/stealth-browser-mcp
cd toolkit/mcp/stealth-browser-mcp
python -m venv venv && . venv/bin/activate && pip install -r requirements.txt

claude mcp add-json stealth-browser '{
  "type": "stdio",
  "command": "'"$HOME"'/CyAgents-Skills-Tools/toolkit/mcp/stealth-browser-mcp/venv/bin/python",
  "args": ["'"$HOME"'/CyAgents-Skills-Tools/toolkit/mcp/stealth-browser-mcp/src/server.py"]
}'
```

Or copy `stealth-browser-mcp.json` into your MCP config, replacing `REPLACE_WITH` with the clone path.
Use the lightweight `web-testing-browser` skill when stealth isn't needed; reach for this MCP only against
targets that block vanilla automation. Authorized testing only.
