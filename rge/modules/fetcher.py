"""Fetch local files, URLs, PDFs, and metadata. Deterministic; no model use.

All fetched source text is untrusted and may contain prompt injection.
Phase 1: local plain-text files only.
Phase 3: staged candidate URL fetch to gitignored artifact paths (ticket-142).
"""

from __future__ import annotations

import hashlib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from rge.modules.source_network import source_network_enabled

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STAGED_FETCH_DIR = REPO_ROOT / "data" / "sources" / "staged"
FETCH_CANDIDATE_COMMAND = "fetch-candidate"
BLOCKED_EXIT_CODE = 1
ERROR_EXIT_CODE = 1
OK_EXIT_CODE = 0


class FetchError(Exception):
    """Raised when a source cannot be fetched."""


def default_staged_fetch_dir() -> Path:
    """Gitignored staging directory for fetched candidate artifacts."""
    return DEFAULT_STAGED_FETCH_DIR


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extension_for_content_type(content_type: str | None) -> str:
    if not content_type:
        return ".bin"
    lowered = content_type.split(";")[0].strip().casefold()
    if lowered == "text/html":
        return ".html"
    if lowered == "application/pdf":
        return ".pdf"
    if lowered.startswith("text/"):
        return ".txt"
    return ".bin"


def fetch_url_bytes(
    url: str,
    *,
    urlopen: Any | None = None,
    timeout: int = 30,
) -> tuple[bytes, str | None]:
    """Fetch raw bytes and content-type from a URL."""
    opener = urlopen or urllib.request.urlopen
    request = urllib.request.Request(url, headers={"Accept": "*/*"})
    try:
        with opener(request, timeout=timeout) as response:
            body = response.read()
            content_type = response.headers.get("Content-Type")
    except urllib.error.URLError as exc:
        raise FetchError(f"URL fetch failed: {exc.reason or exc}") from exc
    if not body:
        raise FetchError("URL fetch returned empty body.")
    return body, content_type


def staged_artifact_path(
    output_dir: Path,
    candidate_id: str,
    content_type: str | None,
) -> Path:
    extension = extension_for_content_type(content_type)
    safe_id = candidate_id.replace("/", "_").replace(":", "_")
    return output_dir / f"{safe_id}{extension}"


def fetch_staged_candidate_artifact(
    candidate: dict[str, Any],
    *,
    output_dir: Path | None = None,
    urlopen: Any | None = None,
) -> dict[str, Any]:
    """Fetch a staged candidate_sources row URL to a gitignored artifact file."""
    candidate_id = str(candidate.get("id") or "")
    url = candidate.get("url")
    if not candidate_id:
        raise FetchError("Candidate row is missing id.")
    if not url:
        raise FetchError(f"Candidate {candidate_id!r} has no URL to fetch.")

    if not source_network_enabled():
        return {
            "status": "blocked",
            "command": FETCH_CANDIDATE_COMMAND,
            "reason": "source_network_disabled",
            "candidate_id": candidate_id,
            "detail": "URL fetch requires RGE_ALLOW_SOURCE_NETWORK=1.",
        }

    target_dir = output_dir or default_staged_fetch_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    body, content_type = fetch_url_bytes(str(url), urlopen=urlopen)
    checksum = sha256_bytes(body)
    artifact_path = staged_artifact_path(target_dir, candidate_id, content_type)

    if artifact_path.is_file():
        existing_checksum = sha256_bytes(artifact_path.read_bytes())
        if existing_checksum == checksum:
            return {
                "status": "already_fetched",
                "command": FETCH_CANDIDATE_COMMAND,
                "candidate_id": candidate_id,
                "url": url,
                "checksum": checksum,
                "content_type": content_type,
                "artifact_path": str(artifact_path.resolve()),
                "byte_count": len(body),
            }

    artifact_path.write_bytes(body)

    return {
        "status": "completed",
        "command": FETCH_CANDIDATE_COMMAND,
        "candidate_id": candidate_id,
        "url": url,
        "checksum": checksum,
        "content_type": content_type,
        "artifact_path": str(artifact_path.resolve()),
        "byte_count": len(body),
    }


def run_fetch_candidate_command(
    conn: Any,
    *,
    candidate_id: str,
    output_dir: Path | None = None,
    urlopen: Any | None = None,
) -> tuple[dict[str, Any], int]:
    """Load staged candidate and fetch URL bytes to artifact path."""
    from rge.db.repositories import CandidateSourceRepository

    repo = CandidateSourceRepository(conn)
    candidate = repo.get_by_id(candidate_id)
    if candidate is None:
        payload = {
            "status": "error",
            "command": FETCH_CANDIDATE_COMMAND,
            "reason": "candidate_not_found",
            "candidate_id": candidate_id,
            "detail": f"No candidate_sources row for id {candidate_id!r}.",
        }
        return payload, ERROR_EXIT_CODE

    try:
        result = fetch_staged_candidate_artifact(
            candidate,
            output_dir=output_dir,
            urlopen=urlopen,
        )
    except FetchError as exc:
        payload = {
            "status": "error",
            "command": FETCH_CANDIDATE_COMMAND,
            "reason": "fetch_failed",
            "candidate_id": candidate_id,
            "detail": str(exc),
        }
        return payload, ERROR_EXIT_CODE

    if result.get("status") == "blocked":
        return result, BLOCKED_EXIT_CODE
    return result, OK_EXIT_CODE


def fetch_local_text_file(path: Path) -> dict[str, Any]:
    """Read a local plain-text or Markdown file for ingestion.

    Returns a dict with ``raw_text``, ``title``, and ``local_path``.
    Does not set ``source_type``; the ingest CLI decides that. Does not persist.
    """
    resolved = path.resolve()
    if not resolved.is_file():
        raise FetchError(f"Source file not found: {resolved}")

    try:
        raw_text = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise FetchError(f"Unable to read source file: {resolved}") from exc

    if not raw_text.strip():
        raise FetchError(f"Source file is empty: {resolved}")

    return {
        "raw_text": raw_text,
        "title": resolved.name,
        "local_path": resolved,
    }


def fetch_source(queue_item: dict[str, Any]) -> dict[str, Any]:
    """Fetch one queued source. Local text files only in Phase 1."""
    local_path = queue_item.get("local_path")
    if local_path is None:
        raise NotImplementedError(
            "fetcher.fetch_source supports local_path only in Phase 1."
        )
    return fetch_local_text_file(Path(local_path))
