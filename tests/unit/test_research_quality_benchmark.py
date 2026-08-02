"""Deterministic research-quality benchmark contract and baseline tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from rge.modules.research_quality_benchmark import (
    ACCEPTED,
    REJECTED,
    REQUIRED_NEGATIVE_SLICES,
    REQUIRED_SLICES,
    BenchmarkContractError,
    CandidateDecision,
    canonical_text_sha256,
    canonicalize_fixture_text,
    evaluate_benchmark,
    load_benchmark_corpus,
    main,
    summarize_decisions,
    validate_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "fixtures" / "research_quality" / "manifest.json"


def test_manifest_is_versioned_domain_neutral_and_provenanced() -> None:
    corpus = load_benchmark_corpus(MANIFEST_PATH)
    manifest = corpus.manifest

    assert manifest["schema_version"] == "research_quality_benchmark_manifest_v1"
    assert manifest["benchmark_version"] == "1.0.0"
    assert manifest["checksum_contract"] == {
        "id": "sha256_utf8_lf_v1",
        "algorithm": "sha256",
        "encoding": "utf-8",
        "newline_normalization": "lf",
        "description": (
            "Decode as UTF-8, normalize CRLF and bare CR to LF, then hash the "
            "bounded canonical text."
        ),
    }
    assert len(manifest["documents"]) == 10
    assert len(manifest["candidates"]) == 40
    assert set(manifest["required_slices"]) >= REQUIRED_SLICES
    assert {candidate["slice"] for candidate in manifest["candidates"]} >= REQUIRED_SLICES

    for document in manifest["documents"]:
        assert document["synthetic"] is True
        assert document["license"] == "synthetic_fixture"
        assert document["canonical_identifier"].startswith("synthetic:rge:")
        fixture = MANIFEST_PATH.parent / document["path"]
        assert fixture.is_file()
        text = canonicalize_fixture_text(fixture.read_text(encoding="utf-8"))
        assert canonical_text_sha256(text) == document["checksum_sha256"]
        boundaries = document["excerpt_boundaries"]
        assert boundaries["start_char"] == 0
        assert boundaries["end_char"] == len(fixture.read_text(encoding="utf-8"))


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_manifest_checksums_are_portable_across_newline_styles(
    tmp_path: Path,
    newline: str,
) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for document in manifest["documents"]:
        source = MANIFEST_PATH.parent / document["path"]
        canonical = canonicalize_fixture_text(source.read_text(encoding="utf-8"))
        destination = tmp_path / document["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical.replace("\n", newline).encode("utf-8"))

    documents = validate_manifest(manifest, base_dir=tmp_path)

    assert len(documents) == 10
    assert all("\r" not in text for text in documents.values())


def test_manifest_checksum_rejects_substantive_change_with_crlf(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for document in manifest["documents"]:
        source = MANIFEST_PATH.parent / document["path"]
        canonical = canonicalize_fixture_text(source.read_text(encoding="utf-8"))
        if document["id"] == "doc-clinical-trial":
            canonical = canonical.replace("Eighty adults", "Ninety adults", 1)
        destination = tmp_path / document["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical.replace("\n", "\r\n").encode("utf-8"))

    with pytest.raises(BenchmarkContractError, match="checksum mismatch"):
        validate_manifest(manifest, base_dir=tmp_path)


def test_quote_presence_baseline_reproduces_known_false_acceptances() -> None:
    artifact = evaluate_benchmark(MANIFEST_PATH)

    assert artifact["status"] == "completed"
    assert artifact["quality_verdict"] == "PARTIAL"
    assert artifact["corpus"] == {
        "document_count": 10,
        "candidate_count": 40,
        "synthetic_document_count": 10,
        "non_synthetic_document_count": 0,
        "slice_count": 9,
    }
    assert artifact["counts"] == {
        "total": 40,
        "expected_accepted": 12,
        "expected_rejected": 28,
        "predicted_accepted": 40,
        "predicted_rejected": 0,
        "true_positive": 12,
        "false_positive": 28,
        "false_negative": 0,
        "true_negative": 0,
    }
    assert artifact["metrics"] == {
        "precision": {"value": 0.3, "numerator": 12, "denominator": 40},
        "recall": {"value": 1.0, "numerator": 12, "denominator": 12},
        "f1": {"value": 0.461538, "numerator": 24, "denominator": 52},
        "false_acceptance_rate": {
            "value": 1.0,
            "numerator": 28,
            "denominator": 28,
        },
    }
    assert set(artifact["false_acceptance_slices"]) == REQUIRED_NEGATIVE_SLICES

    for slice_id in REQUIRED_NEGATIVE_SLICES:
        counts = artifact["per_slice"][slice_id]["counts"]
        assert counts["expected_rejected"] >= 1
        assert counts["false_positive"] == counts["expected_rejected"]
        assert artifact["reason_code_confusion"][slice_id] == {
            ACCEPTED: counts["expected_rejected"]
        }

    checks = artifact["threshold_evaluation"]["checks"]
    assert checks["precision"]["passed"] is False
    assert checks["recall"]["passed"] is True
    assert checks["false_acceptance_rate"]["passed"] is False


def test_metric_math_and_reason_confusion_use_raw_counts() -> None:
    records = [
        {
            "slice": "valid",
            "expected_decision": ACCEPTED,
            "predicted_decision": ACCEPTED,
            "expected_reason_code": ACCEPTED,
            "predicted_reason_code": ACCEPTED,
        },
        {
            "slice": "valid",
            "expected_decision": ACCEPTED,
            "predicted_decision": ACCEPTED,
            "expected_reason_code": ACCEPTED,
            "predicted_reason_code": ACCEPTED,
        },
        {
            "slice": "navigation",
            "expected_decision": REJECTED,
            "predicted_decision": ACCEPTED,
            "expected_reason_code": "navigation",
            "predicted_reason_code": ACCEPTED,
        },
        {
            "slice": "valid",
            "expected_decision": ACCEPTED,
            "predicted_decision": REJECTED,
            "expected_reason_code": ACCEPTED,
            "predicted_reason_code": "quote_not_found",
        },
        {
            "slice": "redirect",
            "expected_decision": REJECTED,
            "predicted_decision": REJECTED,
            "expected_reason_code": "redirect_shell",
            "predicted_reason_code": "redirect_shell",
        },
        {
            "slice": "references",
            "expected_decision": REJECTED,
            "predicted_decision": REJECTED,
            "expected_reason_code": "bibliography_reference_text",
            "predicted_reason_code": "source_artifact",
        },
    ]

    summary = summarize_decisions(records)

    assert summary["counts"]["true_positive"] == 2
    assert summary["counts"]["false_positive"] == 1
    assert summary["counts"]["false_negative"] == 1
    assert summary["counts"]["true_negative"] == 2
    assert summary["metrics"] == {
        "precision": {"value": 0.666667, "numerator": 2, "denominator": 3},
        "recall": {"value": 0.666667, "numerator": 2, "denominator": 3},
        "f1": {"value": 0.666667, "numerator": 4, "denominator": 6},
        "false_acceptance_rate": {
            "value": 0.333333,
            "numerator": 1,
            "denominator": 3,
        },
    }
    assert summary["reason_code_confusion"][ACCEPTED] == {
        ACCEPTED: 2,
        "quote_not_found": 1,
    }
    assert summary["per_slice"]["navigation"]["counts"]["false_positive"] == 1
    assert summary["per_slice"]["references"]["counts"]["true_negative"] == 1


def test_manifest_rejects_checksum_tampering_and_path_escape() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    bad_checksum = copy.deepcopy(manifest)
    bad_checksum["documents"][0]["checksum_sha256"] = "0" * 64
    with pytest.raises(BenchmarkContractError, match="checksum mismatch"):
        validate_manifest(bad_checksum, base_dir=MANIFEST_PATH.parent)

    escaped_path = copy.deepcopy(manifest)
    escaped_path["documents"][0]["path"] = "../outside.txt"
    with pytest.raises(BenchmarkContractError, match="inside the fixture directory"):
        validate_manifest(escaped_path, base_dir=MANIFEST_PATH.parent)


def test_non_synthetic_document_requires_license_and_canonical_source() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    document = manifest["documents"][0]
    document["synthetic"] = False
    document["license"] = ""
    document["canonical_identifier"] = ""

    with pytest.raises(BenchmarkContractError, match="license"):
        validate_manifest(manifest, base_dir=MANIFEST_PATH.parent)


def test_evaluator_is_read_only_and_has_no_live_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_write(*_args: object, **_kwargs: object) -> int:
        raise AssertionError("benchmark attempted a filesystem write")

    monkeypatch.setattr(Path, "write_text", fail_write)
    monkeypatch.setattr(Path, "write_bytes", fail_write)

    artifact = evaluate_benchmark(MANIFEST_PATH)

    assert artifact["execution"] == {
        "deterministic": True,
        "model_calls": 0,
        "network_calls": 0,
        "database_writes": 0,
        "public_export_writes": 0,
    }


def test_evaluator_requires_typed_predictor_decisions() -> None:
    with pytest.raises(BenchmarkContractError, match="CandidateDecision"):
        evaluate_benchmark(
            MANIFEST_PATH,
            predictor=lambda _candidate, _text: {"decision": ACCEPTED},  # type: ignore[return-value]
        )

    decision = CandidateDecision(REJECTED, "fixture_reason")
    assert decision.decision == REJECTED
    assert decision.reason_code == "fixture_reason"


def test_module_cli_prints_failing_baseline_artifact(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--manifest", str(MANIFEST_PATH), "--compact"]) == 0
    artifact = json.loads(capsys.readouterr().out)
    assert artifact["status"] == "completed"
    assert artifact["quality_verdict"] == "PARTIAL"
    assert artifact["metrics"]["precision"]["numerator"] == 12
    assert artifact["metrics"]["false_acceptance_rate"]["numerator"] == 28
