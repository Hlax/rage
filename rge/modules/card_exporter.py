"""Create public-safe card JSON. Deterministic; no model use.

Selects accepted/public-safe records, strips everything not in the curated
public field list (``docs/agents/10_SAFETY_MODEL.md`` section 7), and fails
closed: one unsafe record blocks the whole export.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.db.repositories import (
    PublicCardRepository,
    public_card_record_to_export_dict,
    utc_now_iso,
)
from rge.safety.public_export_policy import (
    curated_public_card,
    validate_public_export_bundle,
)

EXPORT_SCHEMA_VERSION = "0.1.0"
FIXTURE_EXPORT_TIMESTAMP = "2026-06-12T00:00:00Z"
GOLDEN_FIXTURE_SOURCE_COUNT = 3
CARD_GOLDEN_DIVERSITY_ID = "card_golden_diversity_001"
CARD_GOLDEN_ORIGINALITY_ID = "card_golden_originality_002"

GOLDEN_CARD_EXTRAS: dict[str, dict[str, Any]] = {
    CARD_GOLDEN_DIVERSITY_ID: {
        "public_caveats": [
            "Evidence is from short-form creative writing fixtures.",
        ],
        "public_source_metadata": [
            {
                "title": "Creativity AI diversity (fixture)",
                "year": 2026,
                "source_type": "fixture",
            }
        ],
        "related_cards": [CARD_GOLDEN_ORIGINALITY_ID],
        "evidence_type": "empirical",
        "public_run_timestamp": "2026-06-12T00:00:00Z",
    },
    CARD_GOLDEN_ORIGINALITY_ID: {
        "public_caveats": [
            "Fixture-derived synthesis; not a live literature review.",
        ],
        "public_source_metadata": [
            {
                "title": "Creativity AI diversity (fixture)",
                "year": 2026,
                "source_type": "fixture",
            }
        ],
        "related_cards": [CARD_GOLDEN_DIVERSITY_ID],
        "evidence_type": "empirical",
        "public_run_timestamp": "2026-06-12T00:00:00Z",
    },
}

GOLDEN_PRIVATE_FIELDS: dict[str, Any] = {
    "evaluator_notes": "INTERNAL: hidden evaluator notes must never export.",
    "local_path": "C:\\Users\\private\\research_notes.txt",
    "prompt_template": "Extract claims from the following untrusted source text.",
    "raw_source_excerpt": "Full private source text must not appear in export.",
}

EXPORT_CARD_FIELD_ORDER: tuple[str, ...] = (
    "id",
    "type",
    "title",
    "summary",
    "confidence",
    "concepts",
    "source_count",
    "public_caveats",
    "public_source_metadata",
    "related_cards",
    "public_detail_level",
    "evidence_type",
    "public_run_timestamp",
    "updated_at",
)

BUILD_INFO_FIELD_ORDER: tuple[str, ...] = (
    "export_schema_version",
    "generated_at",
    "phase",
    "card_count",
    "memo_count",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_export_dirs(repo_root: Path | None = None) -> list[Path]:
    root = repo_root or _repo_root()
    return [
        root / "data" / "exports",
        root / "apps" / "public-site" / "public" / "data",
    ]


def public_site_export_dir(repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root()
    return root / "apps" / "public-site" / "public" / "data"


def resolve_export_targets(
    *,
    output_dirs: list[Path] | None,
    repo_root: Path | None = None,
    fixture_mode: bool = False,
    publish_public: bool = False,
) -> list[Path]:
    """Resolve export directories with live-mode public-site publish guard."""
    root = repo_root or _repo_root()
    if output_dirs is not None:
        targets = list(output_dirs)
    elif fixture_mode or publish_public:
        targets = default_export_dirs(root)
    else:
        from rge.config import load_config
        from rge.llm.mode import live_llm_enabled

        targets = [root / "data" / "exports"]
        if not live_llm_enabled(load_config()):
            targets.append(public_site_export_dir(root))

    _assert_export_targets_allowed(
        targets,
        repo_root=root,
        fixture_mode=fixture_mode,
        publish_public=publish_public,
    )
    return targets


def _assert_export_targets_allowed(
    targets: list[Path],
    *,
    repo_root: Path,
    fixture_mode: bool,
    publish_public: bool,
) -> None:
    if fixture_mode or publish_public:
        return
    from rge.config import load_config
    from rge.llm.mode import live_llm_enabled

    if not live_llm_enabled(load_config()):
        return

    public_site = public_site_export_dir(repo_root).resolve()
    for target in targets:
        resolved = target.resolve()
        if resolved == public_site or public_site in resolved.parents:
            raise ValueError(
                "Live-mode export to apps/public-site/public/data/ requires --publish. "
                "Use data/exports/ for scratch exports."
            )


def default_ticket_output_dir(repo_root: Path | None = None) -> Path:
    """Gitignored runtime directory for generated improvement ticket artifacts."""
    return (repo_root or _repo_root()) / "data" / "tickets"


def order_public_card_fields(card: dict[str, Any]) -> dict[str, Any]:
    """Return a public card dict with stable field ordering for export."""
    return {key: card[key] for key in EXPORT_CARD_FIELD_ORDER if key in card}


def order_build_info_fields(build_info: dict[str, Any]) -> dict[str, Any]:
    """Return build_info with stable field ordering for export."""
    return {key: build_info[key] for key in BUILD_INFO_FIELD_ORDER if key in build_info}


def canonical_json_dumps(payload: Any) -> str:
    """Serialize JSON with stable key order and trailing newline."""
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _dominant_evidence_type(conn: Any, claim_ids: list[str]) -> str | None:
    """Return the most common evidence type among linked accepted claims."""
    if not claim_ids:
        return None
    placeholders = ",".join("?" * len(claim_ids))
    rows = conn.execute(
        f"""
        SELECT evidence_type FROM claims
        WHERE id IN ({placeholders}) AND status = 'accepted'
        """,
        claim_ids,
    ).fetchall()
    types = [row[0] for row in rows if row[0]]
    if not types:
        return None
    return max(set(types), key=types.count)


def _accepted_claim_count(conn: Any) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM claims WHERE status = 'accepted'"
    ).fetchone()
    return int(row[0]) if row else 0


def ensure_golden_public_cards(conn: Any) -> list[str]:
    """Seed deterministic golden cards when the graph has accepted claims."""
    repo = PublicCardRepository(conn)
    if repo.count_public_safe() > 0:
        return []

    if _accepted_claim_count(conn) == 0:
        return []

    claim_rows = conn.execute(
        "SELECT id, source_id FROM claims WHERE status = 'accepted' ORDER BY id"
    ).fetchall()
    claim_ids = [row["id"] for row in claim_rows[:3]]
    source_count = len({row["source_id"] for row in claim_rows})

    seeded: list[str] = []
    cards = (
        {
            "card_id": CARD_GOLDEN_DIVERSITY_ID,
            "card_type": "cluster_card",
            "title": "AI assistance and semantic diversity",
            "summary": (
                "Fixture evidence suggests AI-assisted brainstorming may improve "
                "average idea quality while reducing semantic diversity in some "
                "short-form writing tasks."
            ),
            "confidence": "medium",
            "concepts": ["AI assistance", "semantic diversity", "ideation"],
        },
        {
            "card_id": CARD_GOLDEN_ORIGINALITY_ID,
            "card_type": "cluster_card",
            "title": "AI assistance and creative originality",
            "summary": (
                "Accepted fixture claims indicate AI assistance can raise output "
                "volume while leaving open whether originality gains persist "
                "outside controlled ideation tasks."
            ),
            "confidence": "medium",
            "concepts": ["AI assistance", "originality", "human control"],
        },
    )

    for card in cards:
        repo.insert(
            card_id=card["card_id"],
            card_type=card["card_type"],
            title=card["title"],
            summary=card["summary"],
            confidence=card["confidence"],
            concepts=card["concepts"],
            source_count=source_count,
            claim_ids=claim_ids,
            public_detail_level="standard",
            is_public_safe=True,
            private_fields=GOLDEN_PRIVATE_FIELDS,
        )
        seeded.append(card["card_id"])

    return seeded


def export_public_cards(
    conn: Any,
    *,
    limit: int = 100,
    output_dirs: list[Path] | None = None,
    repo_root: Path | None = None,
    fixture_mode: bool = False,
    export_timestamp: str | None = None,
    publish_public: bool = False,
) -> dict[str, Any]:
    """Export public-safe cards as JSON files after validation."""
    seeded_ids = ensure_golden_public_cards(conn)
    repo = PublicCardRepository(conn)
    records = repo.list_public_safe(limit=limit)

    cards = []
    for record in records:
        extras = dict(GOLDEN_CARD_EXTRAS.get(record.id) or {})
        claim_ids = json.loads(record.claim_ids_json or "[]")
        if "evidence_type" not in extras:
            evidence_type = _dominant_evidence_type(conn, claim_ids)
            if evidence_type:
                extras["evidence_type"] = evidence_type
        if "public_run_timestamp" not in extras:
            extras["public_run_timestamp"] = record.created_at
        card = curated_public_card(
            public_card_record_to_export_dict(record, extras=extras)
        )
        if fixture_mode:
            card["source_count"] = GOLDEN_FIXTURE_SOURCE_COUNT
            stable_ts = export_timestamp or FIXTURE_EXPORT_TIMESTAMP
            card["updated_at"] = stable_ts
            if "public_run_timestamp" not in extras:
                card["public_run_timestamp"] = stable_ts
        cards.append(order_public_card_fields(card))

    cards.sort(key=lambda item: item["id"])
    memos: list[dict[str, Any]] = []
    generated_at = export_timestamp if fixture_mode else utc_now_iso()
    if fixture_mode and export_timestamp is None:
        generated_at = FIXTURE_EXPORT_TIMESTAMP
    build_info = order_build_info_fields(
        {
            "export_schema_version": EXPORT_SCHEMA_VERSION,
            "generated_at": generated_at,
            "phase": "1",
            "card_count": len(cards),
            "memo_count": len(memos),
        }
    )

    violations = validate_public_export_bundle(cards, memos, build_info)
    if violations:
        raise ValueError(
            "Public export blocked by safety policy: "
            + "; ".join(violations[:5])
            + (f"; and {len(violations) - 5} more" if len(violations) > 5 else "")
        )

    targets = resolve_export_targets(
        output_dirs=output_dirs,
        repo_root=repo_root,
        fixture_mode=fixture_mode,
        publish_public=publish_public,
    )
    written_files: list[str] = []
    payloads = {
        "public_cards.json": cards,
        "public_memos.json": memos,
        "build_info.json": build_info,
    }
    for directory in targets:
        directory.mkdir(parents=True, exist_ok=True)
        for filename, payload in payloads.items():
            path = directory / filename
            path.write_text(canonical_json_dumps(payload), encoding="utf-8")
            written_files.append(str(path))

    return {
        "status": "success",
        "command": "export-public",
        "card_count": len(cards),
        "memo_count": len(memos),
        "seeded_card_ids": seeded_ids,
        "written_files": written_files,
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "fixture_mode": fixture_mode,
        "publish_public": publish_public,
    }
