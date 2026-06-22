"""Evidence-only synthesis packet contract (ticket-059; no cloud calls).

v0.1.0 packets are refs-only (spec/dry-run legacy). Live synthesis requires
v0.2.0 grounded packets with claim/atom text — never opaque ID inference.
"""

from __future__ import annotations

import re
from typing import Any

SCHEMA_VERSION = "synthesis_evidence_packet_v0.1.0"
SCHEMA_VERSION_GROUNDED = "synthesis_evidence_packet_v0.2.0"
SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION, SCHEMA_VERSION_GROUNDED})

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

_GROUNDED_CLAIM_TEXT_KEYS = ("claim_text", "canonical_text")
_GROUNDED_ATOM_TEXT_KEYS = ("canonical_text", "summary_text")
_SOURCE_METADATA_KEYS = ("title", "year", "source_type")


def _claim_text(claim: dict[str, Any]) -> str:
    for key in _GROUNDED_CLAIM_TEXT_KEYS:
        value = str(claim.get(key) or "").strip()
        if value:
            return value
    return ""


def _atom_text(atom: dict[str, Any]) -> str:
    for key in _GROUNDED_ATOM_TEXT_KEYS:
        value = str(atom.get(key) or "").strip()
        if value:
            return value
    return ""


def is_refs_only_packet(packet: dict[str, Any]) -> bool:
    """True when packet lacks grounded claim/atom text (v0.1.0 or incomplete v0.2.0)."""
    schema = str(packet.get("schema_version") or "")
    if schema == SCHEMA_VERSION:
        return True
    for claim in packet.get("claims") or []:
        if isinstance(claim, dict) and _claim_text(claim):
            return False
    for atom in packet.get("atoms") or []:
        if isinstance(atom, dict) and _atom_text(atom):
            return False
    return True


def validate_synthesis_evidence_packet(packet: dict[str, Any]) -> list[str]:
    """Return structural validation errors; empty list means acceptable shape."""
    errors: list[str] = []
    if not isinstance(packet, dict):
        return ["packet must be a JSON object"]

    schema = str(packet.get("schema_version") or "")
    if schema and schema not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(f"unsupported schema_version: {schema}")

    missing = sorted(REQUIRED_TOP_LEVEL_KEYS - set(packet.keys()))
    if missing:
        errors.append("missing required keys: " + ", ".join(missing))

    for key in FORBIDDEN_PACKET_KEYS:
        if key in packet:
            errors.append(f"forbidden key present: {key}")

    is_grounded_schema = schema == SCHEMA_VERSION_GROUNDED

    for atom in packet.get("atoms") or []:
        if not isinstance(atom, dict):
            errors.append("atoms entries must be objects")
            continue
        if not atom.get("atom_id"):
            errors.append("atom missing atom_id")
        if not is_grounded_schema and ("claim_text" in atom or "quote_span" in atom):
            errors.append("v0.1.0 atoms must not include claim_text or quote_span")

    for claim in packet.get("claims") or []:
        if not isinstance(claim, dict):
            errors.append("claims entries must be objects")
            continue
        if not claim.get("claim_id"):
            errors.append("claim missing claim_id")
        if not is_grounded_schema and (claim.get("claim_text") or claim.get("quote_span")):
            errors.append("v0.1.0 claims must not include claim_text or quote_span")

    for ref in packet.get("source_refs") or []:
        if not isinstance(ref, dict) or not ref.get("source_id"):
            errors.append("source_refs entries require source_id")

    for ref in packet.get("trace_refs") or []:
        if not isinstance(ref, dict) or not ref.get("trace_id"):
            errors.append("trace_refs entries require trace_id")

    return errors


def validate_grounded_synthesis_packet(packet: dict[str, Any]) -> list[str]:
    """Strict grounding validation for live synthesis (v0.2.0 required)."""
    errors = list(validate_synthesis_evidence_packet(packet))
    schema = str(packet.get("schema_version") or "")
    if schema != SCHEMA_VERSION_GROUNDED:
        errors.append(
            f"live synthesis requires schema_version={SCHEMA_VERSION_GROUNDED!r}; "
            f"refs-only v0.1.0 packets are rejected"
        )
        return errors

    if is_refs_only_packet(packet):
        errors.append("refs-only packet rejected: claims and atoms require grounded text")

    claims = [row for row in (packet.get("claims") or []) if isinstance(row, dict)]
    atoms = [row for row in (packet.get("atoms") or []) if isinstance(row, dict)]
    sources = {
        str(row.get("source_id")): row
        for row in (packet.get("source_refs") or [])
        if isinstance(row, dict) and row.get("source_id")
    }

    if not claims:
        errors.append("grounded packet requires at least one claim")
    if not atoms:
        errors.append("grounded packet requires at least one atom")

    for index, claim in enumerate(claims):
        prefix = f"claims[{index}]"
        if not _claim_text(claim):
            errors.append(f"{prefix} missing claim_text or canonical_text")
        if not str(claim.get("source_id") or "").strip():
            errors.append(f"{prefix} missing source_id")
        if not str(claim.get("stance") or "").strip():
            errors.append(f"{prefix} missing stance")
        if not str(claim.get("scope") or "").strip():
            errors.append(f"{prefix} missing scope")
        limitations = claim.get("limitations")
        if limitations is None:
            errors.append(f"{prefix} missing limitations (use [] when none)")
        elif not isinstance(limitations, list):
            errors.append(f"{prefix} limitations must be a list")

    for index, atom in enumerate(atoms):
        prefix = f"atoms[{index}]"
        if not _atom_text(atom):
            errors.append(f"{prefix} missing canonical_text or summary_text")
        claim_ids = atom.get("claim_ids") or []
        if not claim_ids:
            errors.append(f"{prefix} missing claim_ids")

    for index, ref in enumerate(packet.get("source_refs") or []):
        if not isinstance(ref, dict):
            continue
        prefix = f"source_refs[{index}]"
        if not str(ref.get("source_type") or "").strip():
            errors.append(f"{prefix} missing source_type")
        if not str(ref.get("title") or "").strip():
            errors.append(f"{prefix} missing title")

    known_claim_ids = {str(c.get("claim_id")) for c in claims if c.get("claim_id")}
    for index, atom in enumerate(atoms):
        for claim_id in atom.get("claim_ids") or []:
            if str(claim_id) not in known_claim_ids:
                errors.append(f"atoms[{index}] references unknown claim_id: {claim_id}")
        for source_id in atom.get("source_ids") or []:
            if str(source_id) not in sources:
                errors.append(f"atoms[{index}] references unknown source_id: {source_id}")

    return errors


def significant_tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z]{4,}", text.lower())}


def claim_text_by_id(packet: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for claim in packet.get("claims") or []:
        if not isinstance(claim, dict) or not claim.get("claim_id"):
            continue
        text = _claim_text(claim)
        if text:
            mapping[str(claim["claim_id"])] = text
    return mapping


def atom_text_by_id(packet: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for atom in packet.get("atoms") or []:
        if not isinstance(atom, dict) or not atom.get("atom_id"):
            continue
        text = _atom_text(atom)
        if text:
            mapping[str(atom["atom_id"])] = text
    return mapping


def _iter_packet_paths(value: object, prefix: str = "") -> list[tuple[str, object]]:
    paths: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            paths.append((path, item))
            paths.extend(_iter_packet_paths(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_iter_packet_paths(item, f"{prefix}[{index}]"))
    return paths


def assert_synthesis_packet_operator_safe(packet: dict[str, Any]) -> list[str]:
    """Ensure operator-private synthesis packets exclude raw source text and secrets."""
    violations: list[str] = []
    for key_path, item in _iter_packet_paths(packet):
        leaf = key_path.rsplit(".", 1)[-1]
        leaf = leaf.split("[", 1)[0]
        if leaf in FORBIDDEN_PACKET_KEYS:
            violations.append(f"forbidden packet key: {key_path}")
        if isinstance(item, str):
            lowered = item.casefold()
            if "fixtures/sources/" in lowered or "data/sources/" in lowered:
                violations.append(f"possible local source path in {key_path}")
            if "api_key" in lowered or item.startswith("sk-"):
                violations.append(f"possible secret in {key_path}")
    return violations
