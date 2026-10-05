# Recon Tools & Command Reference

You actively map live responsive attack surfaces:

| Short Command | Direct Script | Purpose | Example Usage |
|---|---|---|---|
| `bb-recon` | `tools/recon_engine.sh` | Full subdomain, port, HTTP, crawl | `bb-recon target.com` (or `--quick`) |
| `bb-param` | `tools/param_discovery.sh` | Hidden HTTP parameter mining | `bb-param -u https://target.com/page` |
| `bb-cve` | `tools/cve_scan.sh` | Focused Nuclei CVE sweep | `bb-cve target.com` |
| `bb-arsenal` | `tools/external_arsenal.sh` | Tool availability check | `bb-arsenal` |
| - | `tools/wordlist_engine.sh` | Contextual wordlist generator | `bash tools/wordlist_engine.sh target.com` |
| - | `tools/banner.py` | Banner grabbing and TLS inspect | `python3 tools/banner.py target.com` |
