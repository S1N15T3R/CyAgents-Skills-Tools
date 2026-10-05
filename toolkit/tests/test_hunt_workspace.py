"""Regression tests for BBHUNT_WORKSPACE output routing in tools/hunt.py.

The workspace override lets a user `cd` into a per-program dir, set
$BBHUNT_WORKSPACE, and have recon/findings/reports land there instead of
inside the toolkit. Default (unset) must preserve legacy toolkit-root behavior.
"""

import importlib
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO_ROOT, "tools")


def _load_hunt(monkeypatch, workspace):
    """Import (or re-import) tools.hunt with BBHUNT_WORKSPACE set/unset."""
    if workspace is None:
        monkeypatch.delenv("BBHUNT_WORKSPACE", raising=False)
    else:
        monkeypatch.setenv("BBHUNT_WORKSPACE", workspace)
    sys.path.insert(0, TOOLS)
    sys.modules.pop("hunt", None)
    return importlib.import_module("hunt")


def test_workspace_unset_defaults_to_toolkit(monkeypatch):
    hunt = _load_hunt(monkeypatch, None)
    assert hunt.WORKSPACE == hunt.BASE_DIR
    assert hunt.RECON_DIR == os.path.join(hunt.BASE_DIR, "recon")
    assert hunt.FINDINGS_DIR == os.path.join(hunt.BASE_DIR, "findings")


def test_workspace_env_routes_output(monkeypatch, tmp_path):
    ws = str(tmp_path / "acme-corp")
    hunt = _load_hunt(monkeypatch, ws)
    assert hunt.WORKSPACE == ws
    assert hunt.RECON_DIR == os.path.join(ws, "recon")
    assert hunt.FINDINGS_DIR == os.path.join(ws, "findings")
    assert hunt.REPORTS_DIR == os.path.join(ws, "reports")


def test_wordlists_stay_in_toolkit(monkeypatch, tmp_path):
    """Wordlists ship with the toolkit — never relocate to the workspace."""
    hunt = _load_hunt(monkeypatch, str(tmp_path / "acme"))
    assert hunt.WORDLIST_DIR == os.path.join(hunt.BASE_DIR, "wordlists")


@pytest.fixture(autouse=True)
def _cleanup_hunt_module():
    yield
    sys.modules.pop("hunt", None)
    if TOOLS in sys.path:
        sys.path.remove(TOOLS)
