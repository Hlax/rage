"""Golden Test 00: model runtime adapter boundary.

Verifies the registry's fail-closed mode selection, deterministic versioned
mock output, and the no-side-effects boundary of model clients. Forces mock
mode explicitly; never requires Ollama to be installed or running.
"""

from __future__ import annotations

import pytest

from rge.config import load_config
from rge.llm.mock_client import MockModelClient
from rge.llm.ollama_client import OllamaModelClient, OllamaNotAvailableInPhase0
from rge.llm.registry import LlmModeError, get_model_client
from rge.llm.schemas import (
    SCHEMA_VERSION_0_1_0,
    SchemaVersionError,
    validate_schema_version,
)


def _config_with_mode(monkeypatch: pytest.MonkeyPatch, mode: str):
    monkeypatch.setenv("RGE_LLM_MODE", mode)
    return load_config()


def test_registry_selects_mock_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config_with_mode(monkeypatch, "mock")
    client = get_model_client(config)
    assert isinstance(client, MockModelClient)
    assert client.provider == "mock"


def test_registry_selects_ollama_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Constructing the ollama client must not perform any network I/O.
    config = _config_with_mode(monkeypatch, "ollama")
    client = get_model_client(config)
    assert isinstance(client, OllamaModelClient)
    assert client.base_url == config.ollama_base_url
    assert client.model == config.local_llm


def test_registry_fails_closed_on_unknown_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config_with_mode(monkeypatch, "definitely-not-a-mode")
    with pytest.raises(LlmModeError):
        get_model_client(config)


def test_mock_client_returns_deterministic_versioned_output() -> None:
    client = MockModelClient()
    first = client.extract_claims(
        chunk={}, contract={}, domain_pack="creativity",
        schema_version=SCHEMA_VERSION_0_1_0,
    )
    second = client.extract_claims(
        chunk={}, contract={}, domain_pack="creativity",
        schema_version=SCHEMA_VERSION_0_1_0,
    )
    assert first.task_name == "claim_extraction"
    assert first.schema_version == SCHEMA_VERSION_0_1_0
    assert first == second  # deterministic: same input -> same output
    assert len(first.items) == 2
    # The fixture intentionally contains one valid claim and one missing quote span.
    quote_spans = [item.quote_span for item in first.items]
    assert any(span for span in quote_spans)
    assert any(span is None for span in quote_spans)


def test_schema_version_mismatch_fails_closed() -> None:
    with pytest.raises(SchemaVersionError):
        validate_schema_version("9.9.9", SCHEMA_VERSION_0_1_0)
    client = MockModelClient()
    with pytest.raises(SchemaVersionError):
        client.extract_claims(
            chunk={}, contract={}, domain_pack="creativity",
            schema_version="9.9.9",
        )


def test_ollama_structured_tasks_fail_honestly_in_phase_0() -> None:
    client = OllamaModelClient(base_url="http://127.0.0.1:11434", model="qwen2.5:7b")
    with pytest.raises(OllamaNotAvailableInPhase0):
        client.extract_claims(
            chunk={}, contract={}, domain_pack="creativity",
            schema_version=SCHEMA_VERSION_0_1_0,
        )


def test_llm_package_has_no_write_side_effect_imports() -> None:
    """Model clients must not write to SQLite, shell, Git, or the DB layer."""
    import rge.llm.base as base
    import rge.llm.mock_client as mock_client
    import rge.llm.ollama_client as ollama_client
    import rge.llm.registry as registry
    import rge.llm.schemas as schemas

    forbidden = ("sqlite3", "subprocess", "shutil")
    for module in (base, mock_client, ollama_client, registry, schemas):
        source = open(module.__file__, encoding="utf-8").read()
        for name in forbidden:
            assert (
                f"import {name}" not in source
            ), f"{module.__name__} must not import {name}"
        assert (
            "rge.db" not in source and "from rge import db" not in source
        ), f"{module.__name__} must not import the DB layer"
