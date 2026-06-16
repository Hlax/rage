"""Research Atlas export contract inventory (ticket-278).

Scans the repo for current DB tables, schema modules, report/export shapes,
public-site readers, golden coverage, and safety classifications. Emits a
deterministic JSON inventory and markdown report for operator/frontend planning.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rge.contracts.atlas_snapshot_v0 import ATLAS_SNAPSHOT_SCHEMA_VERSION
from rge.modules.card_exporter import BUILD_INFO_FIELD_ORDER, EXPORT_CARD_FIELD_ORDER
from rge.modules.run_evaluator import REPORT_SCHEMA_VERSION

INVENTORY_SCHEMA_VERSION = "research_atlas_export_inventory_v0.1.0"

_CREATE_TABLE_RE = re.compile(
    r"CREATE TABLE IF NOT EXISTS\s+(\w+)",
    re.IGNORECASE,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _relative(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def collect_db_tables(repo_root: Path) -> list[str]:
    schema_path = repo_root / "rge" / "db" / "schema.sql"
    text = schema_path.read_text(encoding="utf-8")
    tables = _CREATE_TABLE_RE.findall(text)
    migration_tables: list[str] = []
    for migration in sorted((repo_root / "rge" / "db" / "migrations").glob("*.sql")):
        migration_tables.extend(
            _CREATE_TABLE_RE.findall(migration.read_text(encoding="utf-8"))
        )
    merged = sorted(set(tables + migration_tables))
    return merged


def collect_schema_files(repo_root: Path) -> list[dict[str, str]]:
    entries = [
        ("rge/db/schema.sql", "sqlite canonical schema"),
        ("rge/models/schemas.py", "core entity schema stub / data model mirror"),
        ("rge/llm/schemas.py", "versioned pydantic candidate model outputs"),
        ("rge/contracts/atlas_snapshot_v0.py", "Research Atlas snapshot v0 contract"),
        ("rge/safety/public_export_policy.py", "public card export allowlist policy"),
    ]
    return [
        {"path": path, "role": role}
        for path, role in entries
        if (repo_root / path).is_file()
    ]


def collect_report_json_shapes() -> list[dict[str, Any]]:
    return [
        {
            "report_type": "run_report",
            "schema_version": REPORT_SCHEMA_VERSION,
            "producer": "rge/modules/run_evaluator.py",
            "key_fields": [
                "run_id",
                "topic",
                "domain_pack",
                "contract_id",
                "claims_accepted",
                "claims_rejected",
                "top_failure_modes",
                "safety_audit_status",
            ],
            "safety_class": "operator_private",
        },
        {
            "report_type": "cluster_report",
            "schema_version": "0.1.0",
            "producer": "rge/modules/cluster_reporter.py",
            "key_fields": ["cluster_id", "claim_ids", "summary", "stance_mix"],
            "safety_class": "operator_private",
        },
        {
            "report_type": "theory_candidate_report",
            "schema_version": "0.1.0",
            "producer": "rge/modules/theory_generator.py",
            "key_fields": ["theory_id", "hypothesis", "supporting_claim_ids"],
            "safety_class": "operator_private",
        },
        {
            "report_type": "operator_proof_bundle",
            "schema_version": "implicit",
            "producer": "rge/modules/operator_proof_bundle.py",
            "key_fields": [
                "pipeline_mode",
                "source_id",
                "claim_count",
                "export_path",
                "usable_output",
            ],
            "safety_class": "operator_private",
        },
        {
            "report_type": "safety_audit_report",
            "schema_version": "implicit",
            "producer": "rge/modules/safety_auditor.py",
            "key_fields": ["audit_type", "status", "blocked_reasons"],
            "safety_class": "operator_private",
        },
    ]


def collect_export_json_shapes() -> list[dict[str, Any]]:
    return [
        {
            "artifact": "public_cards.json",
            "schema_version": "0.1.0",
            "producer": "rge/modules/card_exporter.py",
            "record_fields": list(EXPORT_CARD_FIELD_ORDER),
            "safety_class": "public_safe_when_curated",
        },
        {
            "artifact": "build_info.json",
            "schema_version": "0.1.0",
            "producer": "rge/modules/card_exporter.py",
            "record_fields": list(BUILD_INFO_FIELD_ORDER),
            "safety_class": "public_safe",
        },
        {
            "artifact": "public_memos.json",
            "schema_version": "0.1.0",
            "producer": "rge/modules/card_exporter.py",
            "record_fields": ["id", "title", "summary", "updated_at"],
            "safety_class": "public_safe_when_curated",
        },
        {
            "artifact": "snapshot_manifest.json",
            "schema_version": "implicit",
            "producer": "rge/modules/card_exporter.py",
            "record_fields": ["generated_at", "bundle_files", "card_count"],
            "safety_class": "operator_private",
        },
        {
            "artifact": "atlas_snapshot.json",
            "schema_version": ATLAS_SNAPSHOT_SCHEMA_VERSION,
            "producer": "rge/contracts/atlas_snapshot_v0.py (contract only; export TBD)",
            "record_fields": [
                "schema_version",
                "generated_at",
                "snapshot_id",
                "root",
                "domains",
                "runs",
                "nodes",
                "edges",
                "clusters",
                "reports",
                "cards",
                "safety",
            ],
            "safety_class": "public_safe_when_curated",
        },
    ]


def collect_public_site_data_readers(repo_root: Path) -> list[dict[str, str]]:
    readers = [
        ("apps/public-site/lib/publicCards.ts", "PublicCard type + card/concept helpers"),
        ("apps/public-site/app/page.tsx", "imports public_cards.json, public_memos.json, build_info.json"),
        ("apps/public-site/app/about/page.tsx", "imports build_info.json"),
        ("apps/public-site/app/cards/[id]/page.tsx", "static card detail via generateStaticParams"),
        ("apps/public-site/app/concepts/[id]/page.tsx", "concept pages from exported card concepts"),
    ]
    return [
        {"path": path, "role": role}
        for path, role in readers
        if (repo_root / path).is_file()
    ]


def collect_golden_test_coverage(repo_root: Path) -> list[dict[str, str]]:
    golden_dir = repo_root / "tests" / "golden"
    files = sorted(golden_dir.glob("test_*.py"))
    return [
        {
            "path": _relative(path, repo_root),
            "module": path.stem,
        }
        for path in files
    ]


def collect_safety_classifications() -> list[dict[str, str]]:
    return [
        {
            "surface": "sqlite research graph (claims, sources, relationships)",
            "classification": "operator_private",
            "notes": "Never exported raw; public export uses curated cards only",
        },
        {
            "surface": "public_cards.json / public_memos.json / build_info.json",
            "classification": "public_safe_when_curated",
            "notes": "Fail-closed export policy in public_export_policy.py",
        },
        {
            "surface": "run_report / cluster_report / theory_candidate",
            "classification": "operator_private",
            "notes": "Reporting spec envelopes; not on public site today",
        },
        {
            "surface": "improvement_tickets",
            "classification": "agent_lab_private",
            "notes": "Structured builder queue; must not clutter public atlas",
        },
        {
            "surface": "model invocation metadata / live_probe scratch",
            "classification": "operator_private",
            "notes": "No durable review_batch object yet",
        },
        {
            "surface": "atlas_snapshot_v0.1.0",
            "classification": "public_safe_when_curated",
            "notes": "Contract defined ticket-278; population/export deferred",
        },
        {
            "surface": "media / images",
            "classification": "deferred",
            "notes": "Text-first graph; optional media_assets table reserved for later",
        },
    ]


def collect_research_atlas_gaps() -> list[dict[str, str]]:
    return [
        {
            "gap": "no_explicit_public_atlas_snapshot_export",
            "severity": "high",
            "notes": "Cards alone cannot power graph/atlas UI; atlas_snapshot_v0 contract is shape-only",
        },
        {
            "gap": "no_review_batch_or_synthesis_batch_object",
            "severity": "high",
            "notes": "Larger-model passes need durable review_batch, not scattered invocation metadata",
        },
        {
            "gap": "domain_links_not_normalized_for_ui",
            "severity": "medium",
            "notes": "Domain pack supports overlap/parent/child; atlas needs stable domain_links[]",
        },
        {
            "gap": "research_question_lineage_not_explicit",
            "severity": "medium",
            "notes": "Need parent_question_id, spawned_from_claim_ids, spawned_from_report_id, spawn_reason",
        },
        {
            "gap": "agent_lab_not_separated_from_research_graph",
            "severity": "medium",
            "notes": "Improvement tickets should export to private Agent Lab layer by default",
        },
        {
            "gap": "nodes_edges_clusters_empty_in_v0_contract",
            "severity": "expected",
            "notes": "v0 reserves arrays; graph projection from DB not wired yet",
        },
        {
            "gap": "images_not_in_core_graph",
            "severity": "intentional",
            "notes": "Text-first; reserve optional asset metadata only; no base64 in graph JSON",
        },
    ]


def build_contract_inventory(repo_root: Path | None = None) -> dict[str, Any]:
    """Build deterministic JSON inventory of current export/frontend contracts."""
    root = repo_root or _repo_root()
    return {
        "inventory_schema_version": INVENTORY_SCHEMA_VERSION,
        "atlas_snapshot_contract_version": ATLAS_SNAPSHOT_SCHEMA_VERSION,
        "db_tables": collect_db_tables(root),
        "schema_files": collect_schema_files(root),
        "report_json_shapes": collect_report_json_shapes(),
        "export_json_shapes": collect_export_json_shapes(),
        "public_site_data_readers": collect_public_site_data_readers(root),
        "golden_test_coverage": collect_golden_test_coverage(root),
        "safety_classifications": collect_safety_classifications(),
        "research_atlas_gaps": collect_research_atlas_gaps(),
    }


def render_inventory_markdown(inventory: dict[str, Any]) -> str:
    """Render inventory JSON as markdown for docs/agent_reports."""
    lines = [
        "# Research Atlas Export Contract Inventory v0",
        "",
        f"- Inventory schema: `{inventory['inventory_schema_version']}`",
        f"- Atlas snapshot contract: `{inventory['atlas_snapshot_contract_version']}`",
        "",
        "## Current DB tables",
        "",
    ]
    for table in inventory["db_tables"]:
        lines.append(f"- `{table}`")

    lines.extend(["", "## Schema / contract files", ""])
    for entry in inventory["schema_files"]:
        lines.append(f"- `{entry['path']}` — {entry['role']}")

    lines.extend(["", "## Report JSON shapes", ""])
    for shape in inventory["report_json_shapes"]:
        fields = ", ".join(f"`{f}`" for f in shape["key_fields"])
        lines.append(
            f"- **{shape['report_type']}** ({shape['schema_version']}) "
            f"[{shape['safety_class']}] — {shape['producer']}: {fields}"
        )

    lines.extend(["", "## Export JSON shapes", ""])
    for shape in inventory["export_json_shapes"]:
        fields = ", ".join(f"`{f}`" for f in shape["record_fields"])
        lines.append(
            f"- **{shape['artifact']}** ({shape['schema_version']}) "
            f"[{shape['safety_class']}] — {shape['producer']}: {fields}"
        )

    lines.extend(["", "## Public-site data readers", ""])
    for reader in inventory["public_site_data_readers"]:
        lines.append(f"- `{reader['path']}` — {reader['role']}")

    lines.extend(["", "## Golden test coverage", ""])
    for test in inventory["golden_test_coverage"]:
        lines.append(f"- `{test['path']}`")

    lines.extend(["", "## Private / public safety classification", ""])
    for item in inventory["safety_classifications"]:
        lines.append(
            f"- **{item['surface']}** — `{item['classification']}`: {item['notes']}"
        )

    lines.extend(["", "## Gaps vs Research Atlas + Agent Lab needs", ""])
    for gap in inventory["research_atlas_gaps"]:
        lines.append(
            f"- **[{gap['severity']}]** {gap['gap']}: {gap['notes']}"
        )

    lines.append("")
    return "\n".join(lines)


def write_inventory_report(
    output_path: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    inventory = build_contract_inventory(repo_root)
    markdown = render_inventory_markdown(inventory)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    json_path = output_path.with_suffix(".json")
    json_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    return inventory


if __name__ == "__main__":
    root = _repo_root()
    target = root / "docs" / "contracts" / "research_atlas_export_contract_inventory_v0.md"
    inventory = write_inventory_report(target, repo_root=root)
    print(json.dumps({"status": "written", "path": str(target), "tables": len(inventory["db_tables"])}, indent=2))
