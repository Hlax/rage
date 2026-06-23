"""Atlas-safe synthesis human-review operator artifact (mock/fixture default; no API calls)."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.autonomous_synthesis_governor import (
    DEFAULT_ATLAS_ARTIFACT_REL,
    HUMAN_REVIEW_ARTIFACT_SCHEMA,
    SYNTHESIS_OUTPUT_GLOBS,
    _artifact_is_stale,
    build_circuit_breaker_operator_guidance,
    summarize_governor_status,
    utc_now_iso,
)
from rge.modules.autonomous_synthesis_governor import _safe_rel
from rge.modules.principal_audit_gate import repo_root
from rge.modules.synthesis_grounding import evaluate_synthesis_grounding

SCHEMA_VERSION = HUMAN_REVIEW_ARTIFACT_SCHEMA
ARTIFACT_NAME = DEFAULT_ATLAS_ARTIFACT_REL.name
PACKET_ID = "synthesis-human-review-ui"
RUN_ID = "run_synthesis_human_review_ui"
CLI_SCRIPT = "scripts/run_synthesis_human_review_ui.py"
EXPORT_DIR_REL = Path("data/exports/synthesis_human_review_ui")
GROUNDED_PACKET_FIXTURE_REL = Path("fixtures/synthesis/grounded_evidence_packet_dry_run.json")
FLAGGED_OUTPUT_FIXTURE_REL = Path("fixtures/synthesis/human_review_flagged_fixture.json")
PASSED_OUTPUT_FIXTURE_REL = Path("fixtures/synthesis/human_review_passed_fixture.json")

_FORBIDDEN_REF_PATTERNS = (
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
    re.compile(r"\.env\.local", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9]{8,}", re.IGNORECASE),
)


class SynthesisHumanReviewUIError(RuntimeError):
    """Raised when human-review artifact cannot be built safely."""


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "0").strip().casefold() in {"1", "true", "yes"}


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _safe_output_ref(path: Path | None, *, root: Path) -> str | None:
    if path is None or not path.is_file():
        return None
    rel = _safe_rel(path, root)
    if rel.startswith(".."):
        return path.name
    for pattern in _FORBIDDEN_REF_PATTERNS:
        if pattern.search(rel):
            return path.name
    return rel


def _review_id(output: dict[str, Any]) -> str:
    basis = json.dumps(
        {
            "packet_id": output.get("packet_id"),
            "provider": output.get("provider"),
            "sentences": output.get("summary_sentences") or [],
        },
        sort_keys=True,
    )
    return f"syn_review_{hashlib.sha256(basis.encode('utf-8')).hexdigest()[:12]}"


def _sign_off_status(output: dict[str, Any], *, grounding: dict[str, Any]) -> str:
    if output.get("auto_signed_off"):
        return "signed_off"
    if grounding.get("needs_human_review"):
        return "not_eligible"
    if output.get("sign_off_status"):
        return str(output.get("sign_off_status"))
    return "pending_sign_off"


def build_review_entry(
    output: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    packet: dict[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    packet_payload = packet
    if packet_payload is None:
        packet_path = project_root / GROUNDED_PACKET_FIXTURE_REL
        packet_payload = _load_json(packet_path) if packet_path.is_file() else {}
    grounding = evaluate_synthesis_grounding(output, packet=packet_payload or {})
    review_status = (
        "needs_human_review" if grounding.get("needs_human_review") else "grounding_passed"
    )
    operator_ref = None
    if source_path is not None:
        candidate = (
            Path(str(source_path))
            if Path(str(source_path)).is_absolute()
            else project_root / str(source_path)
        )
        operator_ref = _safe_output_ref(candidate, root=project_root)
    sentences = output.get("summary_sentences") or []
    return {
        "output_id": _review_id(output),
        "packet_id": output.get("packet_id"),
        "packet_sha256": str(output.get("packet_sha256") or ""),
        "review_status": review_status,
        "needs_human_review": bool(grounding.get("needs_human_review")),
        "review_mode": str(output.get("review_mode") or "manual"),
        "governor_verdict": str(output.get("governor_verdict") or "UNKNOWN"),
        "auto_signed_off": bool(output.get("auto_signed_off")),
        "automated_review_status": str(output.get("automated_review_status") or "flagged"),
        "governor_review": dict(output.get("governor_review") or {}),
        "provider": str(output.get("provider") or "mock_cloud"),
        "sentence_count": len(sentences),
        "flagged_sentence_count": len(grounding.get("flagged_sentences") or []),
        "flagged_sentences": list(grounding.get("flagged_sentences") or []),
        "operator_output_ref": operator_ref,
        "sign_off_status": _sign_off_status(output, grounding=grounding),
    }


def _review_summary(review_queue: list[dict[str, Any]]) -> dict[str, int]:
    total = len(review_queue)
    needs = sum(1 for row in review_queue if row.get("needs_human_review"))
    passed = sum(
        1
        for row in review_queue
        if row.get("review_status") == "grounding_passed" and not row.get("needs_human_review")
    )
    return {
        "total_outputs": total,
        "needs_human_review_count": needs,
        "grounding_passed_count": passed,
    }


def _sign_off_summary(review_queue: list[dict[str, Any]]) -> dict[str, int]:
    eligible = sum(
        1
        for row in review_queue
        if row.get("review_status") == "grounding_passed" and not row.get("needs_human_review")
    )
    signed_off = sum(1 for row in review_queue if row.get("sign_off_status") == "signed_off")
    pending = sum(1 for row in review_queue if row.get("sign_off_status") == "pending_sign_off")
    return {
        "eligible_count": eligible,
        "signed_off_count": signed_off,
        "pending_sign_off_count": pending,
    }


def build_atlas_safe_human_review_artifact(
    review_queue: list[dict[str, Any]],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    queue = [dict(row) for row in review_queue if isinstance(row, dict)]
    flagged = [row for row in queue if row.get("needs_human_review")]
    governor_summary = summarize_governor_status(queue, root=project_root)
    circuit_guidance = build_circuit_breaker_operator_guidance(root=project_root)
    artifact: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "completed",
        "packet_id": PACKET_ID,
        "run_id": RUN_ID,
        "review_summary": _review_summary(queue),
        "sign_off_summary": _sign_off_summary(queue),
        "governor_summary": governor_summary,
        "circuit_breaker_guidance": circuit_guidance,
        "review_queue": queue,
        "flagged_review_queue": flagged,
        "operator_actions": [
            "Compare flagged sentence text against cited claim_ids in the grounded packet.",
            "Fix grounding overlap or re-run synthesize after packet corrections.",
            "Record operator sign-off for grounding-passed outputs before promoting prose.",
        ],
        "next_recommended_packet": {
            "id": "synthesis-sign-off-atlas-preview-status-badge",
            "title": "Atlas preview status badge for signed-off synthesis outputs",
        },
    }
    violations = assert_no_private_fields({"synthesis_human_review_artifact": artifact})
    if violations:
        raise SynthesisHumanReviewUIError(
            "Human-review artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return artifact


def sync_human_review_artifact_to_public_site(
    artifact: dict[str, Any],
    *,
    root: Path | None = None,
) -> Path:
    project_root = root or repo_root()
    path = project_root / DEFAULT_ATLAS_ARTIFACT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return path


def _scan_export_outputs(exports_dir: Path) -> list[tuple[float, Path]]:
    rows: list[tuple[float, Path]] = []
    if not exports_dir.is_dir():
        return rows
    for pattern in SYNTHESIS_OUTPUT_GLOBS:
        for path in exports_dir.glob(pattern):
            if path.is_file():
                rows.append((path.stat().st_mtime, path))
    rows.sort(key=lambda item: item[0], reverse=True)
    return rows


def _fixture_review_queue(*, root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in (FLAGGED_OUTPUT_FIXTURE_REL, PASSED_OUTPUT_FIXTURE_REL):
        output_path = root / rel
        output = _load_json(output_path)
        if output is None:
            continue
        rows.append(
            build_review_entry(
                output,
                source_path=rel.as_posix(),
                root=root,
            )
        )
    if rows:
        return rows
    return [
        build_review_entry(
            {
                "schema_version": "synthesis_output_v0.1.0",
                "packet_id": "syn_packet_grounded_dry_run_fixture",
                "provider": "mock_cloud",
                "summary_sentences": [
                    {
                        "text": "Fixture synthesis output for operator preview.",
                        "claim_ids": ["claim_preview_a"],
                        "atom_ids": ["atom_preview_001"],
                        "source_refs": ["src_preview_a"],
                    }
                ],
            },
            root=root,
        )
    ]


def run_synthesis_human_review_ui(
    *,
    sync_public: bool = False,
    fixture_mode: bool = True,
    exports_dir: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    review_queue: list[dict[str, Any]] = []
    source = "fixture"

    if not fixture_mode:
        if not _truthy_env("RGE_ALLOW_SYNTHESIS_HUMAN_REVIEW_UI"):
            return {
                "status": "blocked",
                "detail": "Export scan requires RGE_ALLOW_SYNTHESIS_HUMAN_REVIEW_UI=1",
            }
        scan_root = exports_dir or (project_root / "data/exports")
        scanned = _scan_export_outputs(scan_root)
        for _, path in scanned[:10]:
            output = _load_json(path)
            if output is None or not output.get("summary_sentences"):
                continue
            review_queue.append(
                build_review_entry(
                    output,
                    source_path=_safe_rel(path, project_root),
                    root=project_root,
                )
            )
        source = "export_scan"
    else:
        review_queue = _fixture_review_queue(root=project_root)

    artifact = build_atlas_safe_human_review_artifact(review_queue, root=project_root)
    export_dir = project_root / EXPORT_DIR_REL
    export_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = export_dir / ARTIFACT_NAME
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    public_path: Path | None = None
    if sync_public:
        public_path = sync_human_review_artifact_to_public_site(artifact, root=project_root)
    return {
        "status": "completed",
        "source": source,
        "artifact_path": _safe_rel(artifact_path, project_root),
        "public_artifact_path": _safe_rel(public_path, project_root) if public_path else None,
        "review_summary": artifact.get("review_summary") or {},
        "sign_off_summary": artifact.get("sign_off_summary") or {},
        "governor_summary": artifact.get("governor_summary") or {},
    }


def inspect_synthesis_human_review_plan_status(*, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    artifact_path = project_root / DEFAULT_ATLAS_ARTIFACT_REL
    payload = _load_json(artifact_path) if artifact_path.is_file() else None
    stale = _artifact_is_stale(artifact_path, root=project_root) if artifact_path.is_file() else True
    stale_reasons: list[str] = []
    if not payload:
        stale_reasons.append("atlas synthesis human-review artifact missing")
    elif stale:
        stale_reasons.append("artifact is stale relative to newer synthesis exports")

    review_summary = (payload or {}).get("review_summary") or {}
    flagged_count = int(review_summary.get("needs_human_review_count") or 0)
    synthesis_loop_recommended = bool(stale_reasons) or flagged_count > 0

    return {
        "status": "available" if payload else "unavailable",
        "artifact_path": _safe_rel(artifact_path, project_root),
        "synthesis_loop_recommended": synthesis_loop_recommended,
        "stale_reasons": stale_reasons,
        "flagged_review_count": flagged_count,
        "operator_commands": {
            "standalone_mock_loop": (
                "python scripts/run_end_to_end_synthesis_operator_loop.py "
                "--fixture-packet --sync-public"
            ),
            "refresh_human_review_ui": (
                f"python {CLI_SCRIPT} --sync-public"
            ),
        },
        "env_setup": [
            '$env:RGE_ALLOW_SYNTHESIS_OPERATOR_LOOP = "1"',
        ],
        "updated_at": utc_now_iso(),
    }
