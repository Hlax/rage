"""Unit tests for Phase 3 discover-sources CLI stub (ticket-138)."""

from __future__ import annotations

import json

import pytest

from rge.cli import main
from rge.modules.source_discovery import (
    DISCOVER_SOURCES_COMMAND,
    DISCOVER_SOURCES_PHASE,
    NOT_IMPLEMENTED_EXIT_CODE,
    build_discover_sources_not_implemented_payload,
    discover_sources_not_implemented_result,
)


def test_build_discover_sources_not_implemented_payload_shape() -> None:
    payload = build_discover_sources_not_implemented_payload()

    assert payload == {
        "status": "not_implemented",
        "command": DISCOVER_SOURCES_COMMAND,
        "phase": DISCOVER_SOURCES_PHASE,
        "detail": "Phase 3 source discovery is not implemented yet.",
    }


def test_discover_sources_not_implemented_result_exit_code() -> None:
    payload, exit_code = discover_sources_not_implemented_result()

    assert exit_code == NOT_IMPLEMENTED_EXIT_CODE
    assert payload["status"] == "not_implemented"
    assert "Phase 3" in payload["detail"]
    assert "source discovery" in payload["detail"].lower()


def test_discover_sources_cli_via_main(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["discover-sources"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == NOT_IMPLEMENTED_EXIT_CODE
    assert payload["status"] == "not_implemented"
    assert payload["command"] == DISCOVER_SOURCES_COMMAND
    assert payload["phase"] == DISCOVER_SOURCES_PHASE
    assert "source discovery" in payload["detail"].lower()
    assert "Phase 3" in payload["detail"]
