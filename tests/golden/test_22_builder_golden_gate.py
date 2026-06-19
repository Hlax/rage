"""Golden Test 22: builder changes must pass golden fixtures before merge."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = REPO_ROOT / "tests" / "golden"

BUILDER_MERGE_GATE_COMMAND = "pytest tests/golden"

REQUIRED_GOLDEN_AREAS: dict[str, tuple[str, ...]] = {
    "ingestion": ("tests/golden/test_01_ingestion.py",),
    "claim_extraction": (
        "tests/golden/test_02_claim_extraction.py",
        "tests/golden/test_02_claim_extraction_overlap_domain.py",
    ),
    "claim_validation": (
        "tests/golden/test_02_claim_extraction.py",
        "tests/golden/test_02_claim_extraction_overlap_domain.py",
    ),
    "concept_linking": ("tests/golden/test_05_concept_linking.py",),
    "relationship_building": ("tests/golden/test_06_relationship_builder.py",),
    "contradiction_detection": ("tests/golden/test_07_contradiction_detection.py",),
    "scoring_history": ("tests/golden/test_08_score_reconciliation.py",),
    "research_queue": ("tests/golden/test_09_research_queue.py",),
    "public_export": ("tests/golden/test_11_public_card_export.py",),
    "public_site_static_render": ("tests/golden/test_12_public_site_static_render.py",),
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

# Phase 1 golden tests intentionally outside REQUIRED_GOLDEN_AREAS. The full
# merge gate still runs them via `pytest tests/golden`; they are not separate
# merge-blocker capability areas for builder branches.
INTENTIONALLY_OPTIONAL_GOLDEN_TESTS: dict[str, str] = {
    "tests/golden/test_00_scaffold.py": (
        "Phase 0 scaffold/CLI/schema smoke; covered by the full golden suite."
    ),
    "tests/golden/test_00_model_runtime.py": (
        "Model adapter boundary smoke; mock mode enforced across the suite."
    ),
    "tests/golden/test_00_public_site_static.py": (
        "Lightweight static JSON policy checks; GT12/GT25 cover public-site gates."
    ),
    "tests/golden/test_10_research_contract_drift.py": (
        "Contract drift gating; exercised inside fixture-mode full MVP run."
    ),
    "tests/golden/test_15_theory_generator.py": (
        "Theory candidate generation; orchestrated by GT26 full MVP run."
    ),
    "tests/golden/test_16_question_generation.py": (
        "Follow-up question generation; orchestrated by GT26 full MVP run."
    ),
    "tests/golden/test_17_ontology_pressure.py": (
        "Ontology pressure threshold report; Phase 1 intelligence extension, not core merge gate."
    ),
    "tests/golden/test_18_domain_proposal.py": (
        "Domain proposal threshold report; Phase 1 intelligence extension, not core merge gate."
    ),
    "tests/golden/test_19_run_report.py": (
        "Run report aggregation; orchestrated by GT26 and improvement ticket spine."
    ),
    "tests/golden/test_27_source_resolver.py": (
        "MVP source resolver foundation; mock fixture-mode resolver proofs."
    ),
    "tests/golden/test_28_mvp_research_loop.py": (
        "MVP abstract evidence, field map, and failure recommender fixture chain."
    ),
    "tests/golden/test_29_mvp_research_demo.py": (
        "MVP selective full-text, document parser, and research-run demo loop."
    ),
    "tests/golden/test_30_research_spine_db.py": (
        "Research-run DB ingest and full-text claim persistence (fixture mode)."
    ),
}

META_GOLDEN_TEST_FILES = frozenset({"tests/golden/test_22_builder_golden_gate.py"})


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
        "contradiction_detection",
        "scoring_history",
        "research_queue",
        "public_export",
        "public_site_static_render",
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


def test_phase1_optional_golden_tests_are_documented() -> None:
    golden_files = {
        f"tests/golden/{path.name}" for path in GOLDEN_DIR.glob("test_*.py")
    }
    required_files = {
        relative_path
        for paths in REQUIRED_GOLDEN_AREAS.values()
        for relative_path in paths
    }
    accounted = (
        required_files
        | META_GOLDEN_TEST_FILES
        | set(INTENTIONALLY_OPTIONAL_GOLDEN_TESTS)
    )
    unaccounted = sorted(golden_files - accounted)
    assert unaccounted == [], (
        "golden tests missing from Phase 1 merge gate inventory: "
        + ", ".join(unaccounted)
    )
    for relative_path, reason in INTENTIONALLY_OPTIONAL_GOLDEN_TESTS.items():
        assert reason.strip(), f"missing omission reason for {relative_path}"
        assert (REPO_ROOT / relative_path).is_file()
