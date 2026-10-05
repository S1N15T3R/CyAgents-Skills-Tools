# OSINT Tools & Command Reference

You gather passive intelligence without sending direct packets to target infrastructure:

| Short Command | Direct Script | Purpose | Example Usage |
|---|---|---|---|
| `bb-secrets` | `tools/secrets_hunter.sh` | Scans for leaked keys / tokens | `bb-secrets --filesystem <dir>` or `--git-history <repo>` |
| `bb-cloud` | `tools/cloud_recon.sh` | Public S3/Azure/GCP bucket enum | `bb-cloud --keyword companyname` |
| `bb-dork` | `tools/dork_runner.py` | Automated Google/GitHub dorking | `bb-dork -d target.com` |
| `bb-employees`| `tools/osint_employees.sh` | Employee name/email harvesting | `bb-employees target.com` |
| `bb-breach` | `tools/breach_checker.py` | Leaked credential database check| `bb-breach --domain target.com` |
