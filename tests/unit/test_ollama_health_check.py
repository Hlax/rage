"""Unit tests for OllamaModelClient.health_check hints."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from rge.llm.ollama_client import OllamaModelClient


def test_health_check_reports_available_models_and_configured_model() -> None:
    client = OllamaModelClient(base_url="http://127.0.0.1:11434", model="qwen2.5:7b")
    tags_payload = json.dumps(
        {"models": [{"name": "qwen2.5:7b"}, {"name": "mistral:latest"}]}
    ).encode("utf-8")

    mock_response = MagicMock()
    mock_response.read.return_value = tags_payload
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        report = client.health_check()

    assert report["configured_model"] == "qwen2.5:7b"
    assert report["model_available"] is True
    assert report["available_models"] == ["qwen2.5:7b", "mistral:latest"]
    assert report["action_hint"] is None


def test_health_check_action_hint_when_model_missing() -> None:
    client = OllamaModelClient(base_url="http://127.0.0.1:11434", model="qwen2.5:7b")
    tags_payload = json.dumps(
        {"models": [{"name": "qwen2.5-coder:7b"}]}
    ).encode("utf-8")

    mock_response = MagicMock()
    mock_response.read.return_value = tags_payload
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        report = client.health_check()

    assert report["model_available"] is False
    assert report["action_hint"] is not None
    assert "ollama pull qwen2.5:7b" in report["action_hint"]
    assert "qwen2.5-coder:7b" in report["action_hint"]


def test_health_check_action_hint_when_unreachable() -> None:
    client = OllamaModelClient(base_url="http://127.0.0.1:11434", model="qwen2.5:7b")

    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        report = client.health_check()

    assert report["reachable"] is False
    assert report["action_hint"] is not None
    assert "not reachable" in report["action_hint"]
