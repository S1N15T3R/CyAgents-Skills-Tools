# MobileHunter Tools & Command Reference

You reverse engineer and analyze mobile binaries:

| Short Command | Direct Script | Purpose | Example Usage |
|---|---|---|---|
| - | `tools/token_scanner.py` | Hardcoded token & secret validator | `python3 tools/token_scanner.py <decompiled_dir>` |
| `apkleaks` | System tool | Sensitive data scanning in APKs | `apkleaks -f app.apk` |
| `jadx` | System tool | Decompile Android DEX to Java | `jadx -d out/ app.apk` |
| `mobsf` | System tool | Mobile Security Framework audit | Automated / local report |
| `objection` | System tool | Runtime mobile exploration / Frida | `objection -g app explore` |
