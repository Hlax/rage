"""Deterministic grounding checks for synthesis output sentences."""

from __future__ import annotations

from typing import Any

from rge.contracts.synthesis_evidence_packet_v0 import (
    atom_text_by_id,
    claim_text_by_id,
    significant_tokens,
)


def _overlap_count(sentence: str, grounding_text: str) -> int:
    sentence_tokens = significant_tokens(sentence)
    grounding_tokens = significant_tokens(grounding_text)
    if not sentence_tokens or not grounding_tokens:
        return 0
    return len(sentence_tokens & grounding_tokens)


def evaluate_synthesis_grounding(
    output: dict[str, Any],
    *,
    packet: dict[str, Any],
    min_overlap: int = 1,
) -> dict[str, Any]:
    claim_texts = claim_text_by_id(packet)
    atom_texts = atom_text_by_id(packet)
    sentence_results: list[dict[str, Any]] = []
    flagged_sentences: list[dict[str, Any]] = []
    needs_human_review = False

    for index, sentence in enumerate(output.get("summary_sentences") or []):
        if not isinstance(sentence, dict):
            continue
        text = str(sentence.get("text") or "").strip()
        issues: list[str] = []
        min_count = 0
        grounded = True

        for claim_id in sentence.get("claim_ids") or []:
            claim_text = claim_texts.get(str(claim_id), "")
            overlap = _overlap_count(text, claim_text)
            min_count = min(min_count, overlap) if issues else overlap
            if overlap < min_overlap:
                grounded = False
                issues.append(
                    f"sentence text does not overlap claim_id {claim_id} grounding text"
                )

        for atom_id in sentence.get("atom_ids") or []:
            atom_text = atom_texts.get(str(atom_id), "")
            overlap = _overlap_count(text, atom_text)
            if overlap < min_overlap:
                grounded = False
                issues.append(
                    f"sentence text does not overlap atom_id {atom_id} grounding text"
                )

        row = {
            "index": index,
            "text": text,
            "cited_claim_refs": list(sentence.get("claim_ids") or []),
            "cited_atom_refs": list(sentence.get("atom_ids") or []),
            "cited_source_refs": list(sentence.get("source_refs") or []),
            "issues": issues,
            "min_overlap_count": min_count if issues else max(min_overlap, 1),
            "grounded": grounded,
        }
        sentence_results.append(row)
        if not grounded:
            needs_human_review = True
            flagged_sentences.append(row)

    return {
        "needs_human_review": needs_human_review,
        "sentence_results": sentence_results,
        "flagged_sentences": flagged_sentences,
        "grounding_passed": not needs_human_review,
    }
