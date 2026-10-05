# ApiHunter Tools & Command Reference

You audit REST, GraphQL, gRPC, and WebSocket APIs:

| Short Command | Direct Script | Purpose | Example Usage |
|---|---|---|---|
| `bb-idor` | `tools/h1_idor_scanner.py` | Dual-account cross-user IDOR scan | `bb-idor --token-a "<tokA>" --token-b "<tokB>" --report-id 123` |
| `bb-mutation-idor`| `tools/h1_mutation_idor.py`| GraphQL unauthorized mutation test | `bb-mutation-idor --token-a "<tokA>" --token-b "<tokB>" ...` |
| `bb-graphql` | `tools/graphql_audit.sh` | GraphQL introspection & auth fuzzer| `bb-graphql -u https://target.com/graphql` |
| `bb-param` | `tools/param_discovery.sh` | API parameter discovery | `bb-param -u https://target.com/api/v1/user` |
| - | `tools/h1_oauth_tester.py` | OAuth redirect_uri & state tampering | `python3 tools/h1_oauth_tester.py ...` |
| - | `tools/zendesk_idor_test.py`| Ticket attachment IDOR tester | `python3 tools/zendesk_idor_test.py ...` |
