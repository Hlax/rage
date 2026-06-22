"""Convert governor GO instruction packets into local implementation ticket drafts.

Draft tickets live under ``data/operator/draft_tickets/`` only. They are never
promoted into the canonical ``tickets/`` queue or ``TICKET_QUEUE.md``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rge.modules.autonomous_synthesis_governor import (
    FORBIDDEN_ACTION_PATTERNS,
    FORBIDDEN_GATE_WEAKENING_PATTERNS,
    LOCAL_PATH_PATTERNS,
    RAW_DOCUMENT_PATTERNS,
    _private_value_violations,
    _safe_rel,
    instruction_packet_dir,
    load_governor_ledger,
    utc_now_iso,
)
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.principal_audit_gate import repo_root
from rge.safety.public_export_policy import FORBIDDEN_VALUE_PATTERNS

DRAFT_SCHEMA_VERSION = "instruction_packet_ticket_draft_v0.1.0"
DEFAULT_DRAFT_DIR_REL = Path("data/operator/draft_tickets")
DEFAULT_STATUS_REPORT_REL = Path("data/operator/instruction_packet_ticket_draft_status_latest.json")
DRAFT_CLI_SCRIPT = "scripts/run_instruction_packet_ticket_draft.py"
BACKFILL_CLI_SCRIPT = "scripts/run_draft_expected_files_backfill.py"

GOVERNOR_VERDICT_RE = re.compile(
    r"Governor verdict:\s*(GO|PARTIAL|NO-GO)",
    re.IGNORECASE,
)
CITATION_LINE_RE = re.compile(
    r"^\-\s*(Claim refs|Atom refs|Source refs):\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
BULLET_RE = re.compile(r"^\-\s+`?([^`\n]+)`?\s*$", re.MULTILINE)


class InstructionPacketTicketDraftError(RuntimeError):
    """Raised when instruction packet draft validation or write fails."""


def draft_ticket_dir(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_DRAFT_DIR_REL


def draft_status_report_path(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_STATUS_REPORT_REL


def discover_latest_instruction_packet(*, root: Path | None = None) -> dict[str, Any]:
    """Return metadata for the newest instruction packet markdown file."""
    project_root = root or repo_root()
    packet_dir = instruction_packet_dir(root=project_root)
    if not packet_dir.is_dir():
        return {
            "status": "missing",
            "instruction_packet_path": None,
            "detail": "instruction packet directory does not exist",
        }
    candidates = sorted(
        (path for path in packet_dir.glob("*.md") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return {
            "status": "missing",
            "instruction_packet_path": None,
            "detail": "no instruction packets found",
        }
    latest = candidates[0]
    return {
        "status": "available",
        "instruction_packet_path": _safe_rel(latest, project_root),
        "modified_at": datetime.fromtimestamp(
            latest.stat().st_mtime,
            tz=timezone.utc,
        ).replace(microsecond=0).isoformat(),
    }


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(SECTION_RE.finditer(text))
    for index, match in enumerate(matches):
        title = match.group(1).strip().casefold()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def parse_instruction_packet_text(text: str) -> dict[str, Any]:
    """Parse a governor instruction packet markdown file into structured fields."""
    sections = _split_sections(text)
    title_match = re.search(
        r"^#\s+Autonomous Synthesis Instruction Packet:\s*(.+)$",
        text,
        re.MULTILINE,
    )
    packet_id = title_match.group(1).strip() if title_match else "unknown_packet"

    claim_refs: list[str] = []
    atom_refs: list[str] = []
    source_refs: list[str] = []
    citations = sections.get("citations", "")
    for match in CITATION_LINE_RE.finditer(citations):
        label = match.group(1).casefold()
        raw_values = match.group(2).strip()
        if raw_values.casefold() in {"none", "n/a", ""}:
            values: list[str] = []
        else:
            values = [item.strip() for item in raw_values.split(",") if item.strip()]
        if label.startswith("claim"):
            claim_refs = values
        elif label.startswith("atom"):
            atom_refs = values
        elif label.startswith("source"):
            source_refs = values

    def _bullets(section_key: str) -> list[str]:
        body = sections.get(section_key, "")
        return [
            item.strip()
            for item in BULLET_RE.findall(body)
            if item.strip()
        ]

    plain_bullets = sections.get("explicit non-goals", "")
    non_goals = [
        line.removeprefix("- ").strip()
        for line in plain_bullets.splitlines()
        if line.strip().startswith("-")
    ] or _bullets("explicit non-goals")

    safety_notes = [
        line.removeprefix("- ").strip()
        for line in sections.get("safety notes", "").splitlines()
        if line.strip().startswith("-")
    ]
    governor_verdict = None
    for note in safety_notes:
        verdict_match = GOVERNOR_VERDICT_RE.search(note)
        if verdict_match:
            governor_verdict = verdict_match.group(1).upper()
            break
    if governor_verdict is None:
        for note in safety_notes:
            if "governor verdict" in note.casefold():
                governor_verdict = "UNKNOWN"

    build_title = sections.get("recommended build packet", "").strip()
    summary = sections.get("summary", "").strip()
    likely_files = _bullets("files likely affected")
    acceptance = [
        line.removeprefix("- ").strip()
        for line in sections.get("acceptance criteria", "").splitlines()
        if line.strip().startswith("-")
    ]
    tests = _bullets("tests to run")

    return {
        "packet_id": packet_id,
        "summary": summary,
        "build_title": build_title,
        "claim_refs": claim_refs,
        "atom_refs": atom_refs,
        "source_refs": source_refs,
        "likely_files": likely_files,
        "acceptance_criteria": acceptance,
        "tests_recommended": tests,
        "non_goals": non_goals,
        "safety_notes": safety_notes,
        "governor_verdict": governor_verdict,
        "rollback_plan": sections.get("rollback plan", "").strip(),
    }


_INFERENCE_ALLOWED_PREFIXES = (
    "rge/",
    "tests/",
    "scripts/",
    "docs/",
    "agent_reports/",
    "apps/public-site/",
    "domain_packs/",
    "fixtures/",
)


def _normalize_inference_path(raw: str) -> str | None:
    normalized = raw.replace("\\", "/").strip().strip("`")
    if not normalized:
        return None
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if not any(normalized.startswith(prefix) for prefix in _INFERENCE_ALLOWED_PREFIXES):
        return None
    return normalized


def infer_expected_files(
    parsed: dict[str, Any],
    *,
    root: Path | None = None,
) -> list[str]:
    """Infer draft expected_files from packet content and source/test pairing heuristics."""
    project_root = root or repo_root()
    collected: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        path = _normalize_inference_path(raw)
        if path is None or path in seen:
            return
        seen.add(path)
        collected.append(path)

    for item in parsed.get("likely_files") or []:
        add(str(item))

    for section_key in ("build_title", "summary", "rollback_plan"):
        for match in re.finditer(r"`([^`]+)`", str(parsed.get(section_key) or "")):
            add(match.group(1))

    for test_line in parsed.get("tests_recommended") or []:
        for match in re.finditer(
            r"(tests/\S+\.py|rge/\S+\.py|scripts/\S+\.py|apps/public-site/\S+)",
            str(test_line),
        ):
            add(match.group(1))

    for source_path in list(collected):
        if not source_path.startswith("rge/") or not source_path.endswith(".py"):
            continue
        basename = Path(source_path).stem
        rel_under_rge = source_path[len("rge/") : -3].replace("/", "_")
        candidates = [
            f"tests/unit/test_{basename}.py",
            f"tests/unit/test_{rel_under_rge}.py",
            f"tests/golden/test_{basename}.py",
        ]
        matched = False
        for candidate in candidates:
            if (project_root / candidate).is_file():
                add(candidate)
                matched = True
                break
        if not matched:
            add(candidates[0])

    return sorted(collected)


def parsed_from_draft(
    draft: dict[str, Any],
    *,
    instruction_packet_text: str | None = None,
) -> dict[str, Any]:
    """Rebuild parser-shaped input for infer_expected_files from a draft ticket."""
    if instruction_packet_text:
        parsed = parse_instruction_packet_text(instruction_packet_text)
        packet_id = str(draft.get("id") or "draft")
        parsed.setdefault("packet_id", packet_id)
        return parsed
    return {
        "packet_id": str(draft.get("id") or "draft"),
        "likely_files": list(draft.get("expected_files") or []),
        "tests_recommended": list(draft.get("test_plan") or []),
        "build_title": str(draft.get("title") or ""),
        "summary": str(draft.get("problem") or ""),
        "rollback_plan": str(draft.get("rollback_plan") or ""),
        "acceptance_criteria": list(draft.get("acceptance_criteria") or []),
        "non_goals": list(draft.get("non_goals") or []),
        "safety_notes": list(draft.get("safety_notes") or []),
        "claim_refs": [],
        "atom_refs": [],
        "source_refs": [],
        "governor_verdict": draft.get("governor_verdict") or "GO",
    }


def backfill_draft_expected_files(
    draft_path: Path,
    *,
    dry_run: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    """Re-infer expected_files on an existing draft without re-handoff."""
    project_root = root or repo_root()
    candidate = draft_path if draft_path.is_absolute() else project_root / draft_path
    if not candidate.is_file():
        raise InstructionPacketTicketDraftError(f"draft ticket not found: {draft_path}")
    draft = json.loads(candidate.read_text(encoding="utf-8"))
    packet_text: str | None = None
    packet_ref = draft.get("source_instruction_packet")
    if packet_ref:
        packet_path = project_root / str(packet_ref)
        if packet_path.is_file():
            packet_text = packet_path.read_text(encoding="utf-8")
    parsed = parsed_from_draft(draft, instruction_packet_text=packet_text)
    inferred = infer_expected_files(parsed, root=project_root)
    previous = [str(item).replace("\\", "/") for item in (draft.get("expected_files") or [])]
    added = [path for path in inferred if path not in previous]
    removed = [path for path in previous if path not in inferred]
    changed = bool(added or removed)
    result = {
        "status": "dry_run" if dry_run else ("updated" if changed else "unchanged"),
        "draft_ticket_path": _safe_rel(candidate, project_root),
        "draft_ticket_id": draft.get("id"),
        "previous_expected_files": previous,
        "inferred_expected_files": inferred,
        "added_files": added,
        "removed_files": removed,
        "expected_files_inferred": True,
        "dry_run": dry_run,
    }
    if changed and not dry_run:
        draft["expected_files"] = inferred
        draft["expected_files_inferred"] = True
        draft["expected_files_backfilled_at"] = utc_now_iso()
        violations = assert_no_private_fields({"draft_ticket": draft})
        if violations:
            raise InstructionPacketTicketDraftError(
                "draft backfill blocked: " + "; ".join(violations[:5])
            )
        candidate.write_text(json.dumps(draft, indent=2) + "\n", encoding="utf-8")
        from rge.modules.tier2_patch_staging import (
            revalidate_latest_patch_bundle_for_draft,
            revalidate_patch_after_backfill_enabled,
        )

        if revalidate_patch_after_backfill_enabled():
            revalidation = revalidate_latest_patch_bundle_for_draft(
                str(draft.get("id")),
                root=project_root,
            )
            result["patch_revalidation"] = revalidation
            summary = public_patch_revalidation_summary(revalidation)
            if summary is not None:
                draft["last_patch_revalidation"] = summary
                candidate.write_text(json.dumps(draft, indent=2) + "\n", encoding="utf-8")
    return result


def run_draft_expected_files_backfill_command(
    *,
    draft_ticket: Path | None = None,
    latest: bool = False,
    all_drafts: bool = False,
    dry_run: bool = False,
    root: Path | None = None,
) -> tuple[dict[str, Any], int]:
    project_root = root or repo_root()
    draft_dir = draft_ticket_dir(root=project_root)
    targets: list[Path] = []
    if all_drafts:
        if draft_dir.is_dir():
            targets = sorted(draft_dir.glob("draft_*.json"))
    elif latest:
        discovery = latest_draft_ticket(root=project_root)
        if discovery.get("status") != "available":
            return (
                {
                    "verdict": "NO-GO",
                    "status": "error",
                    "detail": "no draft ticket found for --latest",
                },
                1,
            )
        targets = [project_root / str(discovery["draft_ticket_path"])]
    elif draft_ticket is not None:
        targets = [draft_ticket]
    else:
        return (
            {
                "verdict": "NO-GO",
                "status": "error",
                "detail": "requires --latest, --draft-ticket PATH, or --all",
            },
            2,
        )

    if not targets:
        return (
            {
                "verdict": "NO-GO",
                "status": "error",
                "detail": "no draft tickets matched backfill request",
            },
            1,
        )

    results = [
        backfill_draft_expected_files(path, dry_run=dry_run, root=project_root)
        for path in targets
    ]
    updated = sum(1 for row in results if row.get("status") == "updated")
    payload = {
        "verdict": "GO",
        "status": "dry_run" if dry_run else "completed",
        "draft_count": len(results),
        "updated_count": updated,
        "results": results,
        "dry_run": dry_run,
    }
    return payload, 0


def _latest_go_instruction_packet_from_ledger(*, root: Path) -> dict[str, Any] | None:
    ledger = load_governor_ledger(root=root)
    go_reviews = [
        row
        for row in ledger.get("reviews") or []
        if isinstance(row, dict)
        and row.get("governor_verdict") == "GO"
        and row.get("latest_instruction_packet")
    ]
    if not go_reviews:
        return None
    go_reviews.sort(key=lambda row: str(row.get("reviewed_at") or ""), reverse=True)
    return go_reviews[0]


def _content_policy_violations(text: str, *, label: str) -> list[str]:
    reasons = _private_value_violations({"content": text}, label=label)
    sections = _split_sections(text)
    action_scan = "\n".join(
        sections.get(key, "")
        for key in (
            "summary",
            "recommended build packet",
            "files likely affected",
            "acceptance criteria",
            "tests to run",
        )
    )
    for pattern in (*FORBIDDEN_ACTION_PATTERNS, *FORBIDDEN_GATE_WEAKENING_PATTERNS):
        if pattern.search(action_scan):
            reasons.append(
                f"{label} recommends forbidden merge/push/publish/promote or gate-weakening action"
            )
    for pattern in (*FORBIDDEN_VALUE_PATTERNS, *RAW_DOCUMENT_PATTERNS, *LOCAL_PATH_PATTERNS):
        if pattern.search(text):
            reasons.append(f"{label} contains forbidden secret/raw/path content")
    lowered = text.casefold()
    if "private_notes" in lowered or "private notes" in lowered:
        reasons.append(f"{label} references private notes")
    return reasons


def validate_instruction_packet_for_draft(
    *,
    packet_path: Path,
    parsed: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    """Apply deterministic validation gates before writing a draft ticket."""
    reasons: list[str] = []
    if not packet_path.is_file():
        reasons.append("instruction packet file is missing")
        return {"passed": False, "reasons": reasons}

    text = packet_path.read_text(encoding="utf-8")
    reasons.extend(_content_policy_violations(text, label="instruction_packet"))

    verdict = parsed.get("governor_verdict")
    if verdict in {"PARTIAL", "NO-GO"}:
        reasons.append(f"instruction packet governor verdict is {verdict}")
    elif verdict != "GO":
        reasons.append("instruction packet is not from a GO/auto-signed-off governor output")

    claim_refs = parsed.get("claim_refs") or []
    atom_refs = parsed.get("atom_refs") or []
    source_refs = parsed.get("source_refs") or []
    if not claim_refs and not atom_refs:
        reasons.append("instruction packet missing claim and atom refs")
    if not source_refs:
        reasons.append("instruction packet missing source refs")

    latest_go = _latest_go_instruction_packet_from_ledger(root=root)
    rel_path = _safe_rel(packet_path, root)
    if latest_go:
        latest_packet = str(latest_go.get("latest_instruction_packet") or "")
        if latest_packet and latest_packet != rel_path:
            reasons.append(
                "instruction packet is stale; a newer GO governor output exists at "
                f"{latest_packet}"
            )
        if latest_go.get("governor_verdict") != "GO":
            reasons.append("latest governor ledger review is not GO")

    return {"passed": not reasons, "reasons": reasons, "latest_go_review": latest_go}


def _draft_ticket_name(packet_id: str) -> str:
    safe_packet_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", packet_id).strip("-") or "packet"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"draft_{stamp}_{safe_packet_id}.json"


def build_draft_ticket_payload(
    *,
    parsed: dict[str, Any],
    instruction_packet_path: str,
    validation: dict[str, Any],
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    packet_id = str(parsed.get("packet_id") or "unknown_packet")
    draft_id = f"draft-from-{re.sub(r'[^A-Za-z0-9_.-]+', '-', packet_id).strip('-') or 'packet'}"
    expected_files = infer_expected_files(parsed, root=project_root)
    evidence = [
        *(f"claim:{item}" for item in parsed.get("claim_refs") or []),
        *(f"atom:{item}" for item in parsed.get("atom_refs") or []),
        *(f"source:{item}" for item in parsed.get("source_refs") or []),
    ]
    return {
        "schema_version": DRAFT_SCHEMA_VERSION,
        "id": draft_id,
        "status": "draft",
        "source": "instruction_packet_ticket_draft",
        "source_instruction_packet": instruction_packet_path,
        "governor_verdict": parsed.get("governor_verdict") or "GO",
        "auto_signed_off": True,
        "title": parsed.get("build_title") or f"Implement synthesis finding: {packet_id}",
        "problem": parsed.get("summary") or "Review the governor instruction packet summary.",
        "evidence": evidence,
        "expected_files": expected_files,
        "expected_files_inferred": True,
        "acceptance_criteria": list(parsed.get("acceptance_criteria") or []),
        "test_plan": list(parsed.get("tests_recommended") or []),
        "non_goals": list(parsed.get("non_goals") or []),
        "safety_notes": list(parsed.get("safety_notes") or []),
        "rollback_plan": parsed.get("rollback_plan")
        or "Delete the draft ticket and regenerate from a fresh GO instruction packet.",
        "validation": {
            "passed": validation.get("passed"),
            "reasons": list(validation.get("reasons") or []),
        },
        "forbidden_actions": [
            "auto_merge",
            "auto_push",
            "auto_publish",
            "auto_promote_ticket",
            "edit_TICKET_QUEUE",
        ],
        "created_at": utc_now_iso(),
    }


def latest_draft_ticket(*, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    out_dir = draft_ticket_dir(root=project_root)
    if not out_dir.is_dir():
        return {"status": "missing", "draft_ticket_path": None}
    candidates = sorted(
        (path for path in out_dir.glob("draft_*.json") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return {"status": "missing", "draft_ticket_path": None}
    latest = candidates[0]
    payload = json.loads(latest.read_text(encoding="utf-8"))
    return {
        "status": "available",
        "draft_ticket_path": _safe_rel(latest, project_root),
        "draft_ticket_id": payload.get("id"),
        "source_instruction_packet": payload.get("source_instruction_packet"),
        "acceptance_criteria_count": len(payload.get("acceptance_criteria") or []),
    }


def write_draft_status_report(
    summary: dict[str, Any],
    *,
    root: Path | None = None,
) -> Path:
    project_root = root or repo_root()
    path = draft_status_report_path(root=project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": DRAFT_SCHEMA_VERSION,
        "recorded_at": utc_now_iso(),
        **summary,
    }
    violations = assert_no_private_fields({"draft_status": payload})
    if violations:
        raise InstructionPacketTicketDraftError(
            "Draft status report blocked: " + "; ".join(violations[:5])
        )
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def draft_needs_expected_files_backfill(draft: dict[str, Any]) -> bool:
    if draft.get("expected_files_inferred") is True:
        return False
    return bool(draft.get("expected_files") or draft.get("source_instruction_packet"))


def public_patch_revalidation_summary(
    revalidation: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Public-safe patch revalidation summary for draft tickets and Atlas preview."""
    if not revalidation:
        return None
    reasons = revalidation.get("validation_reasons") or []
    bundle_path = str(revalidation.get("bundle_path") or "")
    bundle_label = Path(bundle_path.replace("\\", "/")).name if bundle_path else None
    return {
        "status": revalidation.get("status"),
        "validation_verdict": revalidation.get("validation_verdict"),
        "passed": revalidation.get("passed"),
        "reason_count": len(reasons),
        "bundle_path_summary": bundle_label,
    }


def execute_safe_draft_backfill_enabled() -> bool:
    return os.environ.get("RGE_EXECUTE_SAFE_DRAFT_BACKFILL", "0").strip().casefold() in {
        "1",
        "true",
        "yes",
    }


def run_execute_safe_draft_backfill_hook(
    *,
    root: Path | None = None,
    action_id: str | None = None,
) -> dict[str, Any] | None:
    """Optional execute-safe hook: backfill draft expected_files when that is the only blocker."""
    if not execute_safe_draft_backfill_enabled():
        return None
    if action_id != "run_draft_expected_files_backfill":
        return {"status": "skipped", "reason": "draft backfill is not the current blocker"}

    project_root = root or repo_root()
    payload, exit_code = run_draft_expected_files_backfill_command(
        latest=True,
        root=project_root,
    )
    revalidations = [
        row.get("patch_revalidation")
        for row in (payload.get("results") or [])
        if row.get("patch_revalidation")
    ]
    return {
        "status": "completed" if exit_code == 0 else "error",
        "verdict": payload.get("verdict"),
        "updated_count": payload.get("updated_count"),
        "draft_count": payload.get("draft_count"),
        "patch_revalidation_summaries": [
            summary
            for row in revalidations
            if (summary := public_patch_revalidation_summary(row)) is not None
        ]
        or None,
    }


def run_execute_safe_tier2_hook_chain(
    *,
    root: Path | None = None,
    working_tree: Any | None = None,
    action_id: str | None = None,
) -> dict[str, Any]:
    """Run backfill hook then patch-staging hook when backfill leaves a controlled-dirty tree."""
    from rge.modules.operator_loop import inspect_working_tree
    from rge.modules.tier2_patch_staging import (
        execute_safe_patch_staging_enabled,
        patch_staging_execute_safe_tree_ok,
        run_execute_safe_patch_staging_hook,
    )

    project_root = root or repo_root()
    tree_before = working_tree or inspect_working_tree(project_root)
    backfill = run_execute_safe_draft_backfill_hook(
        root=project_root,
        action_id=action_id,
    )

    patch_staging: dict[str, Any] | None = None
    chained_patch_staging = False
    tree_became_controlled_dirty = False

    if backfill is not None and backfill.get("status") == "completed":
        tree_after = inspect_working_tree(project_root)
        tree_became_controlled_dirty = (
            tree_before.clean
            and not tree_after.clean
            and patch_staging_execute_safe_tree_ok(tree_after, root=project_root)
        )
        if tree_became_controlled_dirty and execute_safe_patch_staging_enabled():
            patch_staging = run_execute_safe_patch_staging_hook(
                root=project_root,
                working_tree=tree_after,
            )
            chained_patch_staging = True
    elif execute_safe_patch_staging_enabled() and patch_staging_execute_safe_tree_ok(
        tree_before,
        root=project_root,
    ):
        patch_staging = run_execute_safe_patch_staging_hook(
            root=project_root,
            working_tree=tree_before,
        )

    if backfill is None and patch_staging is None:
        return {"status": "skipped", "reason": "no execute-safe tier2 hooks enabled"}

    return {
        "status": "completed",
        "backfill": backfill,
        "patch_staging": patch_staging,
        "chained_patch_staging": chained_patch_staging,
        "tree_became_controlled_dirty": tree_became_controlled_dirty,
    }


def inspect_instruction_packet_ticket_draft_status(*, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    latest_packet = discover_latest_instruction_packet(root=project_root)
    latest_draft = latest_draft_ticket(root=project_root)
    latest_draft_payload: dict[str, Any] | None = None
    if latest_draft.get("draft_ticket_path"):
        draft_path = project_root / str(latest_draft["draft_ticket_path"])
        if draft_path.is_file():
            latest_draft_payload = json.loads(draft_path.read_text(encoding="utf-8"))
    return {
        "status": "available",
        "latest_instruction_packet": latest_packet.get("instruction_packet_path"),
        "latest_draft_ticket_path": latest_draft.get("draft_ticket_path"),
        "draft_ticket_status": latest_draft.get("status", "missing"),
        "instruction_packet_ticket_draft_recommended": (
            latest_packet.get("status") == "available"
            and latest_draft.get("status") != "available"
        ),
        "local_implementation_handoff_recommended": latest_draft.get("status") == "available",
        "draft_expected_files_backfill_recommended": bool(
            latest_draft_payload and draft_needs_expected_files_backfill(latest_draft_payload)
        ),
        "last_patch_revalidation": (
            latest_draft_payload.get("last_patch_revalidation")
            if latest_draft_payload
            else None
        ),
        "expected_files_backfilled_at": (
            latest_draft_payload.get("expected_files_backfilled_at")
            if latest_draft_payload
            else None
        ),
        "operator_commands": {
            "run_ticket_draft_latest": (
                f"python {DRAFT_CLI_SCRIPT} --latest"
            ),
            "run_ticket_draft_dry_run": (
                f"python {DRAFT_CLI_SCRIPT} --latest --dry-run"
            ),
            "backfill_expected_files_latest": (
                f"python {BACKFILL_CLI_SCRIPT} --latest"
            ),
        },
    }


def run_instruction_packet_ticket_draft_command(
    *,
    instruction_packet: Path | None = None,
    latest: bool = False,
    dry_run: bool = False,
    out_dir: Path | None = None,
    root: Path | None = None,
) -> tuple[dict[str, Any], int]:
    project_root = root or repo_root()
    discovery = discover_latest_instruction_packet(root=project_root)
    if instruction_packet is None:
        if not latest:
            return (
                {
                    "verdict": "NO-GO",
                    "status": "error",
                    "detail": "requires --instruction-packet PATH or --latest",
                },
                2,
            )
        if discovery.get("status") != "available":
            return (
                {
                    "verdict": "NO-GO",
                    "status": "error",
                    "detail": discovery.get("detail") or "no instruction packet found",
                },
                2,
            )
        instruction_packet = project_root / str(discovery["instruction_packet_path"])
    elif not instruction_packet.is_absolute():
        instruction_packet = project_root / instruction_packet

    rel_packet_path = _safe_rel(instruction_packet, project_root)
    parsed = parse_instruction_packet_text(
        instruction_packet.read_text(encoding="utf-8") if instruction_packet.is_file() else ""
    )
    validation = validate_instruction_packet_for_draft(
        packet_path=instruction_packet,
        parsed=parsed,
        root=project_root,
    )
    if not validation.get("passed"):
        payload = {
            "verdict": "NO-GO",
            "status": "rejected",
            "source_instruction_packet": rel_packet_path,
            "validation_reasons": validation.get("reasons") or [],
            "recommended_files": parsed.get("likely_files") or [],
            "acceptance_criteria_count": len(parsed.get("acceptance_criteria") or []),
            "tests_recommended": parsed.get("tests_recommended") or [],
            "safety_notes": parsed.get("safety_notes") or [],
            "non_goals": parsed.get("non_goals") or [],
        }
        write_draft_status_report(payload, root=project_root)
        return payload, 1

    draft_payload = build_draft_ticket_payload(
        parsed=parsed,
        instruction_packet_path=rel_packet_path,
        validation=validation,
        root=project_root,
    )
    draft_dir = out_dir or draft_ticket_dir(root=project_root)
    draft_dir.mkdir(parents=True, exist_ok=True)
    draft_path = draft_dir / _draft_ticket_name(str(parsed.get("packet_id") or "packet"))

    summary = {
        "verdict": "GO",
        "status": "completed" if not dry_run else "dry_run",
        "source_instruction_packet": rel_packet_path,
        "draft_ticket_path": _safe_rel(draft_path, project_root) if not dry_run else None,
        "recommended_files": draft_payload.get("expected_files") or [],
        "acceptance_criteria_count": len(draft_payload.get("acceptance_criteria") or []),
        "tests_recommended": draft_payload.get("test_plan") or [],
        "safety_notes": draft_payload.get("safety_notes") or [],
        "non_goals": draft_payload.get("non_goals") or [],
        "dry_run": dry_run,
    }

    if not dry_run:
        violations = assert_no_private_fields({"draft_ticket": draft_payload})
        if violations:
            reject = {
                **summary,
                "verdict": "NO-GO",
                "status": "rejected",
                "validation_reasons": violations[:5],
            }
            write_draft_status_report(reject, root=project_root)
            return reject, 1
        draft_path.write_text(json.dumps(draft_payload, indent=2) + "\n", encoding="utf-8")
        summary["draft_ticket_path"] = _safe_rel(draft_path, project_root)

    write_draft_status_report(summary, root=project_root)
    exit_code = 0 if summary["verdict"] == "GO" else 1
    return summary, exit_code


def public_safe_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a public-safe CLI JSON summary."""
    allowed = {
        "verdict",
        "status",
        "detail",
        "source_instruction_packet",
        "draft_ticket_path",
        "recommended_files",
        "acceptance_criteria_count",
        "tests_recommended",
        "safety_notes",
        "non_goals",
        "validation_reasons",
        "dry_run",
    }
    return {key: payload[key] for key in allowed if key in payload}


def backfill_safe_summary(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "verdict",
        "status",
        "detail",
        "draft_count",
        "updated_count",
        "results",
        "dry_run",
    }
    return {key: payload[key] for key in allowed if key in payload}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a governor GO instruction packet into a local implementation "
            "ticket draft under data/operator/draft_tickets/."
        ),
    )
    parser.add_argument(
        "--instruction-packet",
        type=Path,
        default=None,
        help="Explicit instruction packet markdown path.",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Use the newest instruction packet in data/operator/instruction_packets/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and summarize without writing a draft ticket file.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Override draft ticket output directory (defaults to data/operator/draft_tickets/).",
    )
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)

    payload, exit_code = run_instruction_packet_ticket_draft_command(
        instruction_packet=args.instruction_packet,
        latest=args.latest,
        dry_run=args.dry_run,
        out_dir=args.out_dir,
        root=args.root,
    )
    print(json.dumps(public_safe_summary(payload), indent=2))
    return exit_code


def backfill_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-infer expected_files on existing draft tickets without re-handoff.",
    )
    parser.add_argument("--draft-ticket", type=Path, default=None)
    parser.add_argument("--latest", action="store_true")
    parser.add_argument("--all", action="store_true", dest="all_drafts")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)

    payload, exit_code = run_draft_expected_files_backfill_command(
        draft_ticket=args.draft_ticket,
        latest=args.latest,
        all_drafts=args.all_drafts,
        dry_run=args.dry_run,
        root=args.root,
    )
    print(json.dumps(backfill_safe_summary(payload), indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
