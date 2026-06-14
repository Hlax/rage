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
class CardTemplatesOverlay:
    required_fields_by_type: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class SearchQueryTemplate:
    id: str
    template: str
    preferred_source_types: tuple[str, ...]


@dataclass(frozen=True)
class SearchTemplatesOverlay:
    queries: dict[str, SearchQueryTemplate]


@dataclass(frozen=True)
class SafetyNotesOverlay:
    notes: tuple[str, ...]


@dataclass(frozen=True)
class DomainIdentityOverlay:
    id: str
    name: str
    version: str
    status: str
    summary: str
    primary_domains: tuple[str, ...]
    overlap_domains: tuple[str, ...]
    lifecycle_states: tuple[str, ...]


@dataclass(frozen=True)
class DomainPack:
    pack_id: str
    domain_identity: DomainIdentityOverlay
    concepts: tuple[DomainPackConcept, ...]
    aliases: dict[str, tuple[str, ...]]
    alias_to_canonical: dict[str, str]
    score_reconciliation: ScoreReconciliationOverlay
    evidence_types: tuple[EvidenceTypeDefinition, ...]
    claim_schema: ClaimSchemaOverlay
    source_preferences: SourcePreferencesOverlay
    card_templates: CardTemplatesOverlay
    search_templates: SearchTemplatesOverlay
    safety_notes: SafetyNotesOverlay


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


def parse_card_templates_yaml(path: Path) -> CardTemplatesOverlay:
    """Parse public card template overlay from a domain pack card_templates stub."""
    if not path.is_file():
        raise DomainPackError(f"Card templates file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise DomainPackError(f"Card templates file is empty: {path}")

    if not re.search(r"^cards:\s*$", text, re.MULTILINE):
        raise DomainPackError(
            f"Card templates file must contain top-level 'cards:' key: {path}"
        )

    required_by_type: dict[str, list[str]] = {}
    current_type: str | None = None
    in_required = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "cards:":
            continue

        match_type = re.match(r"^  ([\w]+):\s*$", line)
        if match_type:
            current_type = match_type.group(1).casefold()
            required_by_type[current_type] = []
            in_required = False
            continue

        if current_type is None:
            continue

        if stripped == "required_fields:":
            in_required = True
            continue

        if in_required:
            match_field = re.match(r"^\s{6}- (.+)$", line)
            if match_field:
                required_by_type[current_type].append(match_field.group(1).strip())
                continue
            if line and not line.startswith(" "):
                in_required = False
            elif line.startswith("    ") and not line.startswith("      "):
                in_required = False

    if not required_by_type:
        raise DomainPackError(f"No card templates found in {path}")

    for card_type, fields in required_by_type.items():
        if not fields:
            raise DomainPackError(
                f"Card template {card_type!r} missing required_fields in {path}"
            )

    return CardTemplatesOverlay(
        required_fields_by_type={
            card_type: tuple(fields) for card_type, fields in required_by_type.items()
        }
    )


def template_required_fields(pack: DomainPack, card_type: str) -> tuple[str, ...]:
    """Return pack-defined required fields for a public card type."""
    normalized = card_type.strip().casefold()
    if not normalized:
        return ()
    return pack.card_templates.required_fields_by_type.get(normalized, ())


def parse_search_templates_yaml(path: Path) -> SearchTemplatesOverlay:
    """Parse search query templates from a domain pack search_templates stub."""
    if not path.is_file():
        raise DomainPackError(f"Search templates file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise DomainPackError(f"Search templates file is empty: {path}")

    if not re.search(r"^queries:\s*$", text, re.MULTILINE):
        raise DomainPackError(
            f"Search templates file must contain top-level 'queries:' key: {path}"
        )

    queries: dict[str, SearchQueryTemplate] = {}
    current_id: str | None = None
    template_text = ""
    preferred_types: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "queries:":
            continue

        match_id = re.match(r"^  ([\w]+):\s*$", line)
        if match_id:
            if current_id is not None:
                if not template_text:
                    raise DomainPackError(
                        f"Search template {current_id!r} missing template in {path}"
                    )
                queries[current_id] = SearchQueryTemplate(
                    id=current_id,
                    template=template_text,
                    preferred_source_types=tuple(preferred_types),
                )
            current_id = match_id.group(1)
            template_text = ""
            preferred_types = []
            continue

        if current_id is None:
            continue

        match_template = re.match(r"^    template:\s*\"(.*)\"\s*$", line)
        if match_template:
            template_text = match_template.group(1)
            continue

        match_types = re.match(r"^    preferred_source_types:\s*\[(.*)\]\s*$", line)
        if match_types:
            preferred_types = [
                item.strip() for item in match_types.group(1).split(",") if item.strip()
            ]

    if current_id is not None:
        if not template_text:
            raise DomainPackError(
                f"Search template {current_id!r} missing template in {path}"
            )
        queries[current_id] = SearchQueryTemplate(
            id=current_id,
            template=template_text,
            preferred_source_types=tuple(preferred_types),
        )

    if not queries:
        raise DomainPackError(f"No search query templates found in {path}")

    return SearchTemplatesOverlay(queries=queries)


def search_template_topic_signals(pack: DomainPack, question_text: str) -> int:
    """Count topic-fit signals from pack search template keyword overlap."""
    question = _normalize_label(question_text)
    signals = 0
    for query in pack.search_templates.queries.values():
        words = [
            _normalize_label(word)
            for word in query.template.split()
            if len(word.strip()) > 3
        ]
        matches = sum(1 for word in words if word in question)
        if matches >= 2:
            signals += 2
        elif matches == 1:
            signals += 1
    return signals


def _parse_yaml_multiline_list(text: str, header: str) -> list[str]:
    """Parse a YAML list section that may use folded multi-line bullet items."""
    items: list[str] = []
    in_section = False
    current_parts: list[str] = []

    for line in text.splitlines():
        if line.strip() == f"{header}:":
            in_section = True
            continue
        if not in_section:
            continue
        if line and not line.startswith(" "):
            break
        match = re.match(r"^  - (.+)$", line)
        if match:
            if current_parts:
                items.append(" ".join(current_parts).strip())
            current_parts = [match.group(1).strip()]
            continue
        if current_parts and line.startswith("    "):
            current_parts.append(line.strip())

    if current_parts:
        items.append(" ".join(current_parts).strip())
    return items


def parse_domain_yaml(path: Path) -> DomainIdentityOverlay:
    """Parse domain pack identity metadata from a domain.yaml stub."""
    if not path.is_file():
        raise DomainPackError(f"Domain file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise DomainPackError(f"Domain file is empty: {path}")

    fields: dict[str, str] = {}
    for key in ("id", "name", "version", "status"):
        match = re.search(rf"^{key}: (.+)$", text, re.MULTILINE)
        if not match:
            raise DomainPackError(f"Domain file missing required field {key!r}: {path}")
        fields[key] = match.group(1).strip()

    summary_lines: list[str] = []
    in_summary = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("summary:"):
            in_summary = True
            inline = stripped.split(":", 1)[1].strip()
            if inline and inline != ">":
                summary_lines.append(inline)
            continue
        if in_summary:
            if line.startswith("  ") and not stripped.endswith(":"):
                summary_lines.append(stripped)
            elif stripped and not line.startswith(" "):
                in_summary = False

    primary_domains = _parse_yaml_list_section(text, "primary_domains")
    overlap_domains = _parse_yaml_list_section(text, "overlap_domains")
    lifecycle_states = _parse_yaml_list_section(text, "lifecycle_states")

    if not primary_domains:
        raise DomainPackError(f"Domain file missing primary_domains list in {path}")
    if not lifecycle_states:
        raise DomainPackError(f"Domain file missing lifecycle_states list in {path}")

    return DomainIdentityOverlay(
        id=fields["id"],
        name=fields["name"],
        version=fields["version"],
        status=fields["status"],
        summary=" ".join(summary_lines).strip(),
        primary_domains=tuple(primary_domains),
        overlap_domains=tuple(overlap_domains),
        lifecycle_states=tuple(lifecycle_states),
    )


def verify_pack_identity_for_audit(pack: DomainPack) -> list[str]:
    """Return violations when pack identity metadata is inconsistent or inactive."""
    violations: list[str] = []
    identity = pack.domain_identity
    if pack.pack_id.casefold() != identity.id.casefold():
        violations.append(
            "domain pack directory id does not match domain.yaml id "
            f"({pack.pack_id!r} vs {identity.id!r})"
        )
    if identity.status.casefold() != "active":
        violations.append(f"domain pack status is not active: {identity.status!r}")
    return violations


def allowed_domains_for_pack(pack: DomainPack) -> frozenset[str]:
    """Return normalized domain labels declared by pack primary and overlap lists."""
    labels = list(pack.domain_identity.primary_domains) + list(
        pack.domain_identity.overlap_domains
    )
    return frozenset(_normalize_label(label) for label in labels if label.strip())


def parse_safety_notes_yaml(path: Path) -> SafetyNotesOverlay:
    """Parse domain safety notes from a domain pack safety_notes stub."""
    if not path.is_file():
        raise DomainPackError(f"Safety notes file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise DomainPackError(f"Safety notes file is empty: {path}")

    if not re.search(r"^notes:\s*$", text, re.MULTILINE):
        raise DomainPackError(
            f"Safety notes file must contain top-level 'notes:' key: {path}"
        )

    notes = _parse_yaml_multiline_list(text, "notes")
    if not notes:
        raise DomainPackError(f"Safety notes file missing notes list in {path}")

    return SafetyNotesOverlay(notes=tuple(notes))


def required_safety_note_themes_for_pack(pack_id: str) -> tuple[str, ...]:
    """Return guidance substrings the safety auditor must find in pack safety notes."""
    normalized = pack_id.strip().casefold()
    if normalized == "creativity":
        return (
            "prompt injection",
            "marketing pages",
            "scope-sensitive",
        )
    return ("prompt injection",)


def verify_pack_safety_notes_for_audit(
    pack: DomainPack,
    *,
    required_substrings: tuple[str, ...],
    minimum_note_count: int = 1,
) -> list[str]:
    """Return machine-readable violations when pack safety notes miss audit guidance."""
    violations: list[str] = []
    notes = pack.safety_notes.notes
    if len(notes) < minimum_note_count:
        violations.append(
            f"domain pack safety notes below minimum count {minimum_note_count}"
        )
    combined = "\n".join(notes).casefold()
    for substring in required_substrings:
        if substring.casefold() not in combined:
            violations.append(
                f"domain pack safety notes missing guidance substring: {substring!r}"
            )
    return violations


def source_strategy_from_search_templates(pack: DomainPack) -> dict[str, Any]:
    """Build contract source_strategy search_queries from pack templates."""
    return {
        "mode": "pack_search_templates",
        "search_queries": {
            query_id: {
                "template": query.template,
                "preferred_source_types": list(query.preferred_source_types),
            }
            for query_id, query in pack.search_templates.queries.items()
        },
    }


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
    card_templates_path = pack_root / "card_templates.yaml"
    search_templates_path = pack_root / "search_templates.yaml"
    safety_notes_path = pack_root / "safety_notes.yaml"
    domain_path = pack_root / "domain.yaml"

    domain_identity = parse_domain_yaml(domain_path)
    if _normalize_label(pack_id) != _normalize_label(domain_identity.id):
        raise DomainPackError(
            f"Domain pack id mismatch: directory {pack_id!r} vs "
            f"domain.yaml id {domain_identity.id!r}"
        )

    concepts = parse_ontology_yaml(ontology_path)
    alias_map = parse_aliases_yaml(aliases_path)
    alias_to_canonical = build_alias_to_canonical(alias_map)
    score_reconciliation = parse_scoring_yaml(scoring_path)
    evidence_types = parse_evidence_types_yaml(evidence_types_path)
    claim_schema = parse_claim_schema_yaml(claim_schema_path)
    source_preferences = parse_source_preferences_yaml(source_preferences_path)
    card_templates = parse_card_templates_yaml(card_templates_path)
    search_templates = parse_search_templates_yaml(search_templates_path)
    safety_notes = parse_safety_notes_yaml(safety_notes_path)

    return DomainPack(
        pack_id=pack_id,
        domain_identity=domain_identity,
        concepts=tuple(concepts),
        aliases={key: tuple(values) for key, values in alias_map.items()},
        alias_to_canonical=alias_to_canonical,
        score_reconciliation=score_reconciliation,
        evidence_types=evidence_types,
        claim_schema=claim_schema,
        source_preferences=source_preferences,
        card_templates=card_templates,
        search_templates=search_templates,
        safety_notes=safety_notes,
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
