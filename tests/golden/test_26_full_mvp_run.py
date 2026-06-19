"""Golden Test 26: full fixture-mode MVP run proves the system is real."""

from __future__ import annotations

import io
import json
import os
from itertools import cycle
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import (
    FIXTURE_RUN_ID,
    GOLDEN_MVP_TOPIC,
    STAGED_FIXTURE_RUN_ID,
    execute_fixture_mode_run,
    main,
)
from rge.modules.card_exporter import (
    FIXTURE_EXPORT_TIMESTAMP,
    default_ticket_output_dir,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
RANK1_HTML = (
    b"<html><body><p>Human-AI co-creativity supports diverse songwriting outputs.</p></body></html>"
)
RANK2_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)
SITE_DIR = REPO_ROOT / "apps" / "public-site"
SITE_OUT_DIR = SITE_DIR / "out"
COMMITTED_PUBLIC_DATA = SITE_DIR / "public" / "data"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "full_mvp_run.sqlite"


@pytest.fixture()
def artifact_dirs(tmp_path: Path) -> dict[str, Path]:
    export_dir = tmp_path / "export"
    report_dir = tmp_path / "reports"
    ticket_dir = tmp_path / "tickets"
    for directory in (export_dir, report_dir, ticket_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return {
        "export": export_dir,
        "reports": report_dir,
        "tickets": ticket_dir,
    }


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _run_fixture_mvp(
    temp_db: Path, artifact_dirs: dict[str, Path], *, run_id: str = FIXTURE_RUN_ID
) -> dict:
    return execute_fixture_mode_run(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=run_id,
        report_dir=artifact_dirs["reports"],
        ticket_dir=artifact_dirs["tickets"],
        export_dirs=[artifact_dirs["export"]],
    )


def test_fixture_mode_run_produces_required_graph_artifacts(
    temp_db: Path, artifact_dirs: dict[str, Path]
) -> None:
    result = _run_fixture_mvp(temp_db, artifact_dirs)

    assert result["status"] == "completed"
    assert result["mode"] == "fixture"
    assert result["topic"] == GOLDEN_MVP_TOPIC
    assert result["domain"] == "creativity"
    assert result["queue_count"] >= 3
    assert result["sources_ingested"] >= 2
    assert result["claims_accepted"] >= 1
    assert result["claims_rejected"] >= 1
    assert result["relationships_active"] >= 1
    assert result["score_events"] >= 1
    assert result["card_count"] >= 2
    assert isinstance(result["ticket_ids"], list)
    assert result["cluster_report_id"]
    assert result["theory_candidate_ids"]
    assert result["safety_audit_status"] == "pass"

    artifacts = result["artifacts"]
    for key in (
        "database",
        "run_report",
        "cluster_report",
        "public_cards_export",
        "public_memos_export",
        "improvement_tickets",
    ):
        assert Path(artifacts[key]).is_file(), f"missing artifact: {key}"

    cards = json.loads(
        Path(artifacts["public_cards_export"]).read_text(encoding="utf-8")
    )
    assert len(cards) >= 2

    run_report = json.loads(
        Path(artifacts["run_report"]).read_text(encoding="utf-8")
    )
    assert run_report["report_type"] == "run_report"
    assert run_report["claims_accepted"] >= 1
    assert run_report["claims_rejected"] >= 1
    assert run_report["top_failure_modes"]

    cluster_report = json.loads(
        Path(artifacts["cluster_report"]).read_text(encoding="utf-8")
    )
    assert cluster_report["report_type"] == "cluster_report"

    tickets = json.loads(
        Path(artifacts["improvement_tickets"]).read_text(encoding="utf-8")
    )
    assert isinstance(tickets, list)
    assert run_report["top_failure_modes"]
    missing_quote_modes = [
        mode
        for mode in run_report["top_failure_modes"]
        if mode.get("reason") == "missing_quote_span"
    ]
    assert missing_quote_modes, "fixture spine should record missing_quote_span"
    assert tickets == [], (
        "golden-covered failure modes must not spawn improvement drafts"
    )


def test_research_run_cli_matches_golden_command(
    temp_db: Path, artifact_dirs: dict[str, Path]
) -> None:
    from rge.cli import main

    exit_code = main(
        [
            "run",
            "--topic",
            GOLDEN_MVP_TOPIC,
            "--domain",
            "creativity",
            "--fixture-mode",
            "--db",
            str(temp_db),
            "--run-id",
            "run_golden_test_26_cli",
            "--output-dir",
            str(artifact_dirs["reports"]),
            "--ticket-dir",
            str(artifact_dirs["tickets"]),
            "--export-dir",
            str(artifact_dirs["export"]),
        ]
    )
    assert exit_code == 0


def test_default_research_run_uses_mock_staged_spine(
    temp_db: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import rge.modules.source_providers  # noqa: F401

    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", raising=False)

    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))
    html_cycle = cycle([RANK1_HTML, RANK2_HTML])

    def _urlopen(request, timeout=30):  # noqa: ARG001
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if "api.openalex.org" in url:
            return io.BytesIO(json.dumps(fixture_payload).encode("utf-8"))
        html = next(html_cycle)

        class _Response(io.BytesIO):
            headers = {"Content-Type": "text/html; charset=utf-8"}

        return _Response(html)

    staging_dir = tmp_path / "staged"
    report_dir = tmp_path / "reports"
    staging_dir.mkdir()
    report_dir.mkdir()

    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        _urlopen,
    ), patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        _urlopen,
    ):
        exit_code = main(
            [
                "run",
                "--topic",
                GOLDEN_MVP_TOPIC,
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
                "--staging-dir",
                str(staging_dir),
                "--output-dir",
                str(report_dir),
                "--run-id",
                STAGED_FIXTURE_RUN_ID,
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 0
    decoder = json.JSONDecoder()
    idx = 0
    stdout = captured.out
    document = None
    while idx < len(stdout):
        while idx < len(stdout) and stdout[idx].isspace():
            idx += 1
        if idx >= len(stdout):
            break
        document, end = decoder.raw_decode(stdout, idx)
        idx = end
    assert document is not None
    assert document["status"] == "completed"
    assert document["default_run_mode"] == "staged_spine"
    assert document["mode"] == "fixture_staged"


def test_public_site_build_succeeds_after_export() -> None:
    """Requires a prior ``npm run build`` (see ticket-028 test_plan)."""
    if not (SITE_OUT_DIR / "index.html").is_file():
        pytest.skip("Run `cd apps/public-site && npm run build` before this test")

    assert (SITE_OUT_DIR / "index.html").is_file()
    cards = json.loads(
        (REPO_ROOT / "apps/public-site/public/data/public_cards.json").read_text(
            encoding="utf-8"
        )
    )
    for card in cards:
        card_page = SITE_OUT_DIR / "cards" / f"{card['id']}.html"
        assert card_page.is_file(), f"missing static export for card {card['id']}"


def test_fixture_mode_default_ticket_dir_is_gitignored_runtime_path() -> None:
    assert default_ticket_output_dir(REPO_ROOT) == REPO_ROOT / "data" / "tickets"
    assert default_ticket_output_dir(REPO_ROOT).name == "tickets"
    assert default_ticket_output_dir(REPO_ROOT).parent.name == "data"


def test_fixture_mode_export_matches_committed_public_snapshots(
    temp_db: Path, artifact_dirs: dict[str, Path]
) -> None:
    _run_fixture_mvp(temp_db, artifact_dirs)

    for filename in ("public_cards.json", "public_memos.json", "build_info.json"):
        generated = (artifact_dirs["export"] / filename).read_bytes()
        committed = (COMMITTED_PUBLIC_DATA / filename).read_bytes()
        assert generated == committed, (
            f"fixture export {filename} must match committed public snapshot byte-for-byte"
        )


def test_fixture_mode_export_is_idempotent(
    temp_db: Path, artifact_dirs: dict[str, Path]
) -> None:
    export_dir = artifact_dirs["export"]
    first = _run_fixture_mvp(temp_db, artifact_dirs, run_id="run_golden_fixture_idempotent_a")
    first_bytes = {
        name: (export_dir / name).read_bytes()
        for name in ("public_cards.json", "public_memos.json", "build_info.json")
    }

    second = _run_fixture_mvp(temp_db, artifact_dirs, run_id="run_golden_fixture_idempotent_b")
    assert second["status"] == "completed"
    assert first["card_count"] == second["card_count"]

    for name, expected in first_bytes.items():
        assert (export_dir / name).read_bytes() == expected


def test_fixture_mode_export_uses_stable_timestamp(
    temp_db: Path, artifact_dirs: dict[str, Path]
) -> None:
    _run_fixture_mvp(temp_db, artifact_dirs)

    build_info = json.loads(
        (artifact_dirs["export"] / "build_info.json").read_text(encoding="utf-8")
    )
    cards = json.loads(
        (artifact_dirs["export"] / "public_cards.json").read_text(encoding="utf-8")
    )

    assert build_info["generated_at"] == FIXTURE_EXPORT_TIMESTAMP
    for card in cards:
        assert card["updated_at"] == FIXTURE_EXPORT_TIMESTAMP
        assert card["source_count"] == 3
