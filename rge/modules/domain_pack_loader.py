"""Load domain pack ontology and aliases. Deterministic; no model use.

Reads ``domain_packs/<pack_id>/ontology.yaml`` and ``aliases.yaml`` using a
focused hand-rolled parser (no PyYAML). Domain-specific vocabulary lives in
pack files; the core engine must not hardcode pack content.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class DomainPackError(ValueError):
    """Raised when a domain pack cannot be loaded or parsed."""


_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class DomainPackConcept:
    id: str
    label: str
    definition: str
    status: str


@dataclass(frozen=True)
class EvidenceTypeDefinition:
    id: str
    base_strength: float
    notes: str


@dataclass(frozen=True)
class ScoreReconciliationOverlay:
    formula_version: str
    stronger_evidence_boost: float
    stronger_claim_confidence_threshold: float
    stronger_source_reason: str


@dataclass(frozen=True)
class DomainPack:
    pack_id: str
    concepts: tuple[DomainPackConcept, ...]
    aliases: dict[str, tuple[str, ...]]
    alias_to_canonical: dict[str, str]
    score_reconciliation: ScoreReconciliationOverlay
    evidence_types: tuple[EvidenceTypeDefinition, ...]


def repo_root() -> Path:
    return _REPO_ROOT


def domain_pack_dir(pack_id: str, *, root: Path | None = None) -> Path:
    return (root or _REPO_ROOT) / "domain_packs" / pack_id


def _normalize_label(label: str) -> str:
    return label.strip().casefold()


def parse_ontology_yaml(path: Path) -> list[DomainPackConcept]:
    """Parse ontology concepts from a domain pack ontology stub."""
    if not path.is_file():
        raise DomainPackError(f"Ontology file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise DomainPackError(f"Ontology file is empty: {path}")

    concepts: list[DomainPackConcept] = []
    for block in re.split(r"\n  - id:", text)[1:]:
        fields: dict[str, str] = {}
        block = f"id:{block}"
        for key in ("id", "label", "status", "definition"):
            match = re.search(rf"^\s*{key}: (.+)$", block, re.MULTILINE)
            if match:
                fields[key] = match.group(1).strip()
        concept_id = fields.get("id", "")
        label = fields.get("label", "")
        if not concept_id or not label:
            raise DomainPackError(
                f"Malformed ontology concept in {path}: each concept requires id and label"
            )
        concepts.append(
            DomainPackConcept(
                id=concept_id,
                label=label,
                definition=fields.get("definition", ""),
                status=fields.get("status", "candidate"),
            )
        )

    if not concepts:
        raise DomainPackError(f"No ontology concepts found in {path}")

    return concepts


def parse_aliases_yaml(path: Path) -> dict[str, list[str]]:
    """Parse canonical-label → alias phrases from a domain pack aliases stub."""
    if not path.is_file():
        raise DomainPackError(f"Aliases file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise DomainPackError(f"Aliases file is empty: {path}")

    if not re.search(r"^aliases:\s*$", text, re.MULTILINE):
        raise DomainPackError(f"Aliases file must contain top-level 'aliases:' key: {path}")

    aliases: dict[str, list[str]] = {}
    current_canonical: str | None = None

    for line in text.splitlines():
        if line.strip() == "aliases:" or not line.strip() or line.lstrip().startswith("#"):
            continue

        canonical_match = re.match(r"^  ([^:\n]+):\s*$", line)
        if canonical_match:
            current_canonical = canonical_match.group(1).strip()
            if not current_canonical:
                raise DomainPackError(f"Malformed canonical alias key in {path}")
            aliases.setdefault(current_canonical, [])
            continue

        alias_match = re.match(r"^    - (.+)$", line)
        if alias_match:
            if current_canonical is None:
                raise DomainPackError(
                    f"Alias list entry before canonical key in {path}: {line!r}"
                )
            alias_phrase = alias_match.group(1).strip()
            if not alias_phrase:
                raise DomainPackError(f"Empty alias phrase in {path}")
            aliases[current_canonical].append(alias_phrase)
            continue

        if line.startswith("  "):
            raise DomainPackError(f"Unrecognized aliases.yaml line in {path}: {line!r}")

    if not aliases:
        raise DomainPackError(f"No alias mappings found in {path}")

    return aliases


def _parse_scalar_value(raw: str) -> str | float | bool:
    value = raw.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip('"').strip("'")


def parse_scoring_yaml(path: Path) -> ScoreReconciliationOverlay:
    """Parse score reconciliation overlay from a domain pack scoring stub."""
    if not path.is_file():
        raise DomainPackError(f"Scoring file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise DomainPackError(f"Scoring file is empty: {path}")

    if "score_reconciliation:" not in text:
        raise DomainPackError(
            f"Scoring file must contain top-level 'score_reconciliation:' section: {path}"
        )

    section_lines: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line.strip() == "score_reconciliation:":
            in_section = True
            continue
        if in_section:
            if line and not line.startswith(" "):
                break
            section_lines.append(line)

    fields: dict[str, Any] = {}
    idx = 0
    while idx < len(section_lines):
        line = section_lines[idx]
        match = re.match(r"^\s{2}(\w+):\s*(.*)$", line)
        if not match:
            idx += 1
            continue
        key = match.group(1)
        raw = match.group(2).strip()
        if raw in {">-", ">", "|", "|+", "|-"}:
            value_lines: list[str] = []
            idx += 1
            while idx < len(section_lines):
                continuation = section_lines[idx]
                if not continuation.startswith("    "):
                    break
                value_lines.append(continuation.strip())
                idx += 1
            fields[key] = " ".join(value_lines)
            continue
        fields[key] = _parse_scalar_value(raw)
        idx += 1

    required = (
        "formula_version",
        "stronger_evidence_boost",
        "stronger_claim_confidence_threshold",
        "stronger_source_reason",
    )
    missing = [key for key in required if key not in fields]
    if missing:
        raise DomainPackError(
            f"Scoring file missing score_reconciliation keys {missing} in {path}"
        )

    return ScoreReconciliationOverlay(
        formula_version=str(fields["formula_version"]),
        stronger_evidence_boost=float(fields["stronger_evidence_boost"]),
        stronger_claim_confidence_threshold=float(
            fields["stronger_claim_confidence_threshold"]
        ),
        stronger_source_reason=str(fields["stronger_source_reason"]).strip(),
    )


def parse_evidence_types_yaml(path: Path) -> tuple[EvidenceTypeDefinition, ...]:
    """Parse evidence type definitions from a domain pack evidence_types stub."""
    if not path.is_file():
        raise DomainPackError(f"Evidence types file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise DomainPackError(f"Evidence types file is empty: {path}")

    if not re.search(r"^evidence_types:\s*$", text, re.MULTILINE):
        raise DomainPackError(
            f"Evidence types file must contain top-level 'evidence_types:' key: {path}"
        )

    definitions: list[EvidenceTypeDefinition] = []
    current_id: str | None = None
    current_fields: dict[str, Any] = {}

    def _finalize_current() -> None:
        nonlocal current_id, current_fields
        if current_id is None:
            return
        missing = [
            key
            for key in ("base_strength", "notes")
            if key not in current_fields
        ]
        if missing:
            raise DomainPackError(
                f"Evidence type {current_id!r} missing keys {missing} in {path}"
            )
        definitions.append(
            EvidenceTypeDefinition(
                id=current_id,
                base_strength=float(current_fields["base_strength"]),
                notes=str(current_fields["notes"]).strip(),
            )
        )
        current_id = None
        current_fields = {}

    for line in text.splitlines():
        if line.strip() == "evidence_types:" or not line.strip() or line.lstrip().startswith(
            "#"
        ):
            continue

        type_match = re.match(r"^  (\w+):\s*$", line)
        if type_match:
            _finalize_current()
            current_id = type_match.group(1)
            continue

        field_match = re.match(r"^    (\w+): (.+)$", line)
        if field_match:
            if current_id is None:
                raise DomainPackError(
                    f"Evidence type field before type id in {path}: {line!r}"
                )
            current_fields[field_match.group(1)] = _parse_scalar_value(
                field_match.group(2)
            )
            continue

        if line.startswith("  "):
            raise DomainPackError(
                f"Unrecognized evidence_types.yaml line in {path}: {line!r}"
            )

    _finalize_current()

    if not definitions:
        raise DomainPackError(f"No evidence type definitions found in {path}")

    return tuple(definitions)


def evidence_type_ids(pack: DomainPack) -> frozenset[str]:
    """Return normalized evidence type ids declared by a domain pack."""
    return frozenset(evidence_type.id.casefold() for evidence_type in pack.evidence_types)


def build_alias_to_canonical(aliases: dict[str, list[str]]) -> dict[str, str]:
    """Build normalized alias phrase → canonical label reverse map."""
    reverse: dict[str, str] = {}
    for canonical, phrases in aliases.items():
        normalized_canonical = _normalize_label(canonical)
        if normalized_canonical in reverse:
            raise DomainPackError(
                f"Duplicate canonical alias key after normalization: {canonical!r}"
            )
        for phrase in phrases:
            normalized_phrase = _normalize_label(phrase)
            if normalized_phrase in reverse:
                raise DomainPackError(
                    f"Duplicate alias phrase after normalization: {phrase!r}"
                )
            reverse[normalized_phrase] = canonical
    return reverse


def load_domain_pack(pack_id: str, *, root: Path | None = None) -> DomainPack:
    """Load ontology concepts and aliases for a domain pack."""
    pack_root = domain_pack_dir(pack_id, root=root)
    if not pack_root.is_dir():
        raise DomainPackError(f"Domain pack not found: {pack_id}")

    ontology_path = pack_root / "ontology.yaml"
    aliases_path = pack_root / "aliases.yaml"
    scoring_path = pack_root / "scoring.yaml"
    evidence_types_path = pack_root / "evidence_types.yaml"

    concepts = parse_ontology_yaml(ontology_path)
    alias_map = parse_aliases_yaml(aliases_path)
    alias_to_canonical = build_alias_to_canonical(alias_map)
    score_reconciliation = parse_scoring_yaml(scoring_path)
    evidence_types = parse_evidence_types_yaml(evidence_types_path)

    return DomainPack(
        pack_id=pack_id,
        concepts=tuple(concepts),
        aliases={key: tuple(values) for key, values in alias_map.items()},
        alias_to_canonical=alias_to_canonical,
        score_reconciliation=score_reconciliation,
        evidence_types=evidence_types,
    )


def resolve_canonical_concept_label(pack: DomainPack, concept_label: str) -> str:
    """Map an alias phrase to its canonical ontology label when defined."""
    normalized = _normalize_label(concept_label)
    if normalized in pack.alias_to_canonical:
        return pack.alias_to_canonical[normalized]
    for concept in pack.concepts:
        if _normalize_label(concept.label) == normalized:
            return concept.label
    return concept_label.strip()


def concepts_as_dicts(pack: DomainPack) -> list[dict[str, Any]]:
    """Return ontology concepts in the legacy dict shape used by repositories."""
    return [
        {
            "id": concept.id,
            "label": concept.label,
            "definition": concept.definition,
            "status": concept.status,
        }
        for concept in pack.concepts
    ]
