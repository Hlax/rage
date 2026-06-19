"""Operator-private canonical evidence card export and atlas-safe previews."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rge.contracts.evidence_atom_v0 import EvidenceCard_v0_1, validate_evidence_card
from rge.modules.card_exporter import canonical_json_dumps
from rge.modules.evidence_atoms import build_evidence_card_for_claim
from rge.safety.public_export_policy import FORBIDDEN_KEY_SUBSTRINGS

EVIDENCE_CARDS_PREVIEW_SCHEMA_VERSION = "evidence_cards_preview_v0.1.0"
EXPORT_SCHEMA_VERSION = "evidence_card_export_v0.1.0"
MAX_PREVIEW_SUMMARY_CHARS = 240
MAX_PREVIEW_SCOPE_CHARS = 120
MAX_PREVIEW_TITLE_CHARS = 160


def derive_atlas_safe_evidence_preview(
    card: EvidenceCard_v0_1 | dict[str, Any],
) -> dict[str, Any]:
    """Derive a frontend-safe preview without quotes, IDs, or private paths."""
    data = card if isinstance(card, dict) else card.model_dump(mode="json")
    claim = str(data.get("claim") or "")
    if len(claim) > MAX_PREVIEW_SUMMARY_CHARS:
        summary = claim[: MAX_PREVIEW_SUMMARY_CHARS - 3].rstrip() + "..."
    else:
        summary = claim
    source = data.get("source") or {}
    title = str(source.get("title") or "")
    if len(title) > MAX_PREVIEW_TITLE_CHARS:
        title = title[: MAX_PREVIEW_TITLE_CHARS - 3].rstrip() + "..."
    scope = str(data.get("scope") or "")
    if len(scope) > MAX_PREVIEW_SCOPE_CHARS:
        scope = scope[: MAX_PREVIEW_SCOPE_CHARS - 3].rstrip() + "..."
    return {
        "card_type": data.get("card_type", "evidence_claim"),
        "summary": summary,
        "source_type": source.get("source_type") or "unknown",
        "source_title": title,
        "evidence_type": data.get("evidence_type"),
        "stance": data.get("stance"),
        "evidence_maturity": data.get("evidence_maturity"),
        "asset_tags": list(data.get("asset_tags") or []),
        "confidence": data.get("confidence"),
        "concepts": list(data.get("concepts") or [])[:8],
        "scope": scope,
        "limitations_count": len(data.get("limitations") or []),
    }


def assert_atlas_safe_preview_bundle(previews: list[dict[str, Any]]) -> list[str]:
    """Return violations when atlas-safe previews contain forbidden key fragments."""
    violations: list[str] = []

    def _walk(value: object, prefix: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                key_path = f"{prefix}.{key}" if prefix else str(key)
                leaf = str(key).casefold()
                if any(fragment in leaf for fragment in FORBIDDEN_KEY_SUBSTRINGS):
                    violations.append(f"forbidden preview key: {key_path}")
                _walk(item, key_path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                _walk(item, f"{prefix}[{index}]")

    for index, preview in enumerate(previews):
        _walk(preview, f"atlas_safe_previews[{index}]")
    return violations


def audit_atlas_evidence_cards_preview(previews: list[dict[str, Any]]) -> list[str]:
    """Return violations when atlas evidence card previews leak private fields."""
    violations = assert_atlas_safe_preview_bundle(previews)
    for index, preview in enumerate(previews):
        if "quote" in preview:
            violations.append(f"evidence_cards_preview[{index}] contains quote")
        if "claim" in preview:
            violations.append(f"evidence_cards_preview[{index}] contains claim")
    return violations


def audit_snapshot_evidence_cards_preview(snapshot: dict[str, Any]) -> list[str]:
    """Audit evidence_cards_preview embedded in an atlas snapshot dict."""
    previews = snapshot.get("evidence_cards_preview")
    if previews is None:
        return []
    if not isinstance(previews, list):
        return ["evidence_cards_preview must be a list"]
    return audit_atlas_evidence_cards_preview(previews)


def build_atlas_evidence_cards_preview(
    conn: sqlite3.Connection,
    *,
    domain_pack: str,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Project public-safe evidence card previews for atlas snapshot embedding."""
    cards = list_top_evidence_cards(conn, domain=domain_pack, limit=limit)
    previews = [derive_atlas_safe_evidence_preview(card) for card in cards]
    violations = audit_atlas_evidence_cards_preview(previews)
    if violations:
        raise ValueError(
            "Atlas evidence card preview projection blocked: "
            + "; ".join(violations[:5])
        )
    return previews


def list_top_evidence_cards(
    conn: sqlite3.Connection,
    *,
    claim_ids: list[str] | None = None,
    domain: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Build canonical evidence cards for the top quote-backed accepted claims."""
    if claim_ids:
        candidate_ids = list(claim_ids)
    elif domain:
        rows = conn.execute(
            """
            SELECT id
            FROM claims
            WHERE domain = ? AND status = 'accepted'
            ORDER BY id ASC
            LIMIT ?
            """,
            (domain, max(limit * 3, limit)),
        ).fetchall()
        candidate_ids = [str(row["id"]) for row in rows]
    else:
        raise ValueError("list_top_evidence_cards requires claim_ids or domain")

    cards: list[dict[str, Any]] = []
    for claim_id in candidate_ids:
        try:
            card = build_evidence_card_for_claim(conn, claim_id)
            cards.append(card.model_dump(mode="json"))
        except ValueError:
            continue
        if len(cards) >= limit:
            break
    return cards


def export_evidence_cards(
    conn: sqlite3.Connection,
    *,
    domain: str,
    output_dir: Path,
    limit: int = 100,
    include_atlas_preview: bool = True,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Export operator-private evidence cards and optional atlas-safe previews."""
    rows = conn.execute(
        """
        SELECT id
        FROM claims
        WHERE domain = ? AND status = 'accepted'
        ORDER BY created_at
        LIMIT ?
        """,
        (domain, limit),
    ).fetchall()

    cards: list[dict[str, Any]] = []
    previews: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for row in rows:
        claim_id = str(row["id"])
        try:
            card = build_evidence_card_for_claim(conn, claim_id)
            payload = card.model_dump(mode="json")
            validate_evidence_card(payload)
            cards.append(payload)
            if include_atlas_preview:
                previews.append(derive_atlas_safe_evidence_preview(payload))
        except ValueError as exc:
            skipped.append({"claim_id": claim_id, "reason": str(exc)})

    if include_atlas_preview:
        violations = assert_atlas_safe_preview_bundle(previews)
        if violations:
            raise ValueError(
                "Atlas-safe evidence previews failed private-field scan: "
                + "; ".join(violations[:5])
            )
        violations = audit_atlas_evidence_cards_preview(previews)
        if violations:
            raise ValueError(
                "Atlas-safe evidence previews failed evidence audit: "
                + "; ".join(violations[:5])
            )

    timestamp = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bundle: dict[str, Any] = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "command": "export-evidence-cards",
        "domain": domain,
        "generated_at": timestamp,
        "card_count": len(cards),
        "skipped_count": len(skipped),
        "evidence_cards": cards,
        "skipped": skipped,
    }
    if include_atlas_preview:
        bundle["atlas_safe_previews"] = previews
        bundle["atlas_preview_count"] = len(previews)

    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / "evidence_cards.json"
    bundle_path.write_text(canonical_json_dumps(bundle), encoding="utf-8")
    latest_path = output_dir / "evidence_cards_latest.json"
    latest_path.write_text(canonical_json_dumps(bundle), encoding="utf-8")

    return {
        "status": "success",
        "command": "export-evidence-cards",
        "domain": domain,
        "card_count": len(cards),
        "skipped_count": len(skipped),
        "include_atlas_preview": include_atlas_preview,
        "written_files": [str(bundle_path), str(latest_path)],
        "generated_at": timestamp,
    }
