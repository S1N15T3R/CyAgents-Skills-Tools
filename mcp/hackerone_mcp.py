#!/usr/bin/env python3
"""
FastMCP Server for HackerOne & Bug Bounty Intel.
Integrates live HackerOne policy checks, CVE advisory lookup, and scope validation.
"""

import os
import sys
import json
import ssl
import urllib.request
import urllib.parse
from mcp.server.fastmcp import FastMCP

# Add BugBounty_toolkit tools to path
TOOLKIT_DIR = "/home/sinister/BugBounty_toolkit"
if TOOLKIT_DIR not in sys.path:
    sys.path.insert(0, TOOLKIT_DIR)

mcp = FastMCP("BugBountyIntel")

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

H1_GRAPHQL = "https://hackerone.com/graphql"

@mcp.tool()
def get_hackerone_policy(program: str) -> dict:
    """Fetch live HackerOne program policy, in-scope/out-of-scope assets, and safe-harbor terms.
    
    Args:
        program: HackerOne program handle (e.g., 'security', 'shopify', 'gitlab')
    """
    clean_handle = program.strip().lstrip("@").lower()
    query = """
    query GetTeamPolicy($handle: String!) {
      team(handle: $handle) {
        name
        handle
        policy
        offers_bounties
        structured_scopes {
          nodes {
            asset_identifier
            asset_type
            eligible_for_bounty
            eligible_for_submission
            instruction
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"handle": clean_handle}}).encode("utf-8")
    req = urllib.request.Request(
        H1_GRAPHQL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            team = data.get("data", {}).get("team")
            if not team:
                return {"error": f"Program '{clean_handle}' not found or private", "status": "not_found"}
            scopes = []
            for node in team.get("structured_scopes", {}).get("nodes", []):
                scopes.append({
                    "identifier": node.get("asset_identifier"),
                    "type": node.get("asset_type"),
                    "bounty_eligible": node.get("eligible_for_bounty"),
                    "submission_eligible": node.get("eligible_for_submission"),
                    "instruction": node.get("instruction")
                })
            return {
                "name": team.get("name"),
                "handle": team.get("handle"),
                "offers_bounties": team.get("offers_bounties"),
                "policy_summary": team.get("policy", "")[:2000],
                "scope_count": len(scopes),
                "in_scope_assets": [s for s in scopes if s["submission_eligible"]][:50],
                "out_of_scope_assets": [s for s in scopes if not s["submission_eligible"]][:50]
            }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_tech_cve_intel(tech: str, target: str = "") -> dict:
    """Query GitHub Advisory Database and NVD for known high/critical CVEs on detected tech stacks.
    
    Args:
        tech: Comma-separated list of technologies (e.g. 'nextjs,springboot,laravel,graphql')
        target: Optional target domain for contextualizing findings
    """
    try:
        from tools import learn
        results = {}
        for t in [x.strip() for x in tech.split(",") if x.strip()]:
            gh_advisories = learn.query_github_advisories(t, limit=5)
            results[t] = {
                "github_advisories": [
                    {
                        "cve": a.get("cve_id"),
                        "summary": a.get("summary"),
                        "severity": a.get("severity")
                    } for a in gh_advisories
                ]
            }
        return {"target": target, "tech_intel": results}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def check_asset_scope(asset: str, program_dir: str = ".") -> dict:
    """Verify if an asset (subdomain, IP, endpoint) is strictly in scope using scope.md or scope rules.
    
    Args:
        asset: The URL, domain, or IP to test
        program_dir: The directory containing scope.md
    """
    try:
        from tools import scope_checker
        scope_file = os.path.join(program_dir, "scope.md")
        if not os.path.exists(scope_file):
            return {"error": f"No scope.md found in {program_dir}. Missing scope = testing halted.", "in_scope": False}
        in_scope, reason = scope_checker.check(asset, scope_file)
        return {"asset": asset, "in_scope": in_scope, "reason": reason}
    except Exception as e:
        return {"asset": asset, "error": str(e), "in_scope": False}

if __name__ == "__main__":
    mcp.run()
