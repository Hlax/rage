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
class ClaimSchemaOverlay:
    required_domain_metadata_keys: tuple[str, ...]
    allowed_tracks: frozenset[str]
    allowed_creative_phases: frozenset[str]
    allowed_measured_dimensions: frozenset[str]


@dataclass(frozen=True)
class SourcePreferencesOverlay:
    source_type_weights: dict[str, float]
    preferred_sources: tuple[str, ...]
    avoid_as_primary: tuple[str, ...]


@dataclass(frozen=True)
class DomainPack:
    pack_id: str
    concepts: tuple[DomainPackConcept, ...]
    aliases: dict[str, tuple[str, ...]]
    alias_to_canonical: dict[str, str]
    score_reconciliation: ScoreReconciliationOverlay
    evidence_types: tuple[EvidenceTypeDefinition, ...]
    claim_schema: ClaimSchemaOverlay
    source_preferences: SourcePreferencesOverlay


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


def _parse_yaml_list_section(text: str, header: str) -> list[str]:
    items: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line.strip() == f"{header}:":
            in_section = True
            continue
        if in_section:
            if line and not line.startswith(" "):
                break
            match = re.match(r"^\s{2}- (.+)$", line)
            if match:
                items.append(match.group(1).strip())
    return items


def _normalized_allowset(values: list[str]) -> frozenset[str]:
    return frozenset(_normalize_label(value) for value in values if value.strip())


def parse_claim_schema_yaml(path: Path) -> ClaimSchemaOverlay:
    """Parse claim schema overlay from a domain pack claim_schema stub."""
    if not path.is_file():
        raise DomainPackError(f"Claim schema file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise DomainPackError(f"Claim schema file is empty: {path}")

    required_keys = _parse_yaml_list_section(
        text, "required_domain_metadata_for_creativity_claims"
    )
    allowed_tracks = _parse_yaml_list_section(text, "allowed_tracks")
    allowed_phases = _parse_yaml_list_section(text, "allowed_creative_phases")
    allowed_dimensions = _parse_yaml_list_section(text, "allowed_measured_dimensions")

    if not required_keys:
        raise DomainPackError(
            f"Claim schema file missing required_domain_metadata_for_creativity_claims "
            f"list in {path}"
        )
    if not allowed_tracks:
        raise DomainPackError(f"Claim schema file missing allowed_tracks list in {path}")
    if not allowed_phases:
        raise DomainPackError(
            f"Claim schema file missing allowed_creative_phases list in {path}"
        )
    if not allowed_dimensions:
        raise DomainPackError(
            f"Claim schema file missing allowed_measured_dimensions list in {path}"
        )

    return ClaimSchemaOverlay(
        required_domain_metadata_keys=tuple(required_keys),
        allowed_tracks=_normalized_allowset(allowed_tracks),
        allowed_creative_phases=_normalized_allowset(allowed_phases),
        allowed_measured_dimensions=_normalized_allowset(allowed_dimensions),
    )


def measured_dimension_allowed(pack: DomainPack, value: str) -> bool:
    """Check whether a measured_dimension value is allowed by the pack schema."""
    schema = pack.claim_schema
    direct = _normalize_label(value)
    if direct in schema.allowed_measured_dimensions:
        return True
    resolved = resolve_canonical_concept_label(pack, value)
    return _normalize_label(resolved) in schema.allowed_measured_dimensions


def validate_link_domain_metadata(
    pack: DomainPack,
    metadata: dict[str, Any],
) -> tuple[bool, str | None]:
    """Validate present concept-link domain_metadata keys against pack allowlists."""
    if not metadata:
        return True, None

    for key, raw_value in metadata.items():
        if key not in {"track", "creative_phase", "measured_dimension"}:
            continue
        if raw_value is None or (isinstance(raw_value, str) and not str(raw_value).strip()):
            return False, f"domain_metadata key {key!r} is empty"
        value = str(raw_value).strip()
        if key == "track":
            if _normalize_label(value) not in pack.claim_schema.allowed_tracks:
                return (
                    False,
                    f"domain_metadata track {value!r} is not in domain pack allowlist",
                )
        elif key == "creative_phase":
            if _normalize_label(value) not in pack.claim_schema.allowed_creative_phases:
                return (
                    False,
                    f"domain_metadata creative_phase {value!r} is not in domain pack allowlist",
                )
        elif key == "measured_dimension":
            if not measured_dimension_allowed(pack, value):
                return (
                    False,
                    f"domain_metadata measured_dimension {value!r} is not in domain pack allowlist",
                )

    return True, None


UNKNOWN_SOURCE_TYPE_CREDIBILITY_DEFAULT = 0.40


def parse_source_preferences_yaml(path: Path) -> SourcePreferencesOverlay:
    """Parse source preferences overlay from a domain pack source_preferences stub."""
    if not path.is_file():
        raise DomainPackError(f"Source preferences file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise DomainPackError(f"Source preferences file is empty: {path}")

    if "source_type_weights:" not in text:
        raise DomainPackError(
            f"Source preferences file must contain 'source_type_weights:' section: {path}"
        )

    weight_lines: list[str] = []
    in_weights = False
    for line in text.splitlines():
        if line.strip() == "source_type_weights:":
            in_weights = True
            continue
        if in_weights:
            if line and not line.startswith(" "):
                break
            weight_lines.append(line)

    source_type_weights: dict[str, float] = {}
    for line in weight_lines:
        match = re.match(r"^\s{2}([\w]+):\s*([\d.]+)\s*$", line)
        if not match:
            continue
        source_type_weights[match.group(1).casefold()] = float(match.group(2))

    if not source_type_weights:
        raise DomainPackError(
            f"Source preferences file missing source_type_weights entries in {path}"
        )

    preferred_sources = tuple(_parse_yaml_list_section(text, "preferred_sources"))
    avoid_as_primary = tuple(_parse_yaml_list_section(text, "avoid_as_primary"))

    return SourcePreferencesOverlay(
        source_type_weights=source_type_weights,
        preferred_sources=preferred_sources,
        avoid_as_primary=avoid_as_primary,
    )


def source_type_credibility_prior(
    pack: DomainPack,
    source_type: str,
    *,
    default: float = UNKNOWN_SOURCE_TYPE_CREDIBILITY_DEFAULT,
) -> float:
    """Return pack-defined credibility prior for a candidate source type."""
    normalized = source_type.strip().casefold()
    if not normalized:
        return default
    return pack.source_preferences.source_type_weights.get(normalized, default)


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
    claim_schema_path = pack_root / "claim_schema.yaml"
    source_preferences_path = pack_root / "source_preferences.yaml"

    concepts = parse_ontology_yaml(ontology_path)
    alias_map = parse_aliases_yaml(aliases_path)
    alias_to_canonical = build_alias_to_canonical(alias_map)
    score_reconciliation = parse_scoring_yaml(scoring_path)
    evidence_types = parse_evidence_types_yaml(evidence_types_path)
    claim_schema = parse_claim_schema_yaml(claim_schema_path)
    source_preferences = parse_source_preferences_yaml(source_preferences_path)

    return DomainPack(
        pack_id=pack_id,
        concepts=tuple(concepts),
        aliases={key: tuple(values) for key, values in alias_map.items()},
        alias_to_canonical=alias_to_canonical,
        score_reconciliation=score_reconciliation,
        evidence_types=evidence_types,
        claim_schema=claim_schema,
        source_preferences=source_preferences,
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
