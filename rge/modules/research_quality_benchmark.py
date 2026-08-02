"""Deterministic claim-admission benchmark for Phase 4 research quality.

The benchmark is deliberately read-only. It loads committed fixture text, verifies
the corpus contract, evaluates candidate decisions, and returns JSON-safe metrics.
It does not call a model or network service and it has no database or public-export
write path.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA_VERSION = "research_quality_benchmark_manifest_v1"
RESULT_SCHEMA_VERSION = "research_quality_benchmark_result_v1"
QUOTE_PRESENCE_BASELINE_ID = "quote_presence_v0"
DEFAULT_MANIFEST_REL = Path("fixtures/research_quality/manifest.json")
MIN_DOCUMENT_COUNT = 10
MIN_CANDIDATE_COUNT = 40

ACCEPTED = "accepted"
REJECTED = "rejected"

VALID_SCOPED_FINDING_SLICE = "valid_scoped_finding"
REQUIRED_NEGATIVE_SLICES = frozenset(
    {
        "bibliography_reference_text",
        "navigation",
        "access_challenge_bot_page",
        "redirect_shell",
        "methods_presented_as_findings",
        "cited_background",
        "unsupported_generalization",
        "quote_claim_mismatch",
    }
)
REQUIRED_SLICES = frozenset({VALID_SCOPED_FINDING_SLICE, *REQUIRED_NEGATIVE_SLICES})

Predictor = Callable[[Mapping[str, Any], str], "CandidateDecision"]


class BenchmarkContractError(ValueError):
    """Raised when a benchmark manifest or fixture violates the corpus contract."""


@dataclass(frozen=True)
class CandidateDecision:
    """One deterministic admission decision."""

    decision: str
    reason_code: str

    def __post_init__(self) -> None:
        if self.decision not in {ACCEPTED, REJECTED}:
            raise BenchmarkContractError(
                f"decision must be {ACCEPTED!r} or {REJECTED!r}"
            )
        if not self.reason_code.strip():
            raise BenchmarkContractError("reason_code must be non-empty")


@dataclass(frozen=True)
class BenchmarkCorpus:
    """Validated manifest plus in-memory document text."""

    manifest: dict[str, Any]
    documents: dict[str, str]
    manifest_path: Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_manifest_path(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_MANIFEST_REL


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkContractError(f"{label} must be a non-empty string")
    return value.strip()


def _safe_fixture_path(base_dir: Path, relative_value: object, *, label: str) -> Path:
    relative = Path(_require_string(relative_value, label=label))
    if relative.is_absolute() or ".." in relative.parts:
        raise BenchmarkContractError(f"{label} must stay inside the fixture directory")
    base = base_dir.resolve()
    resolved = (base / relative).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise BenchmarkContractError(
            f"{label} must stay inside the fixture directory"
        ) from exc
    return resolved


def _validate_document(
    document: Mapping[str, Any],
    *,
    base_dir: Path,
) -> tuple[str, str]:
    document_id = _require_string(document.get("id"), label="document.id")
    fixture_path = _safe_fixture_path(
        base_dir,
        document.get("path"),
        label=f"document[{document_id}].path",
    )
    if not fixture_path.is_file():
        raise BenchmarkContractError(
            f"document[{document_id}] fixture is missing: {document.get('path')!r}"
        )

    expected_checksum = _require_string(
        document.get("checksum_sha256"),
        label=f"document[{document_id}].checksum_sha256",
    ).casefold()
    actual_checksum = _sha256(fixture_path)
    if expected_checksum != actual_checksum:
        raise BenchmarkContractError(
            f"document[{document_id}] checksum mismatch: "
            f"expected {expected_checksum}, got {actual_checksum}"
        )

    text = fixture_path.read_text(encoding="utf-8")
    boundaries = document.get("excerpt_boundaries")
    if not isinstance(boundaries, Mapping):
        raise BenchmarkContractError(
            f"document[{document_id}].excerpt_boundaries must be an object"
        )
    start = boundaries.get("start_char")
    end = boundaries.get("end_char")
    if (
        not isinstance(start, int)
        or isinstance(start, bool)
        or not isinstance(end, int)
        or isinstance(end, bool)
        or start < 0
        or end <= start
        or end > len(text)
    ):
        raise BenchmarkContractError(
            f"document[{document_id}] excerpt boundaries are outside the fixture"
        )

    synthetic = document.get("synthetic")
    if not isinstance(synthetic, bool):
        raise BenchmarkContractError(
            f"document[{document_id}].synthetic must be a boolean"
        )
    _require_string(document.get("license"), label=f"document[{document_id}].license")
    identifier = document.get("canonical_url") or document.get("canonical_identifier")
    _require_string(identifier, label=f"document[{document_id}].canonical_identifier")

    if not synthetic:
        _require_string(
            document.get("license"),
            label=f"non-synthetic document[{document_id}].license",
        )
        _require_string(
            identifier,
            label=f"non-synthetic document[{document_id}].canonical source",
        )

    return document_id, text[start:end]


def validate_manifest(
    manifest: Mapping[str, Any],
    *,
    base_dir: Path,
) -> dict[str, str]:
    """Validate a parsed manifest and return bounded document text by ID."""
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise BenchmarkContractError(
            f"schema_version must be {MANIFEST_SCHEMA_VERSION!r}"
        )
    _require_string(manifest.get("benchmark_id"), label="benchmark_id")
    _require_string(manifest.get("benchmark_version"), label="benchmark_version")

    documents = manifest.get("documents")
    if not isinstance(documents, list) or len(documents) < MIN_DOCUMENT_COUNT:
        raise BenchmarkContractError(
            f"manifest requires at least {MIN_DOCUMENT_COUNT} documents"
        )

    document_text: dict[str, str] = {}
    for document in documents:
        if not isinstance(document, Mapping):
            raise BenchmarkContractError("each document entry must be an object")
        document_id, text = _validate_document(document, base_dir=base_dir)
        if document_id in document_text:
            raise BenchmarkContractError(f"duplicate document id: {document_id}")
        document_text[document_id] = text

    candidates = manifest.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < MIN_CANDIDATE_COUNT:
        raise BenchmarkContractError(
            f"manifest requires at least {MIN_CANDIDATE_COUNT} candidate decisions"
        )

    candidate_ids: set[str] = set()
    observed_slices: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise BenchmarkContractError("each candidate entry must be an object")
        candidate_id = _require_string(candidate.get("id"), label="candidate.id")
        if candidate_id in candidate_ids:
            raise BenchmarkContractError(f"duplicate candidate id: {candidate_id}")
        candidate_ids.add(candidate_id)

        document_id = _require_string(
            candidate.get("document_id"),
            label=f"candidate[{candidate_id}].document_id",
        )
        if document_id not in document_text:
            raise BenchmarkContractError(
                f"candidate[{candidate_id}] references unknown document {document_id!r}"
            )

        slice_id = _require_string(
            candidate.get("slice"),
            label=f"candidate[{candidate_id}].slice",
        )
        observed_slices.add(slice_id)
        _require_string(
            candidate.get("claim_text"),
            label=f"candidate[{candidate_id}].claim_text",
        )
        quote_span = _require_string(
            candidate.get("quote_span"),
            label=f"candidate[{candidate_id}].quote_span",
        )
        _require_string(
            candidate.get("scope"),
            label=f"candidate[{candidate_id}].scope",
        )
        if _collapse_whitespace(quote_span) not in _collapse_whitespace(
            document_text[document_id]
        ):
            raise BenchmarkContractError(
                f"candidate[{candidate_id}] quote_span is not present in its fixture"
            )

        expected = candidate.get("expected_decision")
        if expected not in {ACCEPTED, REJECTED}:
            raise BenchmarkContractError(
                f"candidate[{candidate_id}].expected_decision is invalid"
            )
        reason = candidate.get("expected_reason_code")
        if expected == ACCEPTED and reason not in {None, ACCEPTED}:
            raise BenchmarkContractError(
                f"candidate[{candidate_id}] accepted annotation cannot have "
                "a rejection reason"
            )
        if expected == REJECTED:
            _require_string(
                reason,
                label=f"candidate[{candidate_id}].expected_reason_code",
            )

    missing_slices = REQUIRED_SLICES - observed_slices
    if missing_slices:
        raise BenchmarkContractError(
            "manifest is missing required slices: " + ", ".join(sorted(missing_slices))
        )

    declared_slices = manifest.get("required_slices")
    if not isinstance(declared_slices, list):
        raise BenchmarkContractError("required_slices must be a list")
    missing_declarations = REQUIRED_SLICES - {
        str(value) for value in declared_slices if isinstance(value, str)
    }
    if missing_declarations:
        raise BenchmarkContractError(
            "required_slices omits contract slices: "
            + ", ".join(sorted(missing_declarations))
        )

    baseline = manifest.get("baseline")
    if not isinstance(baseline, Mapping):
        raise BenchmarkContractError("baseline must be an object")
    if baseline.get("predictor_id") != QUOTE_PRESENCE_BASELINE_ID:
        raise BenchmarkContractError(
            f"baseline.predictor_id must be {QUOTE_PRESENCE_BASELINE_ID!r}"
        )
    thresholds = baseline.get("thresholds")
    if not isinstance(thresholds, Mapping):
        raise BenchmarkContractError("baseline.thresholds must be an object")
    for key in (
        "precision_min",
        "recall_min",
        "false_acceptance_rate_max",
    ):
        value = thresholds.get(key)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not 0.0 <= float(value) <= 1.0
        ):
            raise BenchmarkContractError(f"baseline.thresholds.{key} must be 0..1")

    return document_text


def load_benchmark_corpus(
    manifest_path: Path | str | None = None,
    *,
    root: Path | None = None,
) -> BenchmarkCorpus:
    """Load and validate the committed benchmark corpus without writing files."""
    resolved = Path(manifest_path) if manifest_path is not None else default_manifest_path(root=root)
    if not resolved.is_absolute():
        resolved = (root or repo_root()) / resolved
    resolved = resolved.resolve()
    if not resolved.is_file():
        raise BenchmarkContractError(f"manifest does not exist: {resolved}")
    try:
        raw = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BenchmarkContractError(f"manifest is invalid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise BenchmarkContractError("manifest root must be an object")
    documents = validate_manifest(raw, base_dir=resolved.parent)
    return BenchmarkCorpus(
        manifest=raw,
        documents=documents,
        manifest_path=resolved,
    )


def quote_presence_baseline(
    candidate: Mapping[str, Any],
    document_text: str,
) -> CandidateDecision:
    """Weak baseline: accept when a quote and basic claim fields are present."""
    for field in ("claim_text", "scope"):
        value = candidate.get(field)
        if not isinstance(value, str) or not value.strip():
            return CandidateDecision(REJECTED, "invalid_candidate")
    quote = candidate.get("quote_span")
    if not isinstance(quote, str) or not quote.strip():
        return CandidateDecision(REJECTED, "missing_quote_span")
    if _collapse_whitespace(quote) not in _collapse_whitespace(document_text):
        return CandidateDecision(REJECTED, "quote_not_found")
    return CandidateDecision(ACCEPTED, ACCEPTED)


def _empty_counts() -> dict[str, int]:
    return {
        "total": 0,
        "expected_accepted": 0,
        "expected_rejected": 0,
        "predicted_accepted": 0,
        "predicted_rejected": 0,
        "true_positive": 0,
        "false_positive": 0,
        "false_negative": 0,
        "true_negative": 0,
    }


def _add_record(counts: dict[str, int], record: Mapping[str, Any]) -> None:
    expected = str(record["expected_decision"])
    predicted = str(record["predicted_decision"])
    counts["total"] += 1
    counts[f"expected_{expected}"] += 1
    counts[f"predicted_{predicted}"] += 1
    if expected == ACCEPTED and predicted == ACCEPTED:
        counts["true_positive"] += 1
    elif expected == REJECTED and predicted == ACCEPTED:
        counts["false_positive"] += 1
    elif expected == ACCEPTED and predicted == REJECTED:
        counts["false_negative"] += 1
    else:
        counts["true_negative"] += 1


def _metric(numerator: int, denominator: int) -> dict[str, int | float]:
    value = round(numerator / denominator, 6) if denominator else 0.0
    return {
        "value": value,
        "numerator": numerator,
        "denominator": denominator,
    }


def _metrics_from_counts(counts: Mapping[str, int]) -> dict[str, dict[str, int | float]]:
    true_positive = int(counts["true_positive"])
    false_positive = int(counts["false_positive"])
    false_negative = int(counts["false_negative"])
    true_negative = int(counts["true_negative"])
    return {
        "precision": _metric(true_positive, true_positive + false_positive),
        "recall": _metric(true_positive, true_positive + false_negative),
        "f1": _metric(
            2 * true_positive,
            (2 * true_positive) + false_positive + false_negative,
        ),
        "false_acceptance_rate": _metric(
            false_positive,
            false_positive + true_negative,
        ),
    }


def summarize_decisions(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Calculate aggregate, per-slice, and reason-code confusion metrics."""
    if not records:
        raise BenchmarkContractError("at least one decision record is required")

    counts = _empty_counts()
    per_slice_counts: dict[str, dict[str, int]] = {}
    reason_confusion: dict[str, dict[str, int]] = {}

    for index, record in enumerate(records):
        expected = record.get("expected_decision")
        predicted = record.get("predicted_decision")
        if expected not in {ACCEPTED, REJECTED} or predicted not in {ACCEPTED, REJECTED}:
            raise BenchmarkContractError(f"decision record {index} has invalid labels")
        slice_id = _require_string(record.get("slice"), label=f"record[{index}].slice")
        expected_reason = str(record.get("expected_reason_code") or ACCEPTED)
        predicted_reason = str(record.get("predicted_reason_code") or predicted)

        _add_record(counts, record)
        slice_counts = per_slice_counts.setdefault(slice_id, _empty_counts())
        _add_record(slice_counts, record)
        reason_bucket = reason_confusion.setdefault(expected_reason, {})
        reason_bucket[predicted_reason] = reason_bucket.get(predicted_reason, 0) + 1

    per_slice = {
        slice_id: {
            "counts": slice_counts,
            "metrics": _metrics_from_counts(slice_counts),
        }
        for slice_id, slice_counts in sorted(per_slice_counts.items())
    }
    normalized_confusion = {
        expected: dict(sorted(predicted.items()))
        for expected, predicted in sorted(reason_confusion.items())
    }
    return {
        "counts": counts,
        "metrics": _metrics_from_counts(counts),
        "per_slice": per_slice,
        "reason_code_confusion": normalized_confusion,
    }


def _evaluate_thresholds(
    metrics: Mapping[str, Mapping[str, int | float]],
    thresholds: Mapping[str, Any],
) -> dict[str, Any]:
    precision = float(metrics["precision"]["value"])
    recall = float(metrics["recall"]["value"])
    false_acceptance_rate = float(metrics["false_acceptance_rate"]["value"])
    checks = {
        "precision": {
            "value": precision,
            "operator": ">=",
            "target": float(thresholds["precision_min"]),
            "passed": precision >= float(thresholds["precision_min"]),
        },
        "recall": {
            "value": recall,
            "operator": ">=",
            "target": float(thresholds["recall_min"]),
            "passed": recall >= float(thresholds["recall_min"]),
        },
        "false_acceptance_rate": {
            "value": false_acceptance_rate,
            "operator": "<=",
            "target": float(thresholds["false_acceptance_rate_max"]),
            "passed": false_acceptance_rate
            <= float(thresholds["false_acceptance_rate_max"]),
        },
    }
    passed_count = sum(1 for check in checks.values() if check["passed"])
    if passed_count == len(checks):
        verdict = "GO"
    elif passed_count:
        verdict = "PARTIAL"
    else:
        verdict = "NO-GO"
    return {
        "verdict": verdict,
        "passed_count": passed_count,
        "check_count": len(checks),
        "checks": checks,
    }


def evaluate_benchmark(
    manifest_path: Path | str | None = None,
    *,
    root: Path | None = None,
    predictor: Predictor = quote_presence_baseline,
    predictor_id: str = QUOTE_PRESENCE_BASELINE_ID,
) -> dict[str, Any]:
    """Evaluate all annotations and return a deterministic, JSON-safe artifact."""
    corpus = load_benchmark_corpus(manifest_path, root=root)
    candidates = corpus.manifest["candidates"]
    records: list[dict[str, Any]] = []

    for candidate in candidates:
        document_id = str(candidate["document_id"])
        prediction = predictor(candidate, corpus.documents[document_id])
        if not isinstance(prediction, CandidateDecision):
            raise BenchmarkContractError(
                "predictor must return CandidateDecision instances"
            )
        expected_reason = candidate.get("expected_reason_code") or ACCEPTED
        records.append(
            {
                "candidate_id": candidate["id"],
                "document_id": document_id,
                "slice": candidate["slice"],
                "expected_decision": candidate["expected_decision"],
                "predicted_decision": prediction.decision,
                "expected_reason_code": expected_reason,
                "predicted_reason_code": prediction.reason_code,
                "correct": candidate["expected_decision"] == prediction.decision,
            }
        )

    summary = summarize_decisions(records)
    baseline = corpus.manifest["baseline"]
    threshold_evaluation = _evaluate_thresholds(
        summary["metrics"],
        baseline["thresholds"],
    )
    documents = corpus.manifest["documents"]
    false_acceptance_slices = sorted(
        slice_id
        for slice_id, slice_result in summary["per_slice"].items()
        if slice_result["counts"]["false_positive"] > 0
    )

    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "benchmark_id": corpus.manifest["benchmark_id"],
        "benchmark_version": corpus.manifest["benchmark_version"],
        "predictor_id": predictor_id,
        "status": "completed",
        "quality_verdict": threshold_evaluation["verdict"],
        "corpus": {
            "document_count": len(documents),
            "candidate_count": len(candidates),
            "synthetic_document_count": sum(
                1 for document in documents if document["synthetic"]
            ),
            "non_synthetic_document_count": sum(
                1 for document in documents if not document["synthetic"]
            ),
            "slice_count": len(summary["per_slice"]),
        },
        "counts": summary["counts"],
        "metrics": summary["metrics"],
        "per_slice": summary["per_slice"],
        "reason_code_confusion": summary["reason_code_confusion"],
        "threshold_evaluation": threshold_evaluation,
        "false_acceptance_slices": false_acceptance_slices,
        "candidate_results": records,
        "limitations": list(corpus.manifest.get("limitations") or []),
        "execution": {
            "deterministic": True,
            "model_calls": 0,
            "network_calls": 0,
            "database_writes": 0,
            "public_export_writes": 0,
        },
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the deterministic research-quality claim-admission benchmark."
        )
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST_REL),
        help="Benchmark manifest path (default: fixtures/research_quality/manifest.json).",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of indented JSON.",
    )
    args = parser.parse_args(argv)
    result = evaluate_benchmark(args.manifest)
    print(
        json.dumps(
            result,
            indent=None if args.compact else 2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through module CLI tests
    raise SystemExit(main())
