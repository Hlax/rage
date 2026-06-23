"""Public-safe Atlas operator preview for Tier 2 patch staging bundles."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.autonomous_synthesis_governor import _safe_rel, utc_now_iso
from rge.modules.principal_audit_gate import repo_root
from rge.modules.tier2_patch_staging import (
    BUNDLE_SCHEMA_VERSION,
    Tier2PatchStagingError,
    discover_latest_patch_bundle,
    inspect_tier2_patch_staging_status,
    load_patch_bundle,
    patch_staging_dir,
)

ATLAS_ARTIFACT_REL = Path(
    "apps/public-site/public/data/atlas_tier2_patch_staging_latest.json"
)
ATLAS_ARTIFACT_SCHEMA = "atlas_tier2_patch_staging_v0.1.0"
REFRESH_CLI_SCRIPT = "scripts/refresh_tier2_patch_staging_preview.py"

_FORBIDDEN_REASON_PATTERNS = (
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
    re.compile(r"\.env\.local", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9]{8,}", re.IGNORECASE),
    re.compile(r"private_notes", re.IGNORECASE),
)


class Tier2PatchStagingPreviewError(RuntimeError):
    """Raised when preview artifact cannot be built safely."""


def atlas_artifact_path(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / ATLAS_ARTIFACT_REL


def _path_summary(value: str | None, *, root: Path) -> tuple[str | None, str | None]:
    if not value or not str(value).strip():
        return None, None
    raw = str(value).replace("\\", "/").strip()
    if re.match(r"^[A-Za-z]:/", raw) or raw.startswith("/"):
        label = Path(raw).name
        return label, label
    rel = _safe_rel(Path(raw), root) if not raw.startswith("data/") else raw
    if rel.startswith(".."):
        label = Path(raw).name
        return label, label
    return Path(rel).name, rel


def _scrub_validation_reasons(reasons: list[Any] | None, *, limit: int = 5) -> list[str]:
    scrubbed: list[str] = []
    for item in list(reasons or [])[:limit]:
        text = str(item).replace("\\", "/")
        for pattern in _FORBIDDEN_REASON_PATTERNS:
            if pattern.search(text):
                text = pattern.sub("[redacted]", text)
        scrubbed.append(text[:240])
    return scrubbed


def _patch_revalidation_summary_from_draft(
    bundle: dict[str, Any],
    *,
    root: Path,
) -> dict[str, Any] | None:
    draft_rel = bundle.get("draft_ticket_path")
    if not draft_rel:
        return None
    draft_path = Path(str(draft_rel))
    if not draft_path.is_absolute():
        draft_path = root / draft_path
    if not draft_path.is_file():
        return None
    try:
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    summary = draft.get("last_patch_revalidation")
    backfilled_at = draft.get("expected_files_backfilled_at")
    if not summary and not backfilled_at:
        return None
    merged: dict[str, Any] = dict(summary) if isinstance(summary, dict) else {"status": "none"}
    if backfilled_at:
        merged["backfilled_at"] = str(backfilled_at)
    return merged


def _resolve_next_recommended_action(verdict: str | None) -> str:
    normalized = str(verdict or "UNKNOWN").upper()
    if normalized == "GO":
        return "apply_staged_patch_and_commit"
    if normalized == "PARTIAL":
        return "fix_staged_patch"
    if normalized == "NO-GO":
        return "fix_staged_patch_blocked"
    if normalized in {"PENDING", "UNKNOWN"}:
        return "validate_staged_patch"
    return "stage_patch_bundle"


def build_atlas_safe_tier2_patch_staging_artifact(
    bundle: dict[str, Any],
    *,
    root: Path | None = None,
    preview_freshness: str = "fresh",
) -> dict[str, Any]:
    project_root = root or repo_root()
    diff = bundle.get("diff_summary") if isinstance(bundle.get("diff_summary"), dict) else {}
    draft_label, draft_path_summary = _path_summary(
        str(bundle.get("draft_ticket_path") or ""),
        root=project_root,
    )
    packet_label, packet_path_summary = _path_summary(
        str(bundle.get("instruction_packet_path") or ""),
        root=project_root,
    )
    verdict = str(bundle.get("validation_verdict") or "UNKNOWN")
    artifact = {
        "schema_version": ATLAS_ARTIFACT_SCHEMA,
        "status": "available",
        "bundle_schema_version": str(bundle.get("schema_version") or BUNDLE_SCHEMA_VERSION),
        "bundle_id": str(bundle.get("bundle_id") or ""),
        "draft_ticket_label": draft_label,
        "draft_ticket_path_summary": draft_path_summary,
        "instruction_packet_label": packet_label,
        "instruction_packet_path_summary": packet_path_summary,
        "branch_name": str(bundle.get("branch_name") or ""),
        "validation_verdict": verdict,
        "risk_class": str(bundle.get("risk_class") or "unknown"),
        "changed_file_count": int(diff.get("changed_file_count") or 0),
        "lines_added": int(diff.get("lines_added") or 0),
        "lines_removed": int(diff.get("lines_removed") or 0),
        "safety_audit_required": bool(bundle.get("safety_audit_required")),
        "test_plan_count": len(bundle.get("test_plan") or []),
        "validation_reasons": _scrub_validation_reasons(bundle.get("validation_reasons")),
        "next_recommended_action": _resolve_next_recommended_action(verdict),
        "apply_ready": verdict == "GO",
        "stop_state": verdict in {"PARTIAL", "NO-GO"},
        "preview_freshness": preview_freshness,
        "patch_revalidation_summary": _patch_revalidation_summary_from_draft(
            bundle,
            root=project_root,
        ),
        "source_bundle_path": bundle.get("_bundle_path"),
        "generated_at": bundle.get("generated_at"),
        "updated_at": utc_now_iso(),
        "forbidden_in_preview": [
            "raw_diff",
            "raw_file_contents",
            "secrets",
            "raw_prompts",
            "absolute_paths",
            "private_notes",
            "operator_ledger_content",
        ],
    }
    violations = assert_no_private_fields({"tier2_patch_staging_artifact": artifact})
    if violations:
        raise Tier2PatchStagingPreviewError(
            "Atlas tier2 patch staging artifact blocked: " + "; ".join(violations[:5])
        )
    return artifact


def build_missing_tier2_patch_staging_artifact(*, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    artifact = {
        "schema_version": ATLAS_ARTIFACT_SCHEMA,
        "status": "missing",
        "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
        "bundle_id": None,
        "draft_ticket_label": None,
        "draft_ticket_path_summary": None,
        "instruction_packet_label": None,
        "instruction_packet_path_summary": None,
        "branch_name": None,
        "validation_verdict": "UNKNOWN",
        "risk_class": "unknown",
        "changed_file_count": 0,
        "lines_added": 0,
        "lines_removed": 0,
        "safety_audit_required": False,
        "test_plan_count": 0,
        "validation_reasons": [],
        "next_recommended_action": "stage_patch_bundle",
        "apply_ready": False,
        "stop_state": False,
        "preview_freshness": "missing",
        "patch_revalidation_summary": None,
        "source_bundle_path": None,
        "generated_at": None,
        "updated_at": utc_now_iso(),
        "forbidden_in_preview": [
            "raw_diff",
            "raw_file_contents",
            "secrets",
            "raw_prompts",
            "absolute_paths",
            "private_notes",
            "operator_ledger_content",
        ],
    }
    violations = assert_no_private_fields({"tier2_patch_staging_artifact": artifact})
    if violations:
        raise Tier2PatchStagingPreviewError(
            "Atlas tier2 patch staging missing artifact blocked: "
            + "; ".join(violations[:5])
        )
    return artifact


def _bundle_mtime(bundle_path: Path | None, *, root: Path) -> float | None:
    if bundle_path is None:
        return None
    candidate = bundle_path if bundle_path.is_absolute() else root / bundle_path
    if not candidate.is_file():
        return None
    return candidate.stat().st_mtime


def inspect_tier2_patch_staging_preview_status(*, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    artifact_path = atlas_artifact_path(root=project_root)
    latest = discover_latest_patch_bundle(root=project_root)
    staging_status = inspect_tier2_patch_staging_status(root=project_root)

    artifact_exists = artifact_path.is_file()
    artifact_mtime = artifact_path.stat().st_mtime if artifact_exists else None
    bundle_path = latest.get("bundle_path")
    bundle_mtime = _bundle_mtime(
        project_root / str(bundle_path) if bundle_path else None,
        root=project_root,
    )

    preview_freshness = "missing"
    refresh_recommended = False
    refresh_reasons: list[str] = []

    if latest.get("status") != "available":
        if not artifact_exists:
            refresh_reasons.append("atlas tier2 patch staging preview artifact missing")
    elif not artifact_exists:
        preview_freshness = "missing"
        refresh_recommended = True
        refresh_reasons.append("atlas preview missing for latest staged patch bundle")
    elif bundle_mtime is not None and artifact_mtime is not None:
        if bundle_mtime > artifact_mtime:
            preview_freshness = "stale"
            refresh_recommended = True
            refresh_reasons.append("latest patch bundle is newer than atlas preview artifact")
        else:
            preview_freshness = "fresh"

    return {
        "status": "available",
        "artifact_path": _safe_rel(artifact_path, project_root),
        "artifact_exists": artifact_exists,
        "latest_bundle_path": bundle_path,
        "latest_bundle_validation_verdict": latest.get("validation_verdict"),
        "preview_freshness": preview_freshness,
        "preview_refresh_recommended": refresh_recommended,
        "preview_refresh_reasons": refresh_reasons,
        "tier2_patch_staging_preview_refresh_recommended": refresh_recommended,
        "operator_commands": {
            "refresh_preview_latest": (
                f"python {REFRESH_CLI_SCRIPT} --latest --sync-public"
            ),
            "refresh_preview_bundle": (
                f"python {REFRESH_CLI_SCRIPT} --bundle PATH --sync-public"
            ),
        },
        "staging_status": staging_status,
    }


def sync_public_tier2_patch_staging_artifact(
    artifact: dict[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    path = atlas_artifact_path(root=project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "completed",
        "public_artifact_path": _safe_rel(path, project_root),
        "validation_verdict": artifact.get("validation_verdict"),
        "preview_freshness": artifact.get("preview_freshness"),
    }


def refresh_tier2_patch_staging_preview(
    *,
    bundle: Path | None = None,
    latest: bool = False,
    sync_public: bool = True,
    dry_run: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    bundle_path: Path | None = None
    bundle_payload: dict[str, Any] | None = None

    if bundle is not None:
        bundle_payload = load_patch_bundle(bundle, root=project_root)
        bundle_path = project_root / str(bundle_payload["_bundle_path"])
    elif latest:
        info = discover_latest_patch_bundle(root=project_root)
        if info.get("status") != "available" or not info.get("bundle_path"):
            raise Tier2PatchStagingPreviewError(
                "no patch staging bundle available for --latest preview refresh"
            )
        bundle_path = project_root / str(info["bundle_path"])
        bundle_payload = load_patch_bundle(bundle_path, root=project_root)
    else:
        raise Tier2PatchStagingPreviewError("requires --latest or --bundle PATH")

    if bundle_payload.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        raise Tier2PatchStagingPreviewError(
            f"unsupported bundle schema: {bundle_payload.get('schema_version')}"
        )

    artifact = build_atlas_safe_tier2_patch_staging_artifact(
        bundle_payload,
        root=project_root,
        preview_freshness="fresh",
    )
    payload = {
        "status": "dry_run" if dry_run else "completed",
        "verdict": artifact.get("validation_verdict"),
        "artifact": artifact,
        "source_bundle_path": artifact.get("source_bundle_path"),
        "dry_run": dry_run,
    }
    if sync_public and not dry_run:
        payload["sync"] = sync_public_tier2_patch_staging_artifact(artifact, root=project_root)
    return payload


def run_refresh_tier2_patch_staging_preview_command(
    *,
    bundle: Path | None = None,
    latest: bool = False,
    sync_public: bool = True,
    dry_run: bool = False,
    root: Path | None = None,
) -> tuple[dict[str, Any], int]:
    payload = refresh_tier2_patch_staging_preview(
        bundle=bundle,
        latest=latest,
        sync_public=sync_public,
        dry_run=dry_run,
        root=root,
    )
    verdict = str(payload.get("verdict") or "UNKNOWN")
    exit_code = 0 if verdict in {"GO", "PARTIAL", "NO-GO", "PENDING", "UNKNOWN"} else 1
    if payload.get("dry_run"):
        exit_code = 0
    return payload, exit_code


def public_safe_summary(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "status",
        "verdict",
        "source_bundle_path",
        "dry_run",
        "sync",
    }
    summary = {key: payload[key] for key in allowed if key in payload}
    artifact = payload.get("artifact")
    if isinstance(artifact, dict):
        summary["validation_verdict"] = artifact.get("validation_verdict")
        summary["preview_freshness"] = artifact.get("preview_freshness")
        summary["next_recommended_action"] = artifact.get("next_recommended_action")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh Atlas Tier 2 patch staging operator preview artifact."
    )
    parser.add_argument("--latest", action="store_true")
    parser.add_argument("--bundle", type=Path, default=None)
    parser.add_argument("--sync-public", action="store_true", default=True)
    parser.add_argument("--no-sync-public", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        payload, exit_code = run_refresh_tier2_patch_staging_preview_command(
            bundle=args.bundle,
            latest=args.latest,
            sync_public=not args.no_sync_public,
            dry_run=args.dry_run,
            root=args.root,
        )
        print(json.dumps(public_safe_summary(payload) if not args.dry_run else payload, indent=2))
        return exit_code
    except Tier2PatchStagingPreviewError as exc:
        print(json.dumps({"status": "error", "detail": str(exc)}, indent=2))
        return 1
