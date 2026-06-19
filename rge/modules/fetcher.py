"""Fetch local files, URLs, PDFs, and metadata. Deterministic; no model use.

All fetched source text is untrusted and may contain prompt injection.
Phase 1: local plain-text files only.
Phase 3: staged candidate URL fetch to gitignored artifact paths (ticket-142).
Ticket-233: ordered OpenAlex URL fallback with structured failure reasons.
"""

from __future__ import annotations

import hashlib
import json
import re
import socket
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from rge.modules.source_network import source_network_enabled
from rge.modules.source_providers.openalex_urls import is_non_oa_url_kind

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STAGED_FETCH_DIR = REPO_ROOT / "data" / "sources" / "staged"
FETCH_CANDIDATE_COMMAND = "fetch-candidate"
INGEST_STAGED_COMMAND = "ingest-staged"
BLOCKED_EXIT_CODE = 1
ERROR_EXIT_CODE = 1
OK_EXIT_CODE = 0
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_RETRYABLE_HTTP_STATUSES = frozenset({401, 403, 406})
_RETRYABLE_ERROR_MARKERS = frozenset({"timed out", "timeout"})
FETCH_ACCESS_BLOCKED_REASONS = frozenset({"forbidden", "paywall_blocked"})


class FetchError(Exception):
    """Raised when a source cannot be fetched."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "fetch_failed",
        http_status: int | None = None,
        attempted_urls: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.http_status = http_status
        self.attempted_urls = attempted_urls or []


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


def parse_url_candidates(candidate: dict[str, Any]) -> list[dict[str, str]]:
    """Load ordered URL routes from a candidate_sources row."""
    raw = candidate.get("url_candidates_json")
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            routes: list[dict[str, str]] = []
            seen: set[str] = set()
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                url = str(item.get("url") or "").strip()
                kind = str(item.get("kind") or "unknown")
                if url and url not in seen:
                    seen.add(url)
                    routes.append({"url": url, "kind": kind})
            if routes:
                return routes

    url = candidate.get("url")
    if url:
        return [{"url": str(url), "kind": "candidate_sources.url"}]
    return []


def _is_retryable_fetch_error(exc: Exception) -> bool:
    if isinstance(exc, FetchError):
        if exc.http_status in _RETRYABLE_HTTP_STATUSES:
            return True
        message = str(exc).casefold()
        return any(marker in message for marker in _RETRYABLE_ERROR_MARKERS)
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in _RETRYABLE_HTTP_STATUSES
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, urllib.error.HTTPError):
            return reason.code in _RETRYABLE_HTTP_STATUSES
        if isinstance(reason, socket.timeout):
            return True
        message = str(reason or exc).casefold()
        return any(marker in message for marker in _RETRYABLE_ERROR_MARKERS)
    message = str(exc).casefold()
    return any(marker in message for marker in _RETRYABLE_ERROR_MARKERS)


def _http_status_from_error(exc: Exception) -> int | None:
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code
    if isinstance(exc, urllib.error.URLError) and isinstance(
        exc.reason, urllib.error.HTTPError
    ):
        return exc.reason.code
    return None


def _attempt_detail(url: str, kind: str, exc: Exception) -> dict[str, Any]:
    status = _http_status_from_error(exc)
    if status is None and isinstance(exc, FetchError):
        status = exc.http_status
    detail = {
        "url": url,
        "kind": kind,
        "error": str(exc),
    }
    if status is not None:
        detail["http_status"] = status
    return detail


def is_fetch_access_blocked(reason: str | None) -> bool:
    """Return True when all URL routes failed with publisher access blocks."""
    return str(reason or "").strip() in FETCH_ACCESS_BLOCKED_REASONS


def classify_fetch_failure(
    attempted_urls: list[dict[str, Any]],
) -> tuple[str, str]:
    """Map attempted URL failures to a structured fetch-candidate reason."""
    if not attempted_urls:
        return "no_fetchable_url", "Candidate has no fetchable URL routes."

    statuses = [
        item["http_status"]
        for item in attempted_urls
        if isinstance(item.get("http_status"), int)
    ]
    if statuses and all(status in {401, 403} for status in statuses):
        if all(is_non_oa_url_kind(str(item.get("kind") or "")) for item in attempted_urls):
            return "paywall_blocked", "All publisher/non-OA URL routes returned 401/403."
        return "forbidden", "All URL routes returned 401/403."

    if statuses and all(status in _RETRYABLE_HTTP_STATUSES for status in statuses):
        return "forbidden", "All URL routes returned retryable HTTP access errors."

    last_error = str(attempted_urls[-1].get("error") or "URL fetch failed.")
    return "fetch_failed", last_error


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
    except urllib.error.HTTPError as exc:
        raise FetchError(
            f"URL fetch failed: HTTP {exc.code}",
            reason="fetch_failed",
            http_status=exc.code,
        ) from exc
    except urllib.error.URLError as exc:
        status = _http_status_from_error(exc)
        detail = exc.reason or exc
        raise FetchError(
            f"URL fetch failed: {detail}",
            reason="fetch_failed",
            http_status=status,
        ) from exc
    if not body:
        raise FetchError("URL fetch returned empty body.")
    return body, content_type


def fetch_url_bytes_with_retry(
    routes: list[dict[str, str]],
    *,
    urlopen: Any | None = None,
    timeout: int = 30,
) -> tuple[bytes, str | None, dict[str, str], list[dict[str, Any]]]:
    """Try ordered URL routes until one succeeds or all fail."""
    if not routes:
        raise FetchError(
            "Candidate has no URL to fetch.",
            reason="no_fetchable_url",
        )

    attempted: list[dict[str, Any]] = []
    for index, route in enumerate(routes):
        url = route["url"]
        kind = route.get("kind") or "unknown"
        try:
            body, content_type = fetch_url_bytes(
                url,
                urlopen=urlopen,
                timeout=timeout,
            )
            return body, content_type, {"url": url, "kind": kind}, attempted
        except FetchError as exc:
            attempted.append(_attempt_detail(url, kind, exc))
            if _is_retryable_fetch_error(exc) and index < len(routes) - 1:
                continue
            reason, detail = classify_fetch_failure(attempted)
            raise FetchError(
                detail,
                reason=reason,
                http_status=exc.http_status,
                attempted_urls=attempted,
            ) from exc
        except Exception as exc:
            attempted.append(_attempt_detail(url, kind, exc))
            if _is_retryable_fetch_error(exc) and index < len(routes) - 1:
                continue
            reason, detail = classify_fetch_failure(attempted)
            raise FetchError(
                detail,
                reason=reason,
                attempted_urls=attempted,
            ) from exc

    reason, detail = classify_fetch_failure(attempted)
    raise FetchError(detail, reason=reason, attempted_urls=attempted)


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
    routes = parse_url_candidates(candidate)
    if not candidate_id:
        raise FetchError("Candidate row is missing id.")
    if not routes:
        raise FetchError(
            f"Candidate {candidate_id!r} has no URL to fetch.",
            reason="no_fetchable_url",
        )

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

    body, content_type, selected_route, attempted_urls = fetch_url_bytes_with_retry(
        routes,
        urlopen=urlopen,
    )
    url = selected_route["url"]
    selected_url_kind = selected_route["kind"]
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
                "selected_url_kind": selected_url_kind,
                "attempted_urls": attempted_urls,
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
        "selected_url_kind": selected_url_kind,
        "attempted_urls": attempted_urls,
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
            "reason": exc.reason,
            "candidate_id": candidate_id,
            "detail": str(exc),
            "attempted_urls": exc.attempted_urls,
        }
        return payload, ERROR_EXIT_CODE

    if result.get("status") == "blocked":
        return result, BLOCKED_EXIT_CODE
    return result, OK_EXIT_CODE


def html_to_text(html: str) -> str:
    """Minimal HTML tag stripping for staged artifact ingestion."""
    without_tags = _HTML_TAG_PATTERN.sub(" ", html)
    return _WHITESPACE_PATTERN.sub(" ", without_tags).strip()


def artifact_bytes_to_text(data: bytes, artifact_path: Path) -> str:
    text = data.decode("utf-8", errors="replace")
    if artifact_path.suffix.casefold() == ".html":
        return html_to_text(text)
    return text.strip()


def resolve_staged_artifact_path(
    *,
    candidate_id: str | None = None,
    artifact_path: Path | None = None,
    staging_dir: Path | None = None,
) -> Path:
    """Resolve a staged artifact file from candidate id or explicit path."""
    if artifact_path is not None:
        resolved = artifact_path.resolve()
        if not resolved.is_file():
            raise FetchError(f"Staged artifact not found: {resolved}")
        return resolved

    if not candidate_id:
        raise FetchError("Either --candidate or --artifact is required.")

    directory = staging_dir or default_staged_fetch_dir()
    if not directory.is_dir():
        raise FetchError(f"Staged artifact directory not found: {directory}")

    safe_id = candidate_id.replace("/", "_").replace(":", "_")
    matches = sorted(directory.glob(f"{safe_id}.*"))
    if not matches:
        raise FetchError(
            f"No staged artifact found for candidate {candidate_id!r} in {directory}."
        )
    return matches[0].resolve()


def ingest_staged_artifact(
    conn: Any,
    *,
    domain: str,
    candidate_id: str | None = None,
    artifact_path: Path | None = None,
    expected_checksum: str | None = None,
    staging_dir: Path | None = None,
    source_type: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Ingest a staged fetch artifact into sources/chunks with checksum verification."""
    from rge.db.repositories import CandidateSourceRepository, ingest_local_source

    path = resolve_staged_artifact_path(
        candidate_id=candidate_id,
        artifact_path=artifact_path,
        staging_dir=staging_dir,
    )
    data = path.read_bytes()
    checksum = sha256_bytes(data)
    if expected_checksum and expected_checksum.casefold() != checksum.casefold():
        raise FetchError(
            f"Checksum mismatch for {path}: expected {expected_checksum}, got {checksum}."
        )

    if candidate_id:
        candidate = CandidateSourceRepository(conn).get_by_id(candidate_id)
        if candidate is not None:
            source_type = source_type or str(candidate.get("source_type") or "")
            title = title or str(candidate.get("title") or "")

    raw_text = artifact_bytes_to_text(data, path)
    if not raw_text.strip():
        raise FetchError(f"Staged artifact produced empty text: {path}")

    effective_source_type = source_type or "staged_fetch"
    effective_title = title or path.name

    result = ingest_local_source(
        conn,
        local_path=path,
        domain=domain,
        raw_text=raw_text,
        title=effective_title,
        source_type=effective_source_type,
    )
    return {
        **result,
        "command": INGEST_STAGED_COMMAND,
        "candidate_id": candidate_id,
        "artifact_path": str(path),
        "artifact_checksum": checksum,
    }


def run_ingest_staged_command(
    conn: Any,
    *,
    domain: str,
    candidate_id: str | None = None,
    artifact_path: Path | None = None,
    expected_checksum: str | None = None,
    staging_dir: Path | None = None,
    source_type: str | None = None,
    title: str | None = None,
) -> tuple[dict[str, Any], int]:
    try:
        payload = ingest_staged_artifact(
            conn,
            domain=domain,
            candidate_id=candidate_id,
            artifact_path=artifact_path,
            expected_checksum=expected_checksum,
            staging_dir=staging_dir,
            source_type=source_type,
            title=title,
        )
        return payload, OK_EXIT_CODE
    except FetchError as exc:
        payload = {
            "status": "error",
            "command": INGEST_STAGED_COMMAND,
            "reason": "ingest_failed",
            "detail": str(exc),
            "candidate_id": candidate_id,
        }
        return payload, ERROR_EXIT_CODE


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
