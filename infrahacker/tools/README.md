# InfraHacker Tools & Command Reference

You hunt cloud, infrastructure, DNS, and CI/CD vulnerabilities:

| Short Command | Direct Script | Purpose | Example Usage |
|---|---|---|---|
| `bb-takeover` | `tools/takeover_scanner.sh`| Subdomain takeover verification | `bb-takeover -l recon/target.com/subdomains.txt` |
| `bb-cloud` | `tools/cloud_recon.sh` | S3Scanner & CloudFail unmasking | `bb-cloud --keyword target` |
| - | `tools/cicd_scanner.sh` | GitHub Actions workflow audit | `bash tools/cicd_scanner.sh <repo_url>` |
