"""Operator proof bundle for mock arbitrary-source pipeline (ticket-267)."""

from __future__ import annotations

import io
import json
from itertools import cycle
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import (
    STAGED_FIXTURE_QUESTION_ID,
    STAGED_FIXTURE_RUN_ID,
    STAGED_RANK1_CANDIDATE_ID,
    main,
)
from rge.modules.operator_proof_bundle import (
    COMMAND,
    PIPELINE_MODE,
    REQUIRED_BUNDLE_FIELDS,
    build_error_bundle,
    collect_source_metrics,
    execute_arbitrary_source_proof_bundle,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
RANK1_HTML = (
    b"<html><body><p>Human-AI co-creativity supports diverse songwriting outputs.</p></body></html>"
)
RANK2_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)
PROOF_TOPIC = "Arbitrary-source operator proof bundle (mock)"

_STABLE_BUNDLE_COUNT_KEYS = (
    "status",
    "usable_output",
    "source_id",
    "claim_count",
    "concept_link_count",
    "relationship_count",
    "qualification_count",
    "card_count",
    "rank1_candidate_id",
)


def _stable_bundle_snapshot(bundle: dict) -> dict:
    return {
        "counts": {key: bundle[key] for key in _STABLE_BUNDLE_COUNT_KEYS},
        "reconcile": dict(bundle["reconcile"]),
    }


@pytest.fixture(autouse=True)
def mock_llm_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def mock_network_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "operator_proof_bundle.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    return directory


@pytest.fixture()
def report_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "reports"
    directory.mkdir()
    return directory


@pytest.fixture()
def export_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "export"
    directory.mkdir()
    return directory


def _staged_network_urlopen(openalex_payload: dict, html_sequence: list[bytes]):
    html_cycle = cycle(html_sequence)

    def _urlopen(request, timeout=30):  # noqa: ARG001
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if "api.openalex.org" in url:
            return io.BytesIO(json.dumps(openalex_payload).encode("utf-8"))

        html = next(html_cycle)

        class _Response(io.BytesIO):
            headers = {"Content-Type": "text/html; charset=utf-8"}

        return _Response(html)

    return _urlopen


@pytest.fixture()
def patched_staged_network():
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())
    urlopen = _staged_network_urlopen(fixture_payload, [RANK1_HTML, RANK2_HTML])
    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        urlopen,
    ), patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        urlopen,
    ):
        yield


def _run_proof_bundle(
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    export_dir: Path,
    bundle_out: Path | None = None,
) -> dict:
    return execute_arbitrary_source_proof_bundle(
        topic=PROOF_TOPIC,
        domain="creativity",
        db_path=temp_db,
        report_dir=report_dir,
        staging_dir=staging_dir,
        export_dir=export_dir,
        bundle_out=bundle_out,
        run_id=STAGED_FIXTURE_RUN_ID,
        question_id=STAGED_FIXTURE_QUESTION_ID,
    )


def test_proof_bundle_happy_path_fixture_staged(
    mock_network_env: None,
    patched_staged_network: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    export_dir: Path,
) -> None:
    bundle_out = temp_db.parent / "operator_proof_bundle.json"
    bundle = _run_proof_bundle(
        temp_db, staging_dir, report_dir, export_dir, bundle_out=bundle_out
    )

    assert bundle["status"] == "completed"
    assert bundle["command"] == COMMAND
    assert bundle["pipeline_mode"] == PIPELINE_MODE
    assert bundle["usable_output"] is True
    assert bundle["claim_count"] == 2
    assert bundle["concept_link_count"] == 3
    assert bundle["relationship_count"] == 2
    assert bundle["qualification_count"] == 1
    assert bundle["reconcile"]["score_events_created"] == 1
    assert bundle["reconcile"]["status"] == "completed"
    assert bundle["rank1_candidate_id"] == STAGED_RANK1_CANDIDATE_ID
    assert bundle["card_count"] >= 2
    assert Path(bundle["report_path"]).is_file()
    assert Path(bundle["export_path"]).is_file()
    assert bundle_out.is_file()
    assert json.loads(bundle_out.read_text(encoding="utf-8"))["status"] == "completed"


def test_proof_bundle_second_run_is_idempotent_on_same_temp_paths(
    mock_network_env: None,
    patched_staged_network: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    export_dir: Path,
) -> None:
    first_bundle_out = temp_db.parent / "operator_proof_bundle_first.json"
    second_bundle_out = temp_db.parent / "operator_proof_bundle_second.json"

    first = _run_proof_bundle(
        temp_db,
        staging_dir,
        report_dir,
        export_dir,
        bundle_out=first_bundle_out,
    )
    second = _run_proof_bundle(
        temp_db,
        staging_dir,
        report_dir,
        export_dir,
        bundle_out=second_bundle_out,
    )

    assert first["status"] == "completed"
    assert second["status"] == "completed"
    assert first["usable_output"] is True
    assert second["usable_output"] is True
    assert _stable_bundle_snapshot(second) == _stable_bundle_snapshot(first)
    assert second_bundle_out.is_file()
    assert json.loads(second_bundle_out.read_text(encoding="utf-8"))["usable_output"] is True


def test_proof_bundle_schema_required_fields(
    mock_network_env: None,
    patched_staged_network: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    export_dir: Path,
) -> None:
    bundle = _run_proof_bundle(temp_db, staging_dir, report_dir, export_dir)

    for field in REQUIRED_BUNDLE_FIELDS:
        assert field in bundle, f"missing required field: {field}"

    assert isinstance(bundle["reconcile"], dict)
    assert "status" in bundle["reconcile"]
    assert "score_events_created" in bundle["reconcile"]
    assert isinstance(bundle["steps_completed"], list)
    assert "export_public_cards" in bundle["steps_completed"]
    assert "operator_proof_bundle" in bundle["steps_completed"]


def test_proof_bundle_export_path_exists_when_completed(
    mock_network_env: None,
    patched_staged_network: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    export_dir: Path,
) -> None:
    bundle = _run_proof_bundle(temp_db, staging_dir, report_dir, export_dir)
    export_path = Path(bundle["export_path"])
    assert export_path.is_file()
    cards = json.loads(export_path.read_text(encoding="utf-8"))
    assert isinstance(cards, list)
    assert len(cards) == bundle["card_count"]


def test_proof_bundle_failure_reports_failed_step(
    mock_network_env: None,
    patched_staged_network: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    export_dir: Path,
) -> None:
    bundle_out = temp_db.parent / "operator_proof_bundle_error.json"

    def _boom(*_args, **_kwargs):
        raise RuntimeError(
            "research CLI step failed (exit 1): extract-claims --source x --db y"
        )

    with patch(
        "rge.modules.operator_proof_bundle.execute_staged_fixture_mode_run",
        side_effect=_boom,
    ):
        bundle = execute_arbitrary_source_proof_bundle(
            topic=PROOF_TOPIC,
            domain="creativity",
            db_path=temp_db,
            report_dir=report_dir,
            staging_dir=staging_dir,
            export_dir=export_dir,
            bundle_out=bundle_out,
        )

    assert bundle["status"] == "error"
    assert bundle["failed_step"] == "extract-claims"
    assert bundle["usable_output"] is False
    assert "extract-claims" in bundle["detail"]
    assert bundle_out.is_file()


def _parse_last_proof_bundle_stdout(stdout: str) -> dict:
    decoder = json.JSONDecoder()
    documents: list[dict] = []
    idx = 0
    while idx < len(stdout):
        while idx < len(stdout) and stdout[idx].isspace():
            idx += 1
        if idx >= len(stdout):
            break
        document, end = decoder.raw_decode(stdout, idx)
        documents.append(document)
        idx = end
    for payload in reversed(documents):
        if payload.get("command") == COMMAND:
            return payload
    raise AssertionError(f"{COMMAND} payload not found in CLI stdout")


def test_proof_bundle_cli_entry_requires_db() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "prove-arbitrary-source-bundle",
                "--topic",
                PROOF_TOPIC,
            ]
        )
    assert excinfo.value.code == 2


def test_proof_bundle_cli_entry_happy_path(
    mock_network_env: None,
    patched_staged_network: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    export_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bundle_out = temp_db.parent / "cli_proof_bundle.json"
    exit_code = main(
        [
            "prove-arbitrary-source-bundle",
            "--topic",
            PROOF_TOPIC,
            "--domain",
            "creativity",
            "--db",
            str(temp_db),
            "--output-dir",
            str(report_dir),
            "--staging-dir",
            str(staging_dir),
            "--export-dir",
            str(export_dir),
            "--bundle-out",
            str(bundle_out),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = _parse_last_proof_bundle_stdout(captured.out)
    assert payload["status"] == "completed"
    assert payload["usable_output"] is True
    assert bundle_out.is_file()


def test_collect_source_metrics_matches_db(
    mock_network_env: None,
    patched_staged_network: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    export_dir: Path,
) -> None:
    bundle = _run_proof_bundle(temp_db, staging_dir, report_dir, export_dir)
    from rge.db.connection import connect

    conn = connect(temp_db)
    try:
        metrics = collect_source_metrics(conn, bundle["source_id"])
    finally:
        conn.close()

    assert metrics["claim_count"] == bundle["claim_count"]
    assert metrics["concept_link_count"] == bundle["concept_link_count"]
    assert metrics["relationship_count"] == bundle["relationship_count"]
    assert metrics["qualification_count"] == bundle["qualification_count"]


def test_build_error_bundle_shape() -> None:
    bundle = build_error_bundle(
        detail="step failed",
        failed_step="link-concepts",
        database_path=Path("/tmp/test.sqlite"),
    )
    assert bundle["status"] == "error"
    assert bundle["failed_step"] == "link-concepts"
    assert bundle["usable_output"] is False
