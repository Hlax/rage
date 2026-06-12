"""Golden Test 00: the Phase 0 scaffold exists and is coherent.

Verifies imports, CLI help, schema placeholder table names, domain pack
files, and fixture files. Runs in mock LLM mode and never requires Ollama,
a populated database, or the network.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_SCHEMA_TABLES = [
    "sources",
    "chunks",
    "research_contracts",
    "claims",
    "claim_quotes",
    "concepts",
    "claim_concepts",
    "relationships",
    "relationship_evidence",
    "score_events",
    "candidate_sources",
    "research_queue",
    "research_runs",
    "node_reports",
    "run_reports",
    "cluster_reports",
    "theory_candidates",
    "public_cards",
    "improvement_tickets",
    "safety_audits",
]

EXPECTED_DOMAIN_PACK_FILES = [
    "domain.yaml",
    "ontology.yaml",
    "aliases.yaml",
    "source_preferences.yaml",
    "evidence_types.yaml",
    "scoring.yaml",
    "claim_schema.yaml",
    "card_templates.yaml",
    "search_templates.yaml",
    "safety_notes.yaml",
]

EXPECTED_FIXTURE_FILES = [
    "fixtures/sources/creativity_ai_diversity_short.txt",
    "fixtures/sources/creativity_ai_diversity_contradiction.txt",
    "fixtures/sources/prompt_injection_source.txt",
    "fixtures/llm_outputs/claim_extraction_valid_and_missing_quote.json",
    "fixtures/llm_outputs/claim_extraction_overgeneralized.json",
    "fixtures/candidate_sources/source_ranking_fixture.json",
]


def test_rge_package_imports() -> None:
    import rge

    assert rge.__version__


def test_subpackages_import() -> None:
    import rge.cli
    import rge.config
    import rge.db.connection
    import rge.llm
    import rge.models.schemas
    import rge.modules.claim_extractor
    import rge.modules.card_exporter
    import rge.modules.safety_auditor
    import rge.safety.public_export_policy  # noqa: F401


def test_cli_top_level_help() -> None:
    from rge.cli import build_parser

    parser = build_parser()
    help_text = parser.format_help()
    assert "research" in help_text
    for command in (
        "run",
        "ingest",
        "extract-claims",
        "link-concepts",
        "build-relationships",
        "reconcile-scores",
        "detect-contradictions",
        "queue-sources",
        "validate-contract",
        "generate-cluster-report",
        "generate-theory-candidates",
        "export-public",
        "verify",
    ):
        assert command in help_text


@pytest.mark.parametrize("command", ["run", "export-public", "verify"])
def test_cli_subcommand_help_exits_cleanly(command: str) -> None:
    from rge.cli import main

    with pytest.raises(SystemExit) as excinfo:
        main([command, "--help"])
    assert excinfo.value.code == 0


def test_cli_placeholders_do_not_pretend_to_work() -> None:
    from rge.cli import main

    exit_code = main(
        ["run", "--topic", "test", "--domain", "creativity", "--fixture-mode"]
    )
    assert exit_code != 0


def test_schema_file_contains_expected_tables() -> None:
    schema_path = REPO_ROOT / "rge" / "db" / "schema.sql"
    assert schema_path.is_file()
    schema_sql = schema_path.read_text(encoding="utf-8")
    for table in EXPECTED_SCHEMA_TABLES:
        assert (
            f"CREATE TABLE IF NOT EXISTS {table}" in schema_sql
        ), f"schema.sql missing table: {table}"


def test_creativity_domain_pack_files_exist() -> None:
    pack_dir = REPO_ROOT / "domain_packs" / "creativity"
    for filename in EXPECTED_DOMAIN_PACK_FILES:
        assert (pack_dir / filename).is_file(), f"missing domain pack file: {filename}"


def test_fixture_files_exist() -> None:
    for relative in EXPECTED_FIXTURE_FILES:
        assert (REPO_ROOT / relative).is_file(), f"missing fixture: {relative}"


def test_env_example_documents_runtime_settings() -> None:
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    for key in (
        "OLLAMA_BASE_URL",
        "RGE_LOCAL_LLM",
        "RGE_LLM_MODE",
        "RGE_TEST_LLM_MODE",
        "RGE_LLM_TIMEOUT_SECONDS",
        "RGE_LLM_TEMPERATURE",
        "RGE_LLM_SCHEMA_VERSION",
        "RGE_EMBEDDING_MODE",
        "RGE_EMBEDDING_MODEL",
    ):
        assert key in env_example, f".env.example missing key: {key}"
