"""``research`` CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rge import __version__

_NOT_IMPLEMENTED_EXIT_CODE = 2


def _not_implemented(command: str, phase_hint: str) -> int:
    payload = {
        "status": "not_implemented",
        "command": command,
        "phase": "0",
        "detail": f"'{command}' is a Phase 0 placeholder. {phase_hint}",
    }
    print(json.dumps(payload, indent=2))
    return _NOT_IMPLEMENTED_EXIT_CODE


def _cmd_run(args: argparse.Namespace) -> int:
    return _not_implemented(
        "run",
        "Fixture-mode research runs arrive with the Phase 3 local research MVP "
        f"(requested topic={args.topic!r}, domain={args.domain!r}, "
        f"fixture_mode={args.fixture_mode}).",
    )


def _cmd_export_public(args: argparse.Namespace) -> int:
    return _not_implemented(
        "export-public",
        "Public-safe card export arrives with Phase 4 "
        f"(requested limit={args.limit}).",
    )


def _cmd_verify(_args: argparse.Namespace) -> int:
    return _not_implemented(
        "verify",
        "Deterministic verification suite arrives with later phases; "
        "use 'pytest tests/golden' for the current scaffold checks.",
    )


def _cmd_extract_claims(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import ClaimRepository, claim_record_to_public_dict
    from rge.modules.claim_extractor import extract_claims_for_source

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        result = extract_claims_for_source(
            conn,
            args.source,
            fixture_name=args.fixture,
        )
        claim_repo = ClaimRepository(conn)
        accepted = claim_repo.list_for_source(args.source, status="accepted")
        rejected = claim_repo.list_for_source(args.source, status="rejected")
        payload = {
            "status": result["status"],
            "command": "extract-claims",
            "source_id": args.source,
            "accepted_count": result["accepted_count"],
            "rejected_count": result["rejected_count"],
            "accepted_claims": [
                claim_record_to_public_dict(claim) for claim in accepted
            ],
            "rejected_claims": [
                claim_record_to_public_dict(claim) for claim in rejected
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {"status": "error", "command": "extract-claims", "detail": str(exc)}
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_link_concepts(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import ClaimConceptRepository
    from rge.modules.concept_linker import link_concepts_for_source

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        result = link_concepts_for_source(
            conn,
            args.source,
            fixture_name=args.fixture,
        )
        links = ClaimConceptRepository(conn).list_for_source(args.source)
        payload = {
            "status": result["status"],
            "command": "link-concepts",
            "source_id": args.source,
            "link_count": result["link_count"],
            "links": links,
            "rejected_link_count": result.get("rejected_link_count", 0),
        }
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {"status": "error", "command": "link-concepts", "detail": str(exc)}
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_build_relationships(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import (
        RelationshipEvidenceRepository,
        RelationshipRepository,
    )
    from rge.modules.relationship_builder import build_relationships_for_source

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        result = build_relationships_for_source(
            conn,
            args.source,
            fixture_name=args.fixture,
        )
        relationships = RelationshipRepository(conn).list_for_source(args.source)
        evidence = RelationshipEvidenceRepository(conn).list_for_source(args.source)
        payload = {
            "status": result["status"],
            "command": "build-relationships",
            "source_id": args.source,
            "relationship_count": result.get(
                "relationship_count", len(relationships)
            ),
            "relationships": relationships,
            "evidence_count": len(evidence),
            "evidence": evidence,
            "rejected_relationship_count": result.get(
                "rejected_relationship_count", 0
            ),
        }
        if result.get("rejected_relationships"):
            payload["rejected_relationships"] = result["rejected_relationships"]
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "build-relationships",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_reconcile_scores(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import RelationshipRepository, ScoreEventRepository
    from rge.modules.score_reconciler import reconcile_scores_for_source

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        result = reconcile_scores_for_source(conn, args.source)
        relationships = RelationshipRepository(conn).list_active()
        score_events = ScoreEventRepository(conn).list_for_source(args.source)
        payload = {
            "status": result["status"],
            "command": "reconcile-scores",
            "source_id": args.source,
            "score_events_created": result.get("score_events_created", 0),
            "relationships_updated": result.get("relationships_updated", 0),
            "score_events": score_events,
            "active_relationships": relationships,
        }
        if result.get("skipped"):
            payload["skipped"] = result["skipped"]
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "reconcile-scores",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_ingest(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import (
        ChunkRepository,
        SourceRepository,
        ingest_local_source,
        source_record_to_public_dict,
    )
    from rge.modules.fetcher import FetchError, fetch_local_text_file

    source_path = Path(args.source_path)
    db_path = Path(args.db) if args.db else None

    try:
        fetched = fetch_local_text_file(source_path)
    except FetchError as exc:
        payload = {"status": "error", "command": "ingest", "detail": str(exc)}
        print(json.dumps(payload, indent=2))
        return 1

    conn = ensure_database(db_path)
    try:
        result = ingest_local_source(
            conn,
            local_path=fetched["local_path"],
            domain=args.domain,
            raw_text=fetched["raw_text"],
            title=fetched["title"],
            source_type=fetched["source_type"],
        )
        source = SourceRepository(conn).get_by_id(result["source_id"])
        chunks = ChunkRepository(conn).list_for_source(result["source_id"])
        payload = {
            "status": result["status"],
            "command": "ingest",
            "source": source_record_to_public_dict(source) if source else None,
            "chunk_count": len(chunks),
            "chunk_ids": [chunk.id for chunk in chunks],
            "raw_text_checksum": result["raw_text_checksum"],
        }
        print(json.dumps(payload, indent=2))
        return 0
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research",
        description=(
            "Research Graph Engine CLI. Local-first research infrastructure: "
            "sources -> scoped claims -> concept graph -> evidence graph -> "
            "reports/cards -> improvement tickets."
        ),
    )
    parser.add_argument("--version", action="version", version=f"research {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Run a research workflow for a topic (placeholder in Phase 0).",
        description="Run a research workflow for a topic. Placeholder in Phase 0.",
    )
    run_parser.add_argument("--topic", help="Root research topic.")
    run_parser.add_argument("--domain", help="Domain pack ID (e.g. creativity).")
    run_parser.add_argument(
        "--fixture-mode",
        action="store_true",
        help="Use deterministic fixture sources instead of live discovery.",
    )
    run_parser.set_defaults(func=_cmd_run)

    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest a local text source into SQLite.",
        description="Ingest a local plain-text source and persist source + chunk records.",
    )
    ingest_parser.add_argument(
        "source_path",
        help="Path to a local plain-text source file.",
    )
    ingest_parser.add_argument(
        "--domain",
        required=True,
        help="Primary domain pack ID (e.g. creativity).",
    )
    ingest_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    ingest_parser.set_defaults(func=_cmd_ingest)

    extract_parser = subparsers.add_parser(
        "extract-claims",
        help="Extract scoped claims from an ingested source (mock LLM).",
        description=(
            "Extract candidate claims via the mock model client, validate them "
            "deterministically, and persist accepted/rejected claim records."
        ),
    )
    extract_parser.add_argument(
        "--source",
        required=True,
        help="Stable source ID to extract claims from.",
    )
    extract_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    extract_parser.add_argument(
        "--fixture",
        help="Optional mock LLM fixture filename for deterministic extraction tests.",
    )
    extract_parser.set_defaults(func=_cmd_extract_claims)

    link_parser = subparsers.add_parser(
        "link-concepts",
        help="Link accepted claims to domain concepts (mock LLM).",
        description=(
            "Propose concept links via the mock model client, validate them "
            "deterministically, and persist claim_concepts rows."
        ),
    )
    link_parser.add_argument(
        "--source",
        required=True,
        help="Stable source ID whose accepted claims should be linked.",
    )
    link_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    link_parser.add_argument(
        "--fixture",
        help="Optional mock LLM fixture filename for deterministic linking tests.",
    )
    link_parser.set_defaults(func=_cmd_link_concepts)

    build_parser = subparsers.add_parser(
        "build-relationships",
        help="Build evidence relationships from linked claims (mock LLM).",
        description=(
            "Propose concept relationships via the mock model client, validate them "
            "deterministically, and persist relationships plus relationship_evidence rows."
        ),
    )
    build_parser.add_argument(
        "--source",
        required=True,
        help="Stable source ID whose accepted claims should drive relationships.",
    )
    build_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    build_parser.add_argument(
        "--fixture",
        help="Optional mock LLM fixture filename for deterministic relationship tests.",
    )
    build_parser.set_defaults(func=_cmd_build_relationships)

    reconcile_parser = subparsers.add_parser(
        "reconcile-scores",
        help="Reconcile relationship scores from new supporting evidence.",
        description=(
            "Apply deterministic score updates when new accepted claims support "
            "existing relationships, writing append-only score_events history."
        ),
    )
    reconcile_parser.add_argument(
        "--source",
        required=True,
        help="Stable source ID whose accepted claims may trigger score updates.",
    )
    reconcile_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    reconcile_parser.set_defaults(func=_cmd_reconcile_scores)

    export_parser = subparsers.add_parser(
        "export-public",
        help="Export public-safe card JSON (placeholder in Phase 0).",
        description="Export public-safe card JSON. Placeholder in Phase 0.",
    )
    export_parser.add_argument(
        "--limit", type=int, default=100, help="Maximum records to export."
    )
    export_parser.set_defaults(func=_cmd_export_public)

    verify_parser = subparsers.add_parser(
        "verify",
        help="Run deterministic verification checks (placeholder in Phase 0).",
        description="Run deterministic verification checks. Placeholder in Phase 0.",
    )
    verify_parser.set_defaults(func=_cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
