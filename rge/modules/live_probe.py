"""Safe local live structured-task probes (report-only, no default DB writes).

Operators use these helpers to prove Ollama/Qwen claim extraction outside CI
without persisting to the default SQLite database or public exports.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rge.config import RgeConfig, load_config
from rge.db.connection import DEFAULT_DB_PATH
from rge.llm.mode import effective_llm_mode, live_llm_enabled
from rge.llm.ollama_client import OllamaStructuredCallError
from rge.llm.registry import get_model_client
from rge.modules.claim_extractor import extract_and_validate_for_chunk
from rge.modules.claim_validator import rejection_diagnostic

DEFAULT_PROBE_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "sources"
    / "live_probe_claim_calibration_short.txt"
)
LEGACY_PROBE_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "sources"
    / "creativity_ai_diversity_short.txt"
)
DEFAULT_PROBE_DOMAIN = "creativity"
PROBE_CHUNK_ID = "chunk_live_probe_001"
PROBE_SOURCE_ID = "src_live_probe_001"


class LiveProbeError(Exception):
    """Probe execution failed (structured call, validation, I/O)."""


class LiveProbeGateError(LiveProbeError):
    """Live opt-in or Ollama health gate failed."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def live_probes_dir(root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    return base / "data" / "reports" / "live_probes"


def resolve_fixture_source(path: Path | None, root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    fixture = path if path is not None else DEFAULT_PROBE_FIXTURE
    if not fixture.is_absolute():
        fixture = base / fixture
    return fixture.resolve()


def assert_live_probe_env(config: RgeConfig | None = None) -> RgeConfig:
    cfg = config if config is not None else load_config()
    if cfg.llm_mode != "ollama":
        raise LiveProbeGateError(
            "probe-extract-claims requires RGE_LLM_MODE=ollama "
            f"(got {cfg.llm_mode!r})."
        )
    if not live_llm_enabled(cfg):
        raise LiveProbeGateError(
            "probe-extract-claims requires RGE_ALLOW_LIVE_LLM=1 with "
            "RGE_LLM_MODE=ollama. Live probes are opt-in only."
        )
    if effective_llm_mode(cfg) != "ollama":
        raise LiveProbeGateError(
            "effective_llm_mode is not ollama; check RGE_LLM_MODE and "
            "RGE_ALLOW_LIVE_LLM."
        )
    return cfg


def assert_ollama_health(config: RgeConfig) -> dict[str, Any]:
    client = get_model_client(config, mode="ollama")
    health = client.health_check()
    if not health.get("reachable"):
        hint = health.get("action_hint") or "Ollama is not reachable."
        raise LiveProbeGateError(hint)
    if not health.get("model_available"):
        hint = health.get("action_hint") or (
            f"Configured model {health.get('model')!r} is not available locally."
        )
        raise LiveProbeGateError(hint)
    return health


def run_probe_extract_claims(
    *,
    fixture_source: Path | None = None,
    domain_pack: str = DEFAULT_PROBE_DOMAIN,
    root: Path | None = None,
    reports_dir: Path | None = None,
    config: RgeConfig | None = None,
    client: Any | None = None,
    skip_health_check: bool = False,
) -> dict[str, Any]:
    """Run live claim extraction on a fixture chunk; write report only (no DB)."""
    base = root if root is not None else repo_root()
    cfg = assert_live_probe_env(config)
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    fixture_path = resolve_fixture_source(fixture_source, base)
    if not fixture_path.is_file():
        raise LiveProbeError(f"fixture source not found: {fixture_path}")

    chunk_text = fixture_path.read_text(encoding="utf-8")
    chunk = {
        "id": PROBE_CHUNK_ID,
        "source_id": PROBE_SOURCE_ID,
        "chunk_index": 0,
        "chunk_text": chunk_text,
    }

    model_client = client or get_model_client(cfg, mode="ollama")
    try:
        validation = extract_and_validate_for_chunk(
            chunk,
            domain_pack=domain_pack,
            client=model_client,
        )
    except OllamaStructuredCallError as exc:
        raise LiveProbeError(str(exc)) from exc

    accepted = validation["accepted"]
    rejected = validation["rejected"]
    for item in rejected:
        item["validation_diagnostic"] = rejection_diagnostic(
            item,
            chunk_text=chunk_text,
            rejection_reason=item.get("rejection_reason"),
        )
    total = len(accepted) + len(rejected)
    if total == 0:
        raise LiveProbeError(
            "Live probe received no parseable claim candidates from the model."
        )

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    report: dict[str, Any] = {
        "report_type": "live_probe_report",
        "command": "probe-extract-claims",
        "status": "ok",
        "probe": "claim_extraction",
        "created_at": created_at,
        "fixture_source": str(fixture_path.relative_to(base)).replace("\\", "/"),
        "chunk_id": PROBE_CHUNK_ID,
        "source_id": PROBE_SOURCE_ID,
        "domain_pack": domain_pack,
        "effective_llm_mode": effective_llm_mode(cfg),
        "provider": model_client.provider,
        "model": getattr(model_client, "model", None),
        "base_url": getattr(model_client, "base_url", None),
        "schema_version": cfg.llm_schema_version,
        "health": health,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
        "db_writes": False,
        "default_db_path": str(DEFAULT_DB_PATH).replace("\\", "/"),
    }

    out_dir = reports_dir if reports_dir is not None else live_probes_dir(base)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    report_path = out_dir / f"probe_extract_claims_{stamp}.json"
    try:
        rel_path = report_path.relative_to(base)
        report["report_path"] = str(rel_path).replace("\\", "/")
    except ValueError:
        report["report_path"] = str(report_path).replace("\\", "/")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def default_db_path(root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    return (base / DEFAULT_DB_PATH).resolve()
