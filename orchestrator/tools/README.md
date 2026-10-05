# Orchestrator Tools & Command Reference

You coordinate the entire bug hunting pipeline. You can use these CLI tools directly:

| Short Command | Direct Script | Purpose | Example Usage |
|---|---|---|---|
| `bb-hunt` | `tools/hunt.py` | Full autonomous hunt loop | `bb-hunt --target target.com --quick` |
| `bb-scope` | `tools/scope_checker.py` | Scope compliance check | `bb-scope --domain sub.target.com --scope scope.md` |
| `bb-scope-agg` | `tools/scope_aggregator.sh` | Aggregate target scopes | `bash tools/scope_aggregator.sh <program>` |
| `bb-learn` | `tools/learn.py` | Fetch CVE/advisories for stack | `bb-learn --tech "nextjs,graphql"` |
| `bb-intel` | `tools/intel_engine.py` | On-demand target intel | `bb-intel --target target.com --tech "springboot"` |
| `bb-dashboard`| `tools/dashboard.py` | Progress & finding monitor | `python3 tools/dashboard.py` |
| `bb-arsenal` | `tools/external_arsenal.sh` | Check installed security tools | `bb-arsenal` |
