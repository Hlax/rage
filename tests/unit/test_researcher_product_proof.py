"""Researcher product proof tests (ticket-381)."""

from __future__ import annotations

import io
import json
from itertools import cycle
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.modules.researcher_product_proof import (
    COMMAND,
    PRODUCT_PROOF_SCHEMA_VERSION,
    collect_db_graph_counts,
    compute_product_verdict,
    inspect_atlas_preview_visibility,
    run_researcher_product_proof,
)
from rge.modules.synthesis_packet_runner import GROUNDED_PACKET_FIXTURE_REL

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
RANK1_HTML = (
    b"<html><body><p>Human-AI co-creativity supports diverse songwriting outputs.</p></body></html>"
)
RANK2_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)
PROOF_TOPIC = "Researcher product proof (mock)"


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
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "0")


@pytest.fixture()
def work_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "researcher_product_proof_work"
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
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))
    urlopen = _staged_network_urlopen(fixture_payload, [RANK1_HTML, RANK2_HTML])
    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        urlopen,
    ), patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        urlopen,
    ):
        yield


def test_compute_product_verdict_go() -> None:
    verdict = compute_product_verdict(
        proof_bundle={"status": "completed", "usable_output": True},
        synthesis={"status": "completed", "no_accepted_graph_writes": True},
        benchmark={"reports_per_hour_estimate": 3600.0, "cloud_call_made_any": False},
        safety={"status": "pass"},
        atlas_preview={"public_preview_visible": True},
    )
    assert verdict == "GO"


def test_compute_product_verdict_no_go_when_safety_fails() -> None:
    verdict = compute_product_verdict(
        proof_bundle={"status": "completed", "usable_output": True},
        synthesis={"status": "completed", "no_accepted_graph_writes": True},
        benchmark={"reports_per_hour_estimate": 3600.0},
        safety={"status": "fail"},
        atlas_preview={"public_preview_visible": True},
    )
    assert verdict == "NO-GO"


def test_inspect_atlas_preview_visibility_on_repo() -> None:
    status = inspect_atlas_preview_visibility(root=REPO_ROOT)
    assert status["public_preview_visible"] is True
    assert status["snapshot_id"]
    assert (status["cluster_count"] or 0) >= 2


def test_run_researcher_product_proof_chains_mock_pipeline(
    work_dir: Path,
    mock_network_env: None,
    patched_staged_network: None,
) -> None:
    artifact_out = work_dir / "researcher_product_proof.json"
    result = run_researcher_product_proof(
        topic=PROOF_TOPIC,
        domain="creativity",
        work_dir=work_dir,
        root=REPO_ROOT,
        benchmark_runs=2,
        write_artifact=True,
        artifact_path=artifact_out,
    )
    assert result["schema_version"] == PRODUCT_PROOF_SCHEMA_VERSION
    assert result["command"] == COMMAND
    assert result["product_verdict"] in {"GO", "PARTIAL"}
    assert result["source_count"] >= 1
    assert result["claim_count"] >= 1
    assert result["evidence_count"] >= 0
    assert result["synthesis"]["status"] == "completed"
    assert result["synthesis"]["synthesis_output_path"]
    assert result["synthesis"]["no_accepted_graph_writes"] is True
    assert result["benchmark"]["reports_per_hour_estimate"] > 0
    assert result["safety_audit"]["status"] == "pass"
    assert result["atlas_preview"]["public_preview_visible"] is True
    assert result["mock_llm_only"] is True
    assert result["live_openai_used"] is False
    assert artifact_out.is_file()
    on_disk = json.loads(artifact_out.read_text(encoding="utf-8"))
    assert on_disk["product_verdict"] in {"GO", "PARTIAL"}


def test_run_researcher_product_proof_records_graph_counts(
    work_dir: Path,
    mock_network_env: None,
    patched_staged_network: None,
) -> None:
    result = run_researcher_product_proof(
        topic=PROOF_TOPIC,
        work_dir=work_dir,
        root=REPO_ROOT,
        benchmark_runs=2,
        write_artifact=False,
    )
    from rge.db.connection import connect, get_db_path

    conn = connect(get_db_path(work_dir / "researcher_product_proof.sqlite"))
    try:
        counts = collect_db_graph_counts(
            conn,
            source_id=result["proof_bundle"]["source_id"],
        )
    finally:
        conn.close()
    assert result["source_count"] == counts["source_count"]
    assert result["claim_count"] == counts["claim_count"]
    assert result["evidence_count"] == counts["evidence_count"]


def test_run_researcher_product_proof_no_go_when_proof_bundle_fails(
    work_dir: Path,
) -> None:
    def fail_bundle(**kwargs: object) -> dict:
        return {
            "status": "error",
            "detail": "injected failure",
            "usable_output": False,
        }

    result = run_researcher_product_proof(
        work_dir=work_dir,
        root=REPO_ROOT,
        benchmark_runs=1,
        write_artifact=False,
        run_proof_bundle=fail_bundle,
    )
    assert result["product_verdict"] == "NO-GO"
    assert result["failed_step"] == "proof_bundle"


def test_run_researcher_product_proof_no_go_when_synthesis_writes_graph(
    work_dir: Path,
    mock_network_env: None,
    patched_staged_network: None,
) -> None:
    from rge.modules.operator_proof_bundle import execute_arbitrary_source_proof_bundle

    def bad_synthesis(**kwargs: object) -> dict:
        return {
            "status": "completed",
            "no_accepted_graph_writes": False,
            "output_path": "data/tmp/out.json",
        }

    result = run_researcher_product_proof(
        topic=PROOF_TOPIC,
        work_dir=work_dir,
        root=REPO_ROOT,
        benchmark_runs=1,
        write_artifact=False,
        run_proof_bundle=execute_arbitrary_source_proof_bundle,
        run_synthesis=bad_synthesis,
        run_safety=lambda *_args, **_kwargs: {"status": "pass", "audit_type": "full"},
    )
    assert result["product_verdict"] == "NO-GO"
    assert result["failed_step"] == "synthesis_packet"


def test_cli_prove_researcher_product_help_lists_command() -> None:
    from io import StringIO
    import sys

    buffer = StringIO()
    stdout = sys.stdout
    sys.stdout = buffer
    try:
        with pytest.raises(SystemExit) as exc:
            main(["prove-researcher-product", "--help"])
        assert exc.value.code == 0
    finally:
        sys.stdout = stdout
    assert "prove-researcher-product" in buffer.getvalue()


def test_cli_prove_researcher_product_requires_work_dir() -> None:
    with pytest.raises(SystemExit):
        main(["prove-researcher-product", "--work-dir"])


def test_synthesis_uses_grounded_fixture_packet(
    work_dir: Path,
    mock_network_env: None,
    patched_staged_network: None,
) -> None:
    seen_packets: list[Path] = []

    def capture_synthesis(**kwargs: object) -> dict:
        packet_path = kwargs["packet_path"]
        seen_packets.append(Path(packet_path))
        from rge.modules.synthesis_packet_runner import run_synthesis_packet

        return run_synthesis_packet(**kwargs)

    run_researcher_product_proof(
        topic=PROOF_TOPIC,
        work_dir=work_dir,
        root=REPO_ROOT,
        benchmark_runs=1,
        write_artifact=False,
        run_synthesis=capture_synthesis,
    )
    assert seen_packets
    assert seen_packets[0] == REPO_ROOT / GROUNDED_PACKET_FIXTURE_REL
