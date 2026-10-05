# VulnResearch Tools & Command Reference

You research complex zero-days, smuggling, and concurrency flaws:

| Short Command | Direct Script | Purpose | Example Usage |
|---|---|---|---|
| `bb-race` | `tools/h1_race.py` | Synchronized concurrency race tester | `bb-race --token-a "<tok>" --test coupon_redeem` |
| - | `tools/zero_day_fuzzer.py` | Differential & edge-case fuzzer | `python3 tools/zero_day_fuzzer.py target.com` |
| - | `tools/waf_encoder.py` | Advanced payload encoding | `python3 tools/waf_encoder.py "<payload>"` |
| - | `tools/waf_response_analyzer.py`| Response differential analysis | `python3 tools/waf_response_analyzer.py <resp>` |
