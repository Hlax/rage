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


def _audit_data_exports(root: Path) -> tuple[list[str], list[str]]:
    """Validate scratch export JSON under data/exports/ when present."""
    exports_dir = root / "data" / "exports"
    checked: list[str] = []
    blocked: list[str] = []
    if not exports_dir.is_dir():
        return checked, blocked

    json_files = sorted(exports_dir.glob("*.json"))
    if not json_files:
        return checked, blocked

    for path in json_files:
        relative = str(path.relative_to(root))
        checked.append(relative)
        payload = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(payload):
                blocked.append(
                    f"secret-like content in {relative} matching {pattern.pattern!r}"
                )

    cards_path = exports_dir / "public_cards.json"
    memos_path = exports_dir / "public_memos.json"
    build_path = exports_dir / "build_info.json"
    if cards_path.is_file() and memos_path.is_file() and build_path.is_file():
        cards = json.loads(cards_path.read_text(encoding="utf-8"))
        memos = json.loads(memos_path.read_text(encoding="utf-8"))
        build_info = json.loads(build_path.read_text(encoding="utf-8"))
        for issue in validate_public_export_bundle(cards, memos, build_info):
            blocked.append(f"data/exports bundle: {issue}")

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
    exporter = root / "rge" / "modules" / "card_exporter.py"
    if exporter.is_file():
        source = exporter.read_text(encoding="utf-8")
        if "resolve_export_targets" not in source or "publish_public" not in source:
            blocked.append("missing publish_public export guard in card_exporter.py")
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
            "ci_golden_gate_policy",
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
        elif check == "ci_golden_gate_policy":
            files, blocked = _audit_ci_golden_gate_policy(project_root)
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
