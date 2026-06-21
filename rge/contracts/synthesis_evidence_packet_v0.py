"""Evidence-only synthesis packet contract (ticket-059 spec; no cloud calls).

Cloud synthesis adapters may consume only packetized refs — never raw documents.
"""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "synthesis_evidence_packet_v0.1.0"

FORBIDDEN_PACKET_KEYS = frozenset(
    {
        "raw_text",
        "raw_html",
        "raw_pdf",
        "document_body",
        "chunk_text",
        "quote_span",
        "prompt",
        "local_path",
    }
)

REQUIRED_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "packet_id",
        "research_question",
        "purpose",
        "atoms",
        "claims",
        "source_refs",
        "trace_refs",
    }
)


def validate_synthesis_evidence_packet(packet: dict[str, Any]) -> list[str]:
    """Return validation errors; empty list means packet is acceptable."""
    errors: list[str] = []
    if not isinstance(packet, dict):
        return ["packet must be a JSON object"]

    missing = sorted(REQUIRED_TOP_LEVEL_KEYS - set(packet.keys()))
    if missing:
        errors.append("missing required keys: " + ", ".join(missing))

    for key in FORBIDDEN_PACKET_KEYS:
        if key in packet:
            errors.append(f"forbidden key present: {key}")

    for atom in packet.get("atoms") or []:
        if not isinstance(atom, dict):
            errors.append("atoms entries must be objects")
            continue
        if not atom.get("atom_id"):
            errors.append("atom missing atom_id")
        if "claim_text" in atom or "quote_span" in atom:
            errors.append("atoms must not include raw claim text or quote spans")

    for claim in packet.get("claims") or []:
        if not isinstance(claim, dict):
            errors.append("claims entries must be objects")
            continue
        if not claim.get("claim_id"):
            errors.append("claim missing claim_id")
        if claim.get("claim_text") or claim.get("quote_span"):
            errors.append("claims must reference ids only — no claim_text or quote_span")

    for ref in packet.get("source_refs") or []:
        if not isinstance(ref, dict) or not ref.get("source_id"):
            errors.append("source_refs entries require source_id")

    for ref in packet.get("trace_refs") or []:
        if not isinstance(ref, dict) or not ref.get("trace_id"):
            errors.append("trace_refs entries require trace_id")

    return errors
