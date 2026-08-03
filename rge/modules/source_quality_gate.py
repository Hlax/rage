"""Deterministic, domain-neutral source-artifact eligibility gate.

The gate runs before claim extraction.  It records only bounded diagnostics and
never stores source text in its decision payload.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

GATE_VERSION = "source_eligibility_v0.1.0"

ELIGIBLE = "eligible"
QUARANTINED = "quarantined"
NEEDS_REVIEW = "needs_review"

EMPTY_CONTENT = "empty_content"
ACCESS_CHALLENGE = "access_challenge"
REDIRECT_SHELL = "redirect_shell"
ERROR_PAGE = "error_page"
NAVIGATION_SHELL = "navigation_shell"
INSUFFICIENT_CONTENT = "insufficient_content"
SHORT_CONTENT_REVIEW = "short_content_needs_review"

_ACCESS_PATTERNS = (
    re.compile(r"\bverify (?:that )?you are (?:a )?human\b", re.I),
    re.compile(r"\bchecking your browser\b", re.I),
    re.compile(r"\benable javascript(?: and cookies)? to continue\b", re.I),
    re.compile(r"\bautomated traffic\b", re.I),
    re.compile(r"\bcaptcha\b", re.I),
    re.compile(r"\baccess denied\b", re.I),
)
_REDIRECT_PATTERNS = (
    re.compile(r"\bdocument moved permanently\b", re.I),
    re.compile(r"\byou (?:are|will be) (?:being )?redirected\b", re.I),
    re.compile(r"\bredirect does not begin\b", re.I),
    re.compile(r"\bcontinue to the new (?:article |document )?location\b", re.I),
)
_ERROR_PATTERNS = (
    re.compile(r"\b(?:4\d\d|5\d\d) (?:error|not found|forbidden)\b", re.I),
    re.compile(r"\binternal server error\b", re.I),
    re.compile(r"\bservice unavailable\b", re.I),
    re.compile(r"\brequested (?:page|document|resource) (?:was |could )?not (?:be )?(?:found|loaded)\b", re.I),
    re.compile(r"\bplease try again later\b", re.I),
)
_NAV_LABELS = frozenset(
    {
        "home",
        "about",
        "sign in",
        "log in",
        "topics",
        "research",
        "previous article",
        "next article",
        "download pdf",
        "view metrics",
        "share",
        "privacy",
        "contact",
    }
)
_SHORT_RESEARCH_SOURCE_TYPES = frozenset(
    {
        "abstract",
        "peer_reviewed_empirical",
        "scholarly_abstract",
        "staged_fetch",
    }
)


@dataclass(frozen=True)
class SourceEligibilityDecision:
    """One stable source-level admission decision."""

    status: str
    reason_codes: tuple[str, ...]
    char_count: int
    word_count: int
    sentence_count: int
    gate_version: str = GATE_VERSION

    @property
    def extraction_eligible(self) -> bool:
        return self.status == ELIGIBLE

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "gate_version": self.gate_version,
            "extraction_eligible": self.extraction_eligible,
            "signals": {
                "char_count": self.char_count,
                "word_count": self.word_count,
                "sentence_count": self.sentence_count,
            },
        }


def _decision(
    status: str,
    reason: str,
    *,
    char_count: int,
    word_count: int,
    sentence_count: int,
) -> SourceEligibilityDecision:
    return SourceEligibilityDecision(
        status=status,
        reason_codes=(reason,),
        char_count=char_count,
        word_count=word_count,
        sentence_count=sentence_count,
    )


def assess_source_eligibility(
    text: str,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> SourceEligibilityDecision:
    """Classify source text without domain-specific vocabulary or model calls."""
    normalized = " ".join(str(text or "").split())
    lowered = normalized.casefold()
    char_count = len(normalized)
    words = re.findall(r"\b[\w'-]+\b", normalized, flags=re.UNICODE)
    word_count = len(words)
    sentence_count = len(re.findall(r"[.!?](?:\s|$)", normalized))
    context = metadata or {}

    raw_status = context.get("http_status") or context.get("status_code")
    try:
        http_status = int(raw_status) if raw_status is not None else None
    except (TypeError, ValueError):
        http_status = None
    if http_status is not None and http_status >= 400:
        return _decision(
            QUARANTINED,
            ERROR_PAGE,
            char_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
        )

    if not normalized:
        return _decision(
            QUARANTINED,
            EMPTY_CONTENT,
            char_count=0,
            word_count=0,
            sentence_count=0,
        )

    access_hits = sum(bool(pattern.search(normalized)) for pattern in _ACCESS_PATTERNS)
    if char_count <= 2500 and (access_hits >= 2 or "captcha" in lowered):
        return _decision(
            QUARANTINED,
            ACCESS_CHALLENGE,
            char_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
        )

    redirect_hits = sum(bool(pattern.search(normalized)) for pattern in _REDIRECT_PATTERNS)
    if char_count <= 1500 and redirect_hits >= 2:
        return _decision(
            QUARANTINED,
            REDIRECT_SHELL,
            char_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
        )

    error_hits = sum(bool(pattern.search(normalized)) for pattern in _ERROR_PATTERNS)
    if char_count <= 2000 and error_hits >= 2:
        return _decision(
            QUARANTINED,
            ERROR_PAGE,
            char_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
        )

    nav_hits = sum(label in lowered for label in _NAV_LABELS)
    pipe_count = normalized.count("|")
    if char_count <= 1500 and nav_hits >= 5 and (sentence_count <= 1 or pipe_count >= 2):
        return _decision(
            QUARANTINED,
            NAVIGATION_SHELL,
            char_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
        )

    if char_count < 40 or word_count < 4:
        return _decision(
            QUARANTINED,
            INSUFFICIENT_CONTENT,
            char_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
        )

    source_type = str(context.get("source_type") or "").strip().casefold()
    if (
        char_count < 120
        and sentence_count >= 1
        and (
            source_type in _SHORT_RESEARCH_SOURCE_TYPES
            or context.get("artifact_validated") is True
        )
    ):
        return _decision(
            ELIGIBLE,
            ELIGIBLE,
            char_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
        )

    if char_count < 120 or sentence_count < 1:
        return _decision(
            NEEDS_REVIEW,
            SHORT_CONTENT_REVIEW,
            char_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
        )

    return _decision(
        ELIGIBLE,
        ELIGIBLE,
        char_count=char_count,
        word_count=word_count,
        sentence_count=sentence_count,
    )


def source_eligibility_from_metadata(
    metadata: Mapping[str, Any],
) -> SourceEligibilityDecision | None:
    """Load a previously persisted private decision when its version is current."""
    raw = metadata.get("source_eligibility")
    if not isinstance(raw, Mapping) or raw.get("gate_version") != GATE_VERSION:
        return None
    status = str(raw.get("status") or "")
    if status not in {ELIGIBLE, QUARANTINED, NEEDS_REVIEW}:
        return None
    reasons = raw.get("reason_codes")
    if not isinstance(reasons, list) or not reasons or not all(
        isinstance(reason, str) and reason for reason in reasons
    ):
        return None
    signals = raw.get("signals") if isinstance(raw.get("signals"), Mapping) else {}
    return SourceEligibilityDecision(
        status=status,
        reason_codes=tuple(reasons),
        char_count=int(signals.get("char_count") or 0),
        word_count=int(signals.get("word_count") or 0),
        sentence_count=int(signals.get("sentence_count") or 0),
    )
