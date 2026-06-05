"""Version consistency checks (ISSUE-028, v0.2.0 release)."""

import tomllib
from pathlib import Path

import supertone_mcp

EXPECTED_VERSION = "0.2.0"
_ROOT = Path(__file__).resolve().parent.parent


def test_package_version() -> None:
    assert supertone_mcp.__version__ == EXPECTED_VERSION


def test_pyproject_version_matches() -> None:
    data = tomllib.loads((_ROOT / "pyproject.toml").read_text())
    assert data["project"]["version"] == EXPECTED_VERSION


def test_server_json_version_matches() -> None:
    import json

    server = json.loads((_ROOT / "server.json").read_text())
    assert server["version"] == EXPECTED_VERSION
    assert server["packages"][0]["version"] == EXPECTED_VERSION


def test_server_json_drops_removed_env_vars() -> None:
    import json

    server = json.loads((_ROOT / "server.json").read_text())
    env_names = {e["name"] for e in server["packages"][0]["environmentVariables"]}
    # v0.2: behavior-control env vars became per-call params
    assert "SUPERTONE_MCP_OUTPUT_MODE" not in env_names
    assert "SUPERTONE_MCP_AUTOPLAY" not in env_names
    assert "SUPERTONE_API_KEY" in env_names
