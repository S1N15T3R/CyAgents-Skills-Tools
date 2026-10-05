# WebAttack Tools & Command Reference

You probe and exploit web application vulnerabilities:

| Short Command | Direct Script | Purpose | Example Usage |
|---|---|---|---|
| `bb-vulnscan` | `tools/vuln_scanner.sh` | XSS, SQLi, SSTI, open redirect, CORS | `bb-vulnscan recon/target.com/` |
| `bb-403` | `tools/bypass_403.sh` | 403/401 bypass test matrix | `bb-403 -u https://target.com/admin` |
| - | `tools/waf_encoder.py` | WAF evasion payload mutator | `python3 tools/waf_encoder.py "<payload>"` |
| - | `tools/waf_response_analyzer.py`| WAF block vs application error | `python3 tools/waf_response_analyzer.py <resp_file>` |
| - | `tools/multipart_mutator.py`| File upload extension/magic mutator| `python3 tools/multipart_mutator.py --file test.php` |
| - | `tools/spray_orchestrator.sh`| Credential spray engine | `bash tools/spray_orchestrator.sh --target target.com` |
| - | `tools/auth_session.py` | Multi-account session management | `python3 tools/auth_session.py --help` |
