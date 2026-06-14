"""Run deterministic safety checks. Deterministic; no model use.

Audit types (10_SAFETY_MODEL.md section 13): prompt_injection, public_export,
route_permissions, secrets, raw_html, model_tool_permissions, full. Deterministic
checks decide pass/fail; model commentary never does.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rge.safety.public_export_policy import (
    FORBIDDEN_VALUE_PATTERNS,
    validate_public_export_bundle,
)
from rge.safety.route_audit import ALLOWED_PUBLIC_ROUTES, FORBIDDEN_PUBLIC_ROUTE_KINDS

AUDIT_TYPES = (
    "prompt_injection",
    "public_export",
    "route_permissions",
    "secrets",
    "raw_html",
    "model_tool_permissions",
    "full",
)

_PASS_EXIT_CODE = 0
_FAIL_EXIT_CODE = 1

_FORBIDDEN_ROUTE_SOURCE_PATTERNS = (
    re.compile(r"export\s+async\s+function\s+(POST|PUT|PATCH|DELETE)\b"),
    re.compile(r"export\s+function\s+(POST|PUT|PATCH|DELETE)\b"),
    re.compile(r"method\s*:\s*['\"](POST|PUT|PATCH|DELETE)['\"]"),
    re.compile(r"/(?:ingest|agent|local/runs|local/sources|local/queue)", re.IGNORECASE),
    re.compile(r"127\.0\.0\.1:\d+"),
    re.compile(r"localhost:\d+/local"),
)

_FORBIDDEN_MODEL_TOOL_PATTERNS = (
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bos\.system\b"),
    re.compile(r"\bPopen\b"),
    re.compile(r"shell\s*=\s*True"),
    re.compile(r"git\s+push", re.IGNORECASE),
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def scan_public_site_source_for_violations(
    source_text: str, relative_path: str
) -> list[str]:
    """Return route/raw-html violations for a single public-site source file."""
    violations: list[str] = []
    if "dangerouslySetInnerHTML" in source_text:
        violations.append(f"unsafe raw HTML rendering in {relative_path}")
    for pattern in _FORBIDDEN_ROUTE_SOURCE_PATTERNS:
        if pattern.search(source_text):
            violations.append(
                f"forbidden public route pattern in {relative_path}: {pattern.pattern}"
            )
    return violations


def scan_model_module_for_violations(
    source_text: str, relative_path: str
) -> list[str]:
    """Return model-tool permission violations for an LLM runtime module."""
    violations: list[str] = []
    for pattern in _FORBIDDEN_MODEL_TOOL_PATTERNS:
        if pattern.search(source_text):
            violations.append(
                f"forbidden model tool pattern in {relative_path}: {pattern.pattern}"
            )
    return violations


def _iter_public_site_sources(root: Path) -> list[tuple[Path, str]]:
    public_site = root / "apps" / "public-site"
    if not public_site.is_dir():
        return []

    scan_roots: list[Path] = [
        public_site / "app",
        public_site / "lib",
        public_site / "next.config.js",
    ]
    files: list[tuple[Path, str]] = []
    for scan_root in scan_roots:
        if scan_root.is_file():
            files.append((scan_root, str(scan_root.relative_to(root))))
            continue
        if not scan_root.is_dir():
            continue
        for path in scan_root.rglob("*"):
            if path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
                continue
            if any(part in {"node_modules", "out", ".next"} for part in path.parts):
                continue
            files.append((path, str(path.relative_to(root))))
    return files


def _audit_route_permissions(root: Path) -> tuple[list[str], list[str]]:
    checked: list[str] = list(ALLOWED_PUBLIC_ROUTES)
    blocked: list[str] = []
    for path, relative_path in _iter_public_site_sources(root):
        checked.append(relative_path)
        source_text = path.read_text(encoding="utf-8")
        blocked.extend(scan_public_site_source_for_violations(source_text, relative_path))
    if not _iter_public_site_sources(root):
        blocked.append("public site directory missing for route audit")
    return checked, blocked


def _audit_raw_html(root: Path) -> tuple[list[str], list[str]]:
    checked: list[str] = []
    blocked: list[str] = []
    for path, relative_path in _iter_public_site_sources(root):
        checked.append(relative_path)
        source_text = path.read_text(encoding="utf-8")
        if "dangerouslySetInnerHTML" in source_text:
            blocked.append(f"unsafe raw HTML rendering in {relative_path}")
    return checked, blocked


def _load_public_export_bundle(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    data_dir = root / "apps" / "public-site" / "public" / "data"
    cards_path = data_dir / "public_cards.json"
    memos_path = data_dir / "public_memos.json"
    build_path = data_dir / "build_info.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8")) if cards_path.is_file() else []
    memos = json.loads(memos_path.read_text(encoding="utf-8")) if memos_path.is_file() else []
    build_info = (
        json.loads(build_path.read_text(encoding="utf-8")) if build_path.is_file() else {}
    )
    return cards, memos, build_info


def _audit_public_export(root: Path) -> tuple[list[str], list[str]]:
    data_dir = root / "apps" / "public-site" / "public" / "data"
    checked: list[str] = []
    blocked: list[str] = []
    for name in ("public_cards.json", "public_memos.json", "build_info.json"):
        path = data_dir / name
        if path.is_file():
            checked.append(str(path.relative_to(root)))
        else:
            blocked.append(f"missing public export file: {path.relative_to(root)}")

    if blocked:
        return checked, blocked

    cards, memos, build_info = _load_public_export_bundle(root)
    blocked.extend(validate_public_export_bundle(cards, memos, build_info))
    scratch_checked, scratch_blocked = _audit_data_exports(root)
    checked.extend(scratch_checked)
    blocked.extend(scratch_blocked)
    return checked, blocked


def _audit_export_json_file(
    path: Path, root: Path, *, label: str
) -> tuple[list[str], list[str]]:
    checked: list[str] = []
    blocked: list[str] = []
    relative = str(path.relative_to(root))
    checked.append(relative)
    payload = path.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_VALUE_PATTERNS:
        if pattern.search(payload):
            blocked.append(
                f"secret-like content in {label} matching {pattern.pattern!r}"
            )
    return checked, blocked


def _audit_export_bundle_triplet(
    bundle_dir: Path, root: Path, *, label: str
) -> tuple[list[str], list[str]]:
    checked: list[str] = []
    blocked: list[str] = []
    cards_path = bundle_dir / "public_cards.json"
    memos_path = bundle_dir / "public_memos.json"
    build_path = bundle_dir / "build_info.json"
    if not (
        cards_path.is_file() and memos_path.is_file() and build_path.is_file()
    ):
        return checked, blocked

    for path in (cards_path, memos_path, build_path):
        file_checked, file_blocked = _audit_export_json_file(
            path, root, label=label
        )
        checked.extend(file_checked)
        blocked.extend(file_blocked)

    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    memos = json.loads(memos_path.read_text(encoding="utf-8"))
    build_info = json.loads(build_path.read_text(encoding="utf-8"))
    for issue in validate_public_export_bundle(cards, memos, build_info):
        blocked.append(f"{label}: {issue}")
    return checked, blocked


def _audit_data_exports(root: Path) -> tuple[list[str], list[str]]:
    """Validate scratch export JSON under data/exports/ when present."""
    exports_dir = root / "data" / "exports"
    checked: list[str] = []
    blocked: list[str] = []
    if not exports_dir.is_dir():
        return checked, blocked

    manifest_name = "snapshot_manifest.json"
    for path in sorted(exports_dir.glob("*.json")):
        if path.name == manifest_name:
            file_checked, file_blocked = _audit_export_json_file(
                path, root, label=str(path.relative_to(root))
            )
            checked.extend(file_checked)
            blocked.extend(file_blocked)
            continue
        file_checked, file_blocked = _audit_export_json_file(
            path, root, label=str(path.relative_to(root))
        )
        checked.extend(file_checked)
        blocked.extend(file_blocked)

    bundle_checked, bundle_blocked = _audit_export_bundle_triplet(
        exports_dir, root, label="data/exports bundle"
    )
    checked.extend(bundle_checked)
    blocked.extend(bundle_blocked)

    history_dir = exports_dir / "history"
    if history_dir.is_dir():
        for bundle_dir in sorted(history_dir.iterdir()):
            if not bundle_dir.is_dir():
                continue
            hist_checked, hist_blocked = _audit_export_bundle_triplet(
                bundle_dir,
                root,
                label=f"data/exports/history/{bundle_dir.name} bundle",
            )
            checked.extend(hist_checked)
            blocked.extend(hist_blocked)

    return checked, blocked


def _audit_secrets(root: Path) -> tuple[list[str], list[str]]:
    data_dir = root / "apps" / "public-site" / "public" / "data"
    checked: list[str] = []
    blocked: list[str] = []
    for name in ("public_cards.json", "public_memos.json", "build_info.json"):
        path = data_dir / name
        if not path.is_file():
            blocked.append(f"missing public export file for secrets audit: {name}")
            continue
        relative = str(path.relative_to(root))
        checked.append(relative)
        payload = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(payload):
                blocked.append(
                    f"secret-like content in {relative} matching {pattern.pattern!r}"
                )
    return checked, blocked


def _audit_model_tool_permissions(root: Path) -> tuple[list[str], list[str]]:
    llm_dir = root / "rge" / "llm"
    checked: list[str] = []
    blocked: list[str] = []
    if not llm_dir.is_dir():
        blocked.append("missing rge/llm directory for model tool audit")
        return checked, blocked
    for path in sorted(llm_dir.glob("*.py")):
        relative_path = str(path.relative_to(root))
        checked.append(relative_path)
        source_text = path.read_text(encoding="utf-8")
        blocked.extend(scan_model_module_for_violations(source_text, relative_path))
    return checked, blocked


def _audit_prompt_injection_policy(root: Path) -> tuple[list[str], list[str]]:
    """Verify prompt-injection policy and deterministic GT24 evidence exist."""
    checked = [
        "rge/safety/prompt_injection.py",
        "fixtures/sources/prompt_injection_creativity_short.txt",
        "fixtures/llm_outputs/claim_extraction_prompt_injection.json",
        "tests/golden/test_24_prompt_injection.py",
    ]
    blocked: list[str] = []
    for relative_path in checked:
        if not (root / relative_path).is_file():
            blocked.append(f"missing prompt injection protection evidence: {relative_path}")
    return checked, blocked


def _audit_public_site_debug_policy(root: Path) -> tuple[list[str], list[str]]:
    """Verify public-site debug detail policy and deterministic GT25 evidence exist."""
    checked = [
        "apps/public-site/app/cards/[id]/page.tsx",
        "apps/public-site/lib/publicCards.ts",
        "tests/golden/test_25_public_site_debug_details.py",
    ]
    blocked: list[str] = []
    for relative_path in checked:
        if not (root / relative_path).is_file():
            blocked.append(
                f"missing public site debug detail protection evidence: {relative_path}"
            )
    return checked, blocked


def _audit_full_mvp_run_policy(root: Path) -> tuple[list[str], list[str]]:
    """Verify fixture-mode full MVP run policy and deterministic GT26 evidence exist."""
    checked = [
        "rge/cli.py",
        "tests/golden/test_26_full_mvp_run.py",
    ]
    blocked: list[str] = []
    for relative_path in checked:
        if not (root / relative_path).is_file():
            blocked.append(
                f"missing full MVP fixture run protection evidence: {relative_path}"
            )
    cli_path = root / "rge" / "cli.py"
    if cli_path.is_file():
        source = cli_path.read_text(encoding="utf-8")
        if "execute_fixture_mode_run" not in source:
            blocked.append("missing execute_fixture_mode_run in rge/cli.py")
    return checked, blocked


def _audit_live_llm_policy(root: Path) -> tuple[list[str], list[str]]:
    """Verify live LLM opt-in helper and deterministic unit-test evidence exist."""
    checked = [
        "rge/llm/mode.py",
        "rge/config.py",
        "tests/unit/test_ollama_structured_tasks.py",
    ]
    blocked: list[str] = []
    for relative_path in checked:
        if not (root / relative_path).is_file():
            blocked.append(f"missing live LLM opt-in evidence: {relative_path}")
    config_path = root / "rge" / "config.py"
    if config_path.is_file():
        source = config_path.read_text(encoding="utf-8")
        if "allow_live_llm" not in source or "RGE_ALLOW_LIVE_LLM" not in source:
            blocked.append("missing RGE_ALLOW_LIVE_LLM in rge/config.py")
    return checked, blocked


def _audit_live_smoke_policy(root: Path) -> tuple[list[str], list[str]]:
    """Verify live smoke gating and model-health CLI evidence exist."""
    checked = [
        "tests/smoke/test_live_ollama_smoke.py",
        "pyproject.toml",
        "rge/cli.py",
    ]
    blocked: list[str] = []
    for relative_path in checked:
        if not (root / relative_path).is_file():
            blocked.append(f"missing live smoke gating evidence: {relative_path}")
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8")
        if "live_smoke" not in text or "not live_smoke" not in text:
            blocked.append("pyproject.toml missing live_smoke marker exclusion")
    cli_path = root / "rge" / "cli.py"
    if cli_path.is_file():
        source = cli_path.read_text(encoding="utf-8")
        if "model-health" not in source or "_cmd_model_health" not in source:
            blocked.append("missing model-health command in rge/cli.py")
        if "probe-extract-claims" not in source or "_cmd_probe_extract_claims" not in source:
            blocked.append("missing probe-extract-claims command in rge/cli.py")
    live_probe = root / "rge" / "modules" / "live_probe.py"
    if live_probe.is_file():
        checked.append("rge/modules/live_probe.py")
    else:
        blocked.append("missing live probe module: rge/modules/live_probe.py")
    exporter = root / "rge" / "modules" / "card_exporter.py"
    if exporter.is_file():
        source = exporter.read_text(encoding="utf-8")
        if "resolve_export_targets" not in source or "publish_public" not in source:
            blocked.append("missing publish_public export guard in card_exporter.py")
    return checked, blocked


def _audit_live_probe_scratch_policy(root: Path) -> tuple[list[str], list[str]]:
    """Verify isolated scratch persistence is explicit and not export-wired."""
    checked: list[str] = []
    blocked: list[str] = []
    module = root / "rge" / "modules" / "live_probe_scratch.py"
    if not module.is_file():
        blocked.append("missing live probe scratch module: rge/modules/live_probe_scratch.py")
        return checked, blocked
    checked.append("rge/modules/live_probe_scratch.py")
    source = module.read_text(encoding="utf-8")
    if "confirm_review" not in source:
        blocked.append("live_probe_scratch missing confirm_review gate")
    if "LIVE_PROBE_SCRATCH_DB_PATH" not in source:
        blocked.append("live_probe_scratch missing dedicated scratch DB path constant")
    if "card_exporter" in source:
        blocked.append("live_probe_scratch must not import card_exporter")

    exporter = root / "rge" / "modules" / "card_exporter.py"
    if exporter.is_file():
        exporter_source = exporter.read_text(encoding="utf-8")
        if "live_probe_scratch" in exporter_source:
            blocked.append("card_exporter must not reference live_probe_scratch")

    live_probe = root / "rge" / "modules" / "live_probe.py"
    if live_probe.is_file():
        live_probe_source = live_probe.read_text(encoding="utf-8")
        if "live_probe_scratch" in live_probe_source:
            blocked.append("live_probe must not auto-call scratch persistence")

    cli_path = root / "rge" / "cli.py"
    if cli_path.is_file():
        cli_source = cli_path.read_text(encoding="utf-8")
        if (
            "probe-persist-reviewed-report" not in cli_source
            or "_cmd_probe_persist_reviewed_report" not in cli_source
        ):
            blocked.append("missing probe-persist-reviewed-report command in rge/cli.py")
        if (
            "probe-scratch-summary" not in cli_source
            or "_cmd_probe_scratch_summary" not in cli_source
        ):
            blocked.append("missing probe-scratch-summary command in rge/cli.py")
        if (
            "probe-scratch-evidence-review" not in cli_source
            or "_cmd_probe_scratch_evidence_review" not in cli_source
        ):
            blocked.append("missing probe-scratch-evidence-review command in rge/cli.py")

    summary_module = root / "rge" / "modules" / "live_probe_scratch_summary.py"
    if summary_module.is_file():
        checked.append("rge/modules/live_probe_scratch_summary.py")
        summary_source = summary_module.read_text(encoding="utf-8")
        if "mode=ro" not in summary_source:
            blocked.append("live_probe_scratch_summary must open scratch DB read-only")
        if "ensure_scratch_database" in summary_source:
            blocked.append("live_probe_scratch_summary must not bootstrap scratch schema")
        if "card_exporter" in summary_source:
            blocked.append("live_probe_scratch_summary must not import card_exporter")
    else:
        blocked.append("missing live probe scratch summary module")

    evidence_module = root / "rge" / "modules" / "live_probe_evidence_review.py"
    if evidence_module.is_file():
        checked.append("rge/modules/live_probe_evidence_review.py")
        evidence_source = evidence_module.read_text(encoding="utf-8")
        if "build_scratch_summary" not in evidence_source:
            blocked.append(
                "live_probe_evidence_review must reuse build_scratch_summary"
            )
        if "automated_ticket_recommendations" not in evidence_source:
            blocked.append(
                "live_probe_evidence_review must declare no automated ticket recommendations"
            )
        if "card_exporter" in evidence_source:
            blocked.append("live_probe_evidence_review must not import card_exporter")
    else:
        blocked.append("missing live probe evidence review module")
    return checked, blocked


def _load_creativity_pack_for_audit(root: Path) -> Any:
    from rge.modules.domain_pack_loader import domain_pack_dir, load_domain_pack

    if domain_pack_dir("creativity", root=root).is_dir():
        return load_domain_pack("creativity", root=root)
    return load_domain_pack("creativity")


def _audit_domain_pack_safety_notes(root: Path) -> tuple[list[str], list[str]]:
    """Verify creativity domain pack safety_notes.yaml guidance is loaded and complete."""
    from rge.modules.domain_pack_loader import (
        domain_pack_dir,
        required_safety_note_themes_for_pack,
        verify_pack_identity_for_audit,
        verify_pack_safety_notes_for_audit,
    )

    checked: list[str] = []
    blocked: list[str] = []
    pack_dir = domain_pack_dir("creativity", root=root)
    if pack_dir.is_dir():
        notes_path = pack_dir / "safety_notes.yaml"
        if notes_path.is_file():
            checked.append(str(notes_path.relative_to(root)))
        else:
            blocked.append("missing domain pack file: domain_packs/creativity/safety_notes.yaml")
            return checked, blocked
    else:
        checked.append("domain_packs/creativity/safety_notes.yaml")

    pack = _load_creativity_pack_for_audit(root)
    required_themes = required_safety_note_themes_for_pack(pack.pack_id)
    minimum_count = 5 if pack.pack_id == "creativity" else 1
    for issue in verify_pack_identity_for_audit(pack):
        blocked.append(issue)
    for issue in verify_pack_safety_notes_for_audit(
        pack,
        required_substrings=required_themes,
        minimum_note_count=minimum_count,
    ):
        blocked.append(issue)
    return checked, blocked


def _audit_ci_golden_gate_policy(root: Path) -> tuple[list[str], list[str]]:
    """Verify CI golden gate workflow and principal audit command evidence."""
    checked = [
        ".github/workflows/golden-gate.yml",
        ".cursor/commands/rge-principal-audit.md",
        "rge/modules/principal_audit_gate.py",
    ]
    blocked: list[str] = []
    for relative_path in checked:
        if not (root / relative_path).is_file():
            blocked.append(f"missing CI golden gate evidence: {relative_path}")
    workflow = root / ".github" / "workflows" / "golden-gate.yml"
    if workflow.is_file():
        text = workflow.read_text(encoding="utf-8")
        required_fragments = (
            "RGE_LLM_MODE: mock",
            "pytest tests/golden",
            "rge.modules.safety_auditor",
            "npm run build",
        )
        for fragment in required_fragments:
            if fragment not in text:
                blocked.append(
                    f"golden-gate.yml missing required step fragment: {fragment}"
                )
    command_doc = root / ".cursor" / "commands" / "rge-principal-audit.md"
    if command_doc.is_file():
        text = command_doc.read_text(encoding="utf-8")
        if "principal_audit_gate" not in text or "overdue" not in text:
            blocked.append("rge-principal-audit.md missing checkpoint status guidance")
    return checked, blocked


def run_safety_audit(audit_type: str = "full", *, root: Path | None = None) -> dict[str, Any]:
    """Run deterministic safety checks and return a machine-readable report."""
    if audit_type not in AUDIT_TYPES:
        raise ValueError(f"unsupported audit_type: {audit_type}")

    project_root = root or repo_root()
    blocked_reasons: list[str] = []
    checked_routes: list[str] = []
    checked_exports: list[str] = []
    checked_secrets: list[str] = []
    checked_files: list[str] = []

    checks: list[str]
    if audit_type == "full":
        checks = [
            "route_permissions",
            "public_export",
            "secrets",
            "raw_html",
            "model_tool_permissions",
            "prompt_injection",
            "public_site_debug",
            "full_mvp_run",
            "live_llm_policy",
            "live_smoke_policy",
            "live_probe_scratch_policy",
            "ci_golden_gate_policy",
            "domain_pack_safety_notes",
        ]
    else:
        checks = [audit_type]

    for check in checks:
        if check == "route_permissions":
            routes, blocked = _audit_route_permissions(project_root)
            checked_routes.extend(routes)
            blocked_reasons.extend(blocked)
            checked_files.extend(routes)
        elif check == "public_export":
            exports, blocked = _audit_public_export(project_root)
            checked_exports.extend(exports)
            blocked_reasons.extend(blocked)
            checked_files.extend(exports)
        elif check == "secrets":
            secrets, blocked = _audit_secrets(project_root)
            checked_secrets.extend(secrets)
            blocked_reasons.extend(blocked)
            checked_files.extend(secrets)
        elif check == "raw_html":
            files, blocked = _audit_raw_html(project_root)
            checked_files.extend(files)
            blocked_reasons.extend(blocked)
        elif check == "model_tool_permissions":
            files, blocked = _audit_model_tool_permissions(project_root)
            checked_files.extend(files)
            blocked_reasons.extend(blocked)
        elif check == "prompt_injection":
            files, blocked = _audit_prompt_injection_policy(project_root)
            checked_files.extend(files)
            blocked_reasons.extend(blocked)
        elif check == "public_site_debug":
            files, blocked = _audit_public_site_debug_policy(project_root)
            checked_files.extend(files)
            blocked_reasons.extend(blocked)
        elif check == "full_mvp_run":
            files, blocked = _audit_full_mvp_run_policy(project_root)
            checked_files.extend(files)
            blocked_reasons.extend(blocked)
        elif check == "live_llm_policy":
            files, blocked = _audit_live_llm_policy(project_root)
            checked_files.extend(files)
            blocked_reasons.extend(blocked)
        elif check == "live_smoke_policy":
            files, blocked = _audit_live_smoke_policy(project_root)
            checked_files.extend(files)
            blocked_reasons.extend(blocked)
        elif check == "live_probe_scratch_policy":
            files, blocked = _audit_live_probe_scratch_policy(project_root)
            checked_files.extend(files)
            blocked_reasons.extend(blocked)
        elif check == "ci_golden_gate_policy":
            files, blocked = _audit_ci_golden_gate_policy(project_root)
            checked_files.extend(files)
            blocked_reasons.extend(blocked)
        elif check == "domain_pack_safety_notes":
            files, blocked = _audit_domain_pack_safety_notes(project_root)
            checked_files.extend(files)
            blocked_reasons.extend(blocked)

    if audit_type == "full":
        for kind in FORBIDDEN_PUBLIC_ROUTE_KINDS:
            checked_routes.append(f"policy:{kind}")

    status = "fail" if blocked_reasons else "pass"
    return {
        "report_type": "safety_audit_report",
        "audit_type": audit_type,
        "status": status,
        "blocked_reasons": blocked_reasons,
        "checked_routes": sorted(set(checked_routes)),
        "checked_exports": sorted(set(checked_exports)),
        "checked_secrets": sorted(set(checked_secrets)),
        "checked_files": sorted(set(checked_files)),
        "created_at": utc_now_iso(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m rge.modules.safety_auditor",
        description="Deterministic safety auditor.",
    )
    parser.add_argument("--audit", default="full", choices=AUDIT_TYPES)
    args = parser.parse_args(argv)

    report = run_safety_audit(args.audit)
    print(json.dumps(report, indent=2))
    return _FAIL_EXIT_CODE if report["status"] == "fail" else _PASS_EXIT_CODE


if __name__ == "__main__":
    sys.exit(main())
