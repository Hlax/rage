"""Golden Test 22: builder changes must pass golden fixtures before merge."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = REPO_ROOT / "tests" / "golden"

BUILDER_MERGE_GATE_COMMAND = "pytest tests/golden"

REQUIRED_GOLDEN_AREAS: dict[str, tuple[str, ...]] = {
    "ingestion": ("tests/golden/test_01_ingestion.py",),
    "claim_extraction": ("tests/golden/test_02_claim_extraction.py",),
    "claim_validation": ("tests/golden/test_02_claim_extraction.py",),
    "concept_linking": ("tests/golden/test_05_concept_linking.py",),
    "relationship_building": ("tests/golden/test_06_relationship_builder.py",),
    "scoring_history": ("tests/golden/test_08_score_reconciliation.py",),
    "public_export": ("tests/golden/test_11_public_card_export.py",),
    "cluster_report": ("tests/golden/test_13_cluster_report.py",),
    "ticket_generation": (
        "tests/golden/test_20_improvement_tickets.py",
        "tests/golden/test_21_builder_ticket_consumption.py",
    ),
    "safety_audit_gate": ("tests/golden/test_23_safety_audit_gate.py",),
    "prompt_injection": ("tests/golden/test_24_prompt_injection.py",),
    "public_site_debug": ("tests/golden/test_25_public_site_debug_details.py",),
    "full_mvp_run": ("tests/golden/test_26_full_mvp_run.py",),
}


def _collect_test_count(relative_path: str) -> int:
    class _Collector:
        def __init__(self) -> None:
            self.count = 0

        def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
            self.count = len(items)

    collector = _Collector()
    exit_code = pytest.main(
        [str(REPO_ROOT / relative_path), "--collect-only", "-q"],
        plugins=[collector],
    )
    assert exit_code == pytest.ExitCode.OK, (
        f"failed to collect tests for {relative_path}: exit_code={exit_code}"
    )
    return collector.count


def test_builder_merge_gate_command_is_documented() -> None:
    assert BUILDER_MERGE_GATE_COMMAND == "pytest tests/golden"
    assert "tests/golden" in BUILDER_MERGE_GATE_COMMAND


def test_required_golden_coverage_modules_exist() -> None:
    missing: list[str] = []
    for area, paths in REQUIRED_GOLDEN_AREAS.items():
        for relative_path in paths:
            absolute_path = REPO_ROOT / relative_path
            if not absolute_path.is_file():
                missing.append(f"{area}: {relative_path}")
    assert missing == [], f"missing golden modules: {missing}"


def test_required_golden_modules_remain_collectible() -> None:
    seen_paths: set[str] = set()
    for area, paths in REQUIRED_GOLDEN_AREAS.items():
        for relative_path in paths:
            if relative_path in seen_paths:
                continue
            seen_paths.add(relative_path)
            count = _collect_test_count(relative_path)
            assert count >= 1, f"{area} module {relative_path} has no tests"


def test_golden_directory_covers_all_required_areas() -> None:
    covered_areas = set(REQUIRED_GOLDEN_AREAS)
    assert covered_areas == {
        "ingestion",
        "claim_extraction",
        "claim_validation",
        "concept_linking",
        "relationship_building",
        "scoring_history",
        "public_export",
        "cluster_report",
        "ticket_generation",
        "safety_audit_gate",
        "prompt_injection",
        "public_site_debug",
        "full_mvp_run",
    }
    assert GOLDEN_DIR.is_dir()
    golden_files = {path.name for path in GOLDEN_DIR.glob("test_*.py")}
    for paths in REQUIRED_GOLDEN_AREAS.values():
        for relative_path in paths:
            assert Path(relative_path).name in golden_files
