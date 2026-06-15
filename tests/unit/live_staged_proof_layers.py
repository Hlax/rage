"""Three-layer live staged proof helpers (ticket-234).

Layer 1 — live source acquisition: OpenAlex discover + top-N fetch succeeds.
Layer 2 — deterministic mock-spine: fixture-backed network-free tests elsewhere.
Layer 3 — optional combined live proof: proceeds only when fetched artifact
          satisfies mock-spine preconditions; otherwise skips with
          ``unsuitable_live_artifact`` (not a fetch/reconcile/report regression).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from rge.cli import main
from tests.unit.live_staged_candidates import (
    MOCK_STAGED_ARTIFACT_MARKERS,
    artifact_missing_markers,
    fetch_first_fetchable_staged_candidate,
    list_top_staged_candidate_ids,
)
from rge.modules.fetcher import run_fetch_candidate_command

LIVE_DISCOVER_QUERY = "human AI creativity"
UNSUITABLE_LIVE_ARTIFACT = "unsuitable_live_artifact"


def run_live_openalex_discover(
    temp_db: Path,
    research_question_id: str,
    *,
    query: str = LIVE_DISCOVER_QUERY,
) -> None:
    """Layer-1 prerequisite: enqueue real OpenAlex candidates."""
    assert (
        main(
            [
                "discover-sources",
                "--provider",
                "openalex",
                "--query",
                query,
                "--rank-only",
                "--enqueue",
                "--question",
                research_question_id,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )


def run_live_source_acquisition(
    conn: Any,
    *,
    research_question_id: str,
    staging_dir: Path,
    max_candidates: int = 10,
    urlopen: Any | None = None,
) -> tuple[str, dict[str, Any]]:
    """Layer 1: fetch first successful top-N candidate (no mock-spine coupling)."""
    return fetch_first_fetchable_staged_candidate(
        conn,
        research_question_id=research_question_id,
        staging_dir=staging_dir,
        max_candidates=max_candidates,
        urlopen=urlopen,
    )


def evaluate_mock_spine_compatibility(
    fetch_payload: dict[str, Any],
    artifact_text_markers: tuple[str, ...],
) -> dict[str, Any]:
    """Return structured compatibility diagnostics for one fetched artifact."""
    artifact_path_raw = fetch_payload.get("artifact_path")
    if not artifact_path_raw:
        return {
            "compatible": False,
            "reason": UNSUITABLE_LIVE_ARTIFACT,
            "detail": "Fetch payload missing artifact_path.",
            "required_markers": list(artifact_text_markers),
            "missing_markers": list(artifact_text_markers),
        }

    artifact_path = Path(str(artifact_path_raw))
    if not artifact_path.is_file():
        return {
            "compatible": False,
            "reason": UNSUITABLE_LIVE_ARTIFACT,
            "detail": f"Fetched artifact file not found: {artifact_path}",
            "required_markers": list(artifact_text_markers),
            "missing_markers": list(artifact_text_markers),
        }

    missing_markers = artifact_missing_markers(artifact_path, artifact_text_markers)
    if missing_markers:
        return {
            "compatible": False,
            "reason": UNSUITABLE_LIVE_ARTIFACT,
            "detail": (
                "Fetched live artifact is fetchable but lacks mock-spine marker phrases."
            ),
            "required_markers": list(artifact_text_markers),
            "missing_markers": missing_markers,
            "artifact_path": str(artifact_path),
            "selected_url_kind": fetch_payload.get("selected_url_kind"),
        }

    return {
        "compatible": True,
        "reason": "compatible",
        "detail": "Artifact contains all required mock-spine markers.",
        "required_markers": list(artifact_text_markers),
        "missing_markers": [],
        "artifact_path": str(artifact_path),
        "selected_url_kind": fetch_payload.get("selected_url_kind"),
    }


def _fetch_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "url": payload.get("url"),
        "selected_url_kind": payload.get("selected_url_kind"),
        "artifact_path": payload.get("artifact_path"),
        "attempted_urls": payload.get("attempted_urls", []),
    }


def format_unsuitable_live_artifact_skip(
    *,
    research_question_id: str,
    required_markers: tuple[str, ...],
    unsuitable_candidates: list[dict[str, Any]],
    fetch_failures: list[dict[str, Any]],
) -> str:
    """Machine-readable skip reason for layer-3 combined proofs."""
    body = {
        "proof_layer": "combined_live_mock_spine",
        "reason": UNSUITABLE_LIVE_ARTIFACT,
        "detail": (
            "Live source acquisition succeeded for one or more candidates, but none "
            "of the fetched top-N artifacts satisfy mock-spine marker preconditions."
        ),
        "research_question_id": research_question_id,
        "required_markers": list(required_markers),
        "fetch_failures": fetch_failures,
        "unsuitable_candidates": unsuitable_candidates,
        "assessment": (
            "Not a fetch/reconcile/report regression — live OpenAlex catalog text "
            "does not match checksum-pinned mock fixture phrases for this query."
        ),
    }
    return json.dumps(body, indent=2)


def require_mock_spine_compatible_fetch_or_skip(
    conn: Any,
    *,
    research_question_id: str,
    staging_dir: Path,
    artifact_text_markers: tuple[str, ...],
    max_candidates: int = 10,
    urlopen: Any | None = None,
) -> tuple[str, dict[str, Any]]:
    """Layer 3: return first fetchable+compatible candidate or skip clearly."""
    candidate_ids = list_top_staged_candidate_ids(
        conn,
        research_question_id,
        max_candidates=max_candidates,
    )
    assert candidate_ids, (
        f"live discover must enqueue at least one candidate for {research_question_id}"
    )

    fetch_failures: list[dict[str, Any]] = []
    unsuitable_candidates: list[dict[str, Any]] = []

    for candidate_id in candidate_ids:
        payload, exit_code = run_fetch_candidate_command(
            conn,
            candidate_id=candidate_id,
            output_dir=staging_dir,
            urlopen=urlopen,
        )
        if exit_code != 0 or payload.get("status") not in {
            "completed",
            "already_fetched",
        }:
            fetch_failures.append(
                {
                    "candidate_id": candidate_id,
                    "exit_code": exit_code,
                    "reason": payload.get("reason"),
                    "detail": payload.get("detail"),
                    "attempted_urls": payload.get("attempted_urls", []),
                }
            )
            continue

        compatibility = evaluate_mock_spine_compatibility(
            payload,
            artifact_text_markers,
        )
        if compatibility["compatible"]:
            return candidate_id, payload

        unsuitable_candidates.append(
            {
                "candidate_id": candidate_id,
                "fetch": _fetch_summary(payload),
                **compatibility,
            }
        )

    if unsuitable_candidates:
        pytest.skip(
            format_unsuitable_live_artifact_skip(
                research_question_id=research_question_id,
                required_markers=artifact_text_markers,
                unsuitable_candidates=unsuitable_candidates,
                fetch_failures=fetch_failures,
            )
        )

    failure_summary = "; ".join(
        f"{item['candidate_id']}:{item.get('reason')}" for item in fetch_failures[:5]
    )
    raise AssertionError(
        "live source acquisition failed for all top "
        f"{max_candidates} candidates for {research_question_id}; "
        f"failures: {failure_summary}"
    )
