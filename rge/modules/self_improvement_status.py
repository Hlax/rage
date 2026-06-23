"""Private operator status summary for the self-improvement build spine."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.autonomous_synthesis_governor import (
    inspect_autonomous_synthesis_governor_plan_status,
    load_circuit_breaker,
    load_governor_ledger,
    utc_now_iso,
)
from rge.modules.instruction_packet_ticket_draft import (
    inspect_instruction_packet_ticket_draft_status,
)
from rge.modules.operator_loop import inspect_working_tree
from rge.modules.principal_audit_gate import repo_root
from rge.modules.release_governor import inspect_release_governor_plan_status
from rge.modules.tier2_patch_staging import inspect_tier2_patch_staging_status

SCHEMA_VERSION = "self_improvement_status_v0.1.0"
DEFAULT_STATUS_REL = Path("data/operator/self_improvement_status_latest.json")


def status_path(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_STATUS_REL


def self_improvement_spine_map() -> list[dict[str, Any]]:
    return [
        {
            "step": "research_run_report",
            "source_of_truth": "rge/modules/run_evaluator.py + run_reports",
            "required_inputs": ["research DB", "research contract", "pipeline metrics"],
            "outputs": ["run_report JSON", "quality/failure signals"],
            "blocking_gates": ["contract drift", "missing graph evidence", "unsafe export policy"],
            "blocked_action": "repair research spine or rerun fixture/mock proof",
            "llm_allowed": "mock/Ollama only for upstream structured extraction; report aggregation is deterministic Python",
            "touches_db_or_graph": True,
            "touches_public_atlas": False,
        },
        {
            "step": "evaluator",
            "source_of_truth": "research quality/evaluator modules and reports",
            "required_inputs": ["run report", "graph metrics", "failure modes"],
            "outputs": ["improvement evidence", "recommended build focus"],
            "blocking_gates": ["insufficient evidence", "drift/cadence gates"],
            "blocked_action": "run principal/operator proof or collect stronger evidence",
            "llm_allowed": "mock/local structured proposals only unless explicitly cloud-gated for synthesis",
            "touches_db_or_graph": False,
            "touches_public_atlas": False,
        },
        {
            "step": "instruction_packet",
            "source_of_truth": "rge/modules/autonomous_synthesis_governor.py",
            "required_inputs": ["grounded packet", "synthesis output", "budget/provider gates"],
            "outputs": ["governor ledger row", "GO instruction packet"],
            "blocking_gates": ["NO-GO/PARTIAL ledger rows", "open circuit breaker", "budget/provider/grounding failures"],
            "blocked_action": "inspect circuit breaker and remediate ledger reasons; reset only with explicit audited command",
            "llm_allowed": "OpenAI/OpenRouter/mock cloud may draft synthesis only; deterministic Python governs",
            "touches_db_or_graph": False,
            "touches_public_atlas": True,
        },
        {
            "step": "draft_ticket",
            "source_of_truth": "rge/modules/instruction_packet_ticket_draft.py",
            "required_inputs": ["GO instruction packet", "governor ledger", "citation refs"],
            "outputs": ["data/operator/draft_tickets/*.json", "draft status report"],
            "blocking_gates": ["stale packet", "missing refs", "forbidden actions", "private-field scan"],
            "blocked_action": "regenerate from latest GO packet or fix packet content",
            "llm_allowed": "no new LLM call; parses governed packet only",
            "touches_db_or_graph": False,
            "touches_public_atlas": False,
        },
        {
            "step": "expected_files_backfill",
            "source_of_truth": "rge/modules/instruction_packet_ticket_draft.py",
            "required_inputs": ["draft ticket", "source instruction packet when present"],
            "outputs": ["backfilled expected_files", "optional patch revalidation summary"],
            "blocking_gates": ["draft missing", "private-field scan", "patch revalidation failure"],
            "blocked_action": "repair draft/instruction packet then rerun backfill",
            "llm_allowed": "none",
            "touches_db_or_graph": False,
            "touches_public_atlas": False,
        },
        {
            "step": "patch_staging",
            "source_of_truth": "rge/modules/tier2_patch_staging.py",
            "required_inputs": ["draft ticket", "working-tree diff", "expected_files"],
            "outputs": ["patch bundle", "validation JSON", "Tier 2 Atlas preview artifact"],
            "blocking_gates": ["forbidden paths", "diff too large", "missing tests", "public-surface safety flag"],
            "blocked_action": "revise patch and re-stage; do not apply NO-GO bundles",
            "llm_allowed": "external builder may propose code; Python validates staged diff",
            "touches_db_or_graph": False,
            "touches_public_atlas": True,
        },
        {
            "step": "tier2_implementation",
            "source_of_truth": "rge/modules/tier2_local_implementation.py",
            "required_inputs": ["GO draft", "Tier 2 policy", "optional GO patch bundle"],
            "outputs": ["local feature branch", "local commit", "test/safety result sidecars"],
            "blocking_gates": ["circuit breaker", "tier policy", "dirty tree", "test failure", "safety failure"],
            "blocked_action": "fix implementation/tests or lower autonomy to manual handoff",
            "llm_allowed": "external builder/IDE only; no model writes accepted graph records",
            "touches_db_or_graph": False,
            "touches_public_atlas": False,
        },
        {
            "step": "tests_safety",
            "source_of_truth": "rge/modules/verify_runner.py + rge/modules/safety_auditor.py",
            "required_inputs": ["repo working tree", "mock LLM mode"],
            "outputs": ["verification report", "safety audit report"],
            "blocking_gates": ["golden/full pytest failure", "public/private leak", "route or model-tool violation"],
            "blocked_action": "fix failing tests/safety issues before release governor GO",
            "llm_allowed": "mock only",
            "touches_db_or_graph": False,
            "touches_public_atlas": False,
        },
        {
            "step": "release_batch",
            "source_of_truth": "rge/modules/release_batch_assembler.py",
            "required_inputs": ["draft ticket", "branch/commit", "test results", "safety results", "agent reports"],
            "outputs": ["data/operator/release_batches/*.json"],
            "blocking_gates": ["unsafe dirty tree", "missing test/safety artifacts", "missing rollback/report metadata"],
            "blocked_action": "clean tree and attach passing result artifacts",
            "llm_allowed": "none",
            "touches_db_or_graph": False,
            "touches_public_atlas": True,
        },
        {
            "step": "release_governor",
            "source_of_truth": "rge/modules/release_governor.py",
            "required_inputs": ["release batch", "ledger", "circuit breaker", "verify", "safety audit"],
            "outputs": ["release governor report", "Atlas release governor artifact"],
            "blocking_gates": ["verify failure", "NO-GO/PARTIAL ledger rows", "open circuit breaker", "unsafe batch"],
            "blocked_action": "fix real health failures first; remediate ledger/circuit state with explicit audited commands",
            "llm_allowed": "none",
            "touches_db_or_graph": False,
            "touches_public_atlas": True,
        },
        {
            "step": "atlas_preview",
            "source_of_truth": "apps/public-site/public/data/*atlas*_latest.json",
            "required_inputs": ["public-safe operator artifacts"],
            "outputs": ["/atlas-preview operator panels"],
            "blocking_gates": ["private-field scan", "static render/build failure"],
            "blocked_action": "refresh safe artifact and rebuild public site",
            "llm_allowed": "none",
            "touches_db_or_graph": False,
            "touches_public_atlas": True,
        },
    ]


def build_self_improvement_status(*, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    tree = inspect_working_tree(project_root)
    ledger = load_governor_ledger(root=project_root)
    flagged = [
        {
            "review_id": row.get("review_id"),
            "governor_verdict": row.get("governor_verdict"),
            "failure_reasons": list(row.get("failure_reasons") or [])[:5],
        }
        for row in ledger.get("reviews") or []
        if row.get("governor_verdict") in {"PARTIAL", "NO-GO"}
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": utc_now_iso(),
        "status": "NO-GO" if flagged else "PARTIAL",
        "spine_map": self_improvement_spine_map(),
        "current_state": {
            "working_tree_clean": tree.clean,
            "dirty_path_count": len(tree.dirty_paths),
            "circuit_breaker": load_circuit_breaker(root=project_root),
            "flagged_synthesis_governor_reviews": flagged,
            "instruction_packet_ticket_draft_status": inspect_instruction_packet_ticket_draft_status(
                root=project_root
            ),
            "tier2_patch_staging_status": inspect_tier2_patch_staging_status(
                root=project_root,
                working_tree=tree,
            ),
            "release_governor_status": inspect_release_governor_plan_status(
                root=project_root,
                working_tree=tree,
            ),
            "autonomous_synthesis_governor_status": inspect_autonomous_synthesis_governor_plan_status(
                root=project_root
            ),
        },
        "forbidden_actions": [
            "reset_circuit_breaker_without_confirmed_operator_command",
            "delete_or_mutate_governor_ledger_rows",
            "edit_TICKET_QUEUE",
            "push_merge_publish_or_promote",
            "weaken_release_governor_checks",
            "model_output_direct_graph_write",
        ],
    }
    violations = assert_no_private_fields({"self_improvement_status": payload})
    if violations:
        raise ValueError("self-improvement status blocked: " + "; ".join(violations[:5]))
    return payload


def write_self_improvement_status(*, root: Path | None = None) -> Path:
    project_root = root or repo_root()
    path = status_path(root=project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(build_self_improvement_status(root=project_root), indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write private self-improvement spine status.")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    project_root = args.root or repo_root()
    payload = build_self_improvement_status(root=project_root)
    path = args.out if args.out is not None else status_path(root=project_root)
    if not path.is_absolute():
        path = project_root / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "path": path.relative_to(project_root).as_posix()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
