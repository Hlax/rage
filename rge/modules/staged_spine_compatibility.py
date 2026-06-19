"""Mock-spine artifact compatibility checks for live staged orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rge.modules.fetcher import html_to_text

MOCK_STAGED_RANK1_ARTIFACT_MARKERS = (
    "human-ai co-creativity",
    "songwriting",
)
UNSUITABLE_LIVE_ARTIFACT = "unsuitable_live_artifact"


def artifact_missing_markers(
    artifact_path: Path,
    markers: tuple[str, ...],
) -> list[str]:
    """Return marker phrases absent from artifact text."""
    data = artifact_path.read_bytes()
    if artifact_path.suffix.casefold() == ".html":
        text = html_to_text(data.decode("utf-8", errors="replace"))
    else:
        text = data.decode("utf-8", errors="replace")
    folded = text.casefold()
    return [marker for marker in markers if marker.casefold() not in folded]


def fetch_payload_has_mock_spine_markers(
    payload: dict[str, Any],
    *,
    markers: tuple[str, ...] = MOCK_STAGED_RANK1_ARTIFACT_MARKERS,
) -> bool:
    """Return True when a completed fetch payload artifact contains spine markers."""
    artifact_path_raw = payload.get("artifact_path")
    if not artifact_path_raw:
        return False
    artifact_path = Path(str(artifact_path_raw))
    if not artifact_path.is_file():
        return False
    return not artifact_missing_markers(artifact_path, markers)


def evaluate_mock_spine_compatibility(
    fetch_payload: dict[str, Any],
    *,
    markers: tuple[str, ...] = MOCK_STAGED_RANK1_ARTIFACT_MARKERS,
) -> dict[str, Any]:
    """Return structured compatibility diagnostics for one fetched artifact."""
    artifact_path_raw = fetch_payload.get("artifact_path")
    if not artifact_path_raw:
        return {
            "compatible": False,
            "reason": UNSUITABLE_LIVE_ARTIFACT,
            "detail": "Fetch payload missing artifact_path.",
            "required_markers": list(markers),
            "missing_markers": list(markers),
        }

    artifact_path = Path(str(artifact_path_raw))
    if not artifact_path.is_file():
        return {
            "compatible": False,
            "reason": UNSUITABLE_LIVE_ARTIFACT,
            "detail": f"Fetched artifact file not found: {artifact_path}",
            "required_markers": list(markers),
            "missing_markers": list(markers),
        }

    missing_markers = artifact_missing_markers(artifact_path, markers)
    if missing_markers:
        return {
            "compatible": False,
            "reason": UNSUITABLE_LIVE_ARTIFACT,
            "detail": (
                "Fetched live artifact is fetchable but lacks mock-spine marker phrases."
            ),
            "required_markers": list(markers),
            "missing_markers": missing_markers,
            "artifact_path": str(artifact_path),
            "selected_url_kind": fetch_payload.get("selected_url_kind"),
        }

    return {
        "compatible": True,
        "reason": "compatible",
        "detail": "Artifact contains all required mock-spine markers.",
        "required_markers": list(markers),
        "missing_markers": [],
        "artifact_path": str(artifact_path),
        "selected_url_kind": fetch_payload.get("selected_url_kind"),
    }
