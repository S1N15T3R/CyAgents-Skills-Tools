# Verifier Tools & Command Reference

You independently reproduce and validate findings:

| Short Command | Direct Script | Purpose | Example Usage |
|---|---|---|---|
| `bb-validate` | `tools/validate.py` | 4-gate verification engine | `bb-validate --scanner-summary findings/summary.json` |
| `bb-scope` | `tools/scope_checker.py` | Enforce scope boundaries | `bb-scope --domain target.com --scope scope.md` |
| - | Browser scripts | Headless browser PoC replay | `node ../skills/web-testing-browser/scripts/navigate.js --url <target>` |
