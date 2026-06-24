"""Mock-first cloud synthesis clients (ticket-059).

OpenAI live HTTP is opt-in only. Default path returns deterministic mock output.
Candidate synthesis output is validated upstream; nothing here writes accepted graph rows.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from rge.contracts.synthesis_evidence_packet_v0 import (
    atom_text_by_id,
    claim_text_by_id,
    validate_synthesis_evidence_packet,
)
from rge.modules.operator_env_loader import openai_key_available


def _load_circuit_breaker(root: Any | None = None):
    from rge.modules.autonomous_synthesis_governor import load_circuit_breaker

    return load_circuit_breaker(root=root)


def _evaluate_budget_gate(*, provider_id: str):
    from rge.modules.autonomous_synthesis_governor import evaluate_budget_gate

    return evaluate_budget_gate(provider_id=provider_id)

OUTPUT_SCHEMA_VERSION = "synthesis_output_v0.1.0"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


class CloudSynthesisError(RuntimeError):
    """Raised when cloud synthesis cannot proceed safely."""


class CloudSynthesisGateError(CloudSynthesisError):
    """Raised when required env gates are missing (fail closed)."""


def _truthy(name: str) -> bool:
    return os.environ.get(name, "0").strip().casefold() in {"1", "true", "yes"}


def _positive_float(raw: str) -> float | None:
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def _positive_int(raw: str) -> int | None:
    try:
        value = int(float(raw))
    except ValueError:
        return None
    return value if value > 0 else None


def missing_live_openai_http_gates(*, root: Any | None = None) -> dict[str, str]:
    """Return missing live OpenAI HTTP gates; empty dict means all gates satisfied."""
    missing: dict[str, str] = {}
    if not _truthy("RGE_CLOUD_LLM_ENABLED"):
        missing["RGE_CLOUD_LLM_ENABLED"] = "required=1"
    if not _truthy("RGE_ALLOW_OPENAI_SYNTHESIS"):
        missing["RGE_ALLOW_OPENAI_SYNTHESIS"] = "required=1"
    if not _truthy("RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP"):
        missing["RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP"] = "required=1"
    if not openai_key_available():
        missing["OPENAI_API_KEY"] = "required (never logged or exported)"

    allowlist_raw = (
        os.environ.get("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST")
        or os.environ.get("RGE_CLOUD_PROVIDER_ALLOWLIST")
        or ""
    ).strip()
    if not allowlist_raw:
        missing["RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST"] = "must include openai"
    else:
        allowed = {item.strip().casefold() for item in allowlist_raw.split(",") if item.strip()}
        if "openai" not in allowed:
            missing["RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST"] = "must include openai"

    max_usd_raw = os.environ.get("RGE_CLOUD_MAX_USD_PER_RUN", "").strip()
    max_tokens_raw = os.environ.get("RGE_CLOUD_MAX_TOKENS_PER_CALL", "").strip()
    if not max_usd_raw:
        missing["RGE_CLOUD_MAX_USD_PER_RUN"] = "required and > 0"
    elif _positive_float(max_usd_raw) is None:
        missing["RGE_CLOUD_MAX_USD_PER_RUN"] = "must be numeric and > 0"
    if not max_tokens_raw:
        missing["RGE_CLOUD_MAX_TOKENS_PER_CALL"] = "required and > 0"
    elif _positive_int(max_tokens_raw) is None:
        missing["RGE_CLOUD_MAX_TOKENS_PER_CALL"] = "must be numeric and > 0"

    circuit = _load_circuit_breaker(root=root)
    if circuit.get("status") == "open":
        missing["autonomy_circuit_breaker"] = (
            f"open: {circuit.get('latest_stop_reason') or 'unknown'}"
        )
    return missing


def assert_live_openai_http_gates(*, root: Any | None = None) -> dict[str, str]:
    """Fail closed before any live OpenAI HTTP request is constructed."""
    missing = missing_live_openai_http_gates(root=root)
    if missing:
        raise CloudSynthesisGateError(
            "Live OpenAI HTTP blocked. Set: "
            + ", ".join(f"{key} ({hint})" for key, hint in missing.items())
        )
    budget = _evaluate_budget_gate(provider_id="openai")
    if not budget.get("passed"):
        raise CloudSynthesisGateError(
            "Live OpenAI HTTP blocked by budget gate: "
            + "; ".join(budget.get("reasons") or ["unknown"])
        )
    return build_public_safe_live_status(root=root)


def build_public_safe_live_status(*, root: Any | None = None) -> dict[str, Any]:
    """Public-safe operator status (no secrets, no raw prompts)."""
    circuit = _load_circuit_breaker(root=root)
    budget = _evaluate_budget_gate(provider_id="openai")
    return {
        "provider_id": "openai",
        "openai_key_available": openai_key_available(),
        "cloud_llm_enabled": _truthy("RGE_CLOUD_LLM_ENABLED"),
        "openai_synthesis_enabled": _truthy("RGE_ALLOW_OPENAI_SYNTHESIS"),
        "live_http_enabled": _truthy("RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP"),
        "circuit_breaker_status": str(circuit.get("status") or "closed"),
        "max_usd_per_run": budget.get("max_usd_per_run"),
        "max_tokens_per_call": budget.get("max_tokens_per_call"),
        "provider_allowlist": budget.get("provider_allowlist"),
        "live_http_gates_satisfied": not missing_live_openai_http_gates(root=root),
    }


def _packet_sha256(packet: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(packet, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _public_source_metadata(ref: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": ref.get("source_id"),
        "source_type": ref.get("source_type"),
        "title": ref.get("title"),
    }


def _build_grounding_payload(packet: dict[str, Any]) -> dict[str, Any]:
    """Public-safe grounded text and metadata for OpenAI synthesis prompts."""
    claim_texts = claim_text_by_id(packet)
    atom_texts = atom_text_by_id(packet)
    claims_payload: list[dict[str, Any]] = []
    for claim in packet.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id") or "")
        claims_payload.append(
            {
                "claim_id": claim.get("claim_id"),
                "source_id": claim.get("source_id"),
                "claim_text": claim_texts.get(claim_id, ""),
                "stance": claim.get("stance"),
                "scope": claim.get("scope"),
                "limitations": claim.get("limitations"),
            }
        )
    atoms_payload: list[dict[str, Any]] = []
    for atom in packet.get("atoms") or []:
        if not isinstance(atom, dict):
            continue
        atom_id = str(atom.get("atom_id") or "")
        atoms_payload.append(
            {
                "atom_id": atom.get("atom_id"),
                "canonical_text": atom_texts.get(atom_id, ""),
                "maturity": atom.get("maturity"),
                "claim_ids": atom.get("claim_ids"),
                "source_ids": atom.get("source_ids"),
            }
        )
    source_metadata = [
        _public_source_metadata(ref)
        for ref in (packet.get("source_refs") or [])
        if isinstance(ref, dict)
    ]
    return {
        "research_question": packet.get("research_question"),
        "purpose": packet.get("purpose"),
        "claims": claims_payload,
        "atoms": atoms_payload,
        "source_refs": source_metadata,
        "trace_refs": packet.get("trace_refs") or [],
    }


def _allowed_source_ids(packet: dict[str, Any]) -> set[str]:
    return {
        str(row.get("source_id"))
        for row in (packet.get("source_refs") or [])
        if isinstance(row, dict) and row.get("source_id")
    }


def _normalize_source_ref(value: Any, *, allowed_sources: set[str]) -> str | None:
    if isinstance(value, dict):
        source_id = str(value.get("source_id") or "").strip()
    else:
        source_id = str(value or "").strip()
    if not source_id or source_id not in allowed_sources:
        return None
    return source_id


def _normalize_summary_sentences(
    sentences: list[Any],
    *,
    packet: dict[str, Any],
) -> list[dict[str, Any]]:
    allowed_sources = _allowed_source_ids(packet)
    normalized: list[dict[str, Any]] = []
    for index, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            raise CloudSynthesisError(f"summary_sentences[{index}] must be an object")
        source_refs: list[str] = []
        for ref_index, ref in enumerate(sentence.get("source_refs") or []):
            resolved = _normalize_source_ref(ref, allowed_sources=allowed_sources)
            if resolved is None:
                raise CloudSynthesisError(
                    f"summary_sentences[{index}] source_refs[{ref_index}] cites unresolvable source_ref"
                )
            source_refs.append(resolved)
        normalized.append(
            {
                "text": str(sentence.get("text") or "").strip(),
                "claim_ids": [str(value) for value in (sentence.get("claim_ids") or []) if value],
                "atom_ids": [str(value) for value in (sentence.get("atom_ids") or []) if value],
                "source_refs": source_refs,
            }
        )
    return normalized


def _first_grounded_sentence(packet: dict[str, Any]) -> dict[str, Any]:
    claim_texts = claim_text_by_id(packet)
    atom_texts = atom_text_by_id(packet)
    claims = packet.get("claims") or []
    atoms = packet.get("atoms") or []
    claim_id = str((claims[0] or {}).get("claim_id") or "claim_preview_a")
    atom_id = str((atoms[0] or {}).get("atom_id") or "atom_preview_001")
    source_id = str((claims[0] or {}).get("source_id") or "src_preview_a")
    claim_text = claim_texts.get(claim_id, "")
    atom_text = atom_texts.get(atom_id, "")
    if claim_text:
        text = claim_text
    elif atom_text:
        text = atom_text
    else:
        text = (
            f"Mock synthesis summary grounded to {claim_id} and {atom_id} "
            f"for packet {packet.get('packet_id')}."
        )
    return {
        "text": text,
        "claim_ids": [claim_id],
        "atom_ids": [atom_id],
        "source_refs": [source_id],
    }


class CloudSynthesisClient(ABC):
    provider: str

    @abstractmethod
    def synthesize(self, packet: dict[str, Any]) -> dict[str, Any]:
        """Return candidate synthesis output (never writes accepted graph rows)."""


class MockCloudSynthesisClient(CloudSynthesisClient):
    provider = "mock_cloud"

    def synthesize(self, packet: dict[str, Any]) -> dict[str, Any]:
        errors = validate_synthesis_evidence_packet(packet)
        if errors:
            raise CloudSynthesisError(
                "Evidence packet failed validation: " + "; ".join(errors[:5])
            )
        return {
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "packet_id": str(packet.get("packet_id") or "unknown"),
            "packet_sha256": _packet_sha256(packet),
            "provider": self.provider,
            "no_paid_api_calls": True,
            "review_mode": "mock",
            "summary_sentences": [_first_grounded_sentence(packet)],
            "usage": {"tokens": 0, "usd": 0.0},
        }


class OpenAISynthesisClient(CloudSynthesisClient):
    provider = "openai"

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 180,
        urlopen: Any | None = None,
    ) -> None:
        self.model = (model or os.environ.get("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL).strip()
        self.base_url = (
            base_url or os.environ.get("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE_URL
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._urlopen = urlopen

    def synthesize(self, packet: dict[str, Any]) -> dict[str, Any]:
        errors = validate_synthesis_evidence_packet(packet)
        if errors:
            raise CloudSynthesisError(
                "Evidence packet failed validation: " + "; ".join(errors[:5])
            )
        assert_live_openai_http_gates()
        response = self._post_chat_completion(packet)
        return self._parse_candidate_output(packet, response)

    def _build_request_body(self, packet: dict[str, Any]) -> dict[str, Any]:
        max_tokens = _positive_int(os.environ.get("RGE_CLOUD_MAX_TOKENS_PER_CALL", ""))
        if max_tokens is None:
            raise CloudSynthesisGateError("RGE_CLOUD_MAX_TOKENS_PER_CALL must be > 0")
        grounding = _build_grounding_payload(packet)
        return {
            "model": self.model,
            "temperature": 0,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return JSON with summary_sentences: an array of objects each "
                        "containing text, claim_ids, atom_ids, and source_refs. "
                        "source_refs must be source_id strings from the provided "
                        "source_refs list. Cite only provided claim_ids, atom_ids, and "
                        "source_refs; do not invent sources. Each sentence must reuse "
                        "significant wording (words of four or more letters) from the "
                        "claim_text and canonical_text of every cited claim_id and atom_id."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(grounding, sort_keys=True),
                },
            ],
        }

    def _post_chat_completion(self, packet: dict[str, Any]) -> dict[str, Any]:
        body = self._build_request_body(packet)
        api_key = os.environ.get("OPENAI_API_KEY", "").strip() or os.environ.get(
            "RGE_OPENAI_API_KEY", ""
        ).strip()
        if not api_key:
            raise CloudSynthesisGateError("OPENAI_API_KEY is required (never logged)")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        urlopen = self._urlopen or urllib.request.urlopen
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise CloudSynthesisError(f"OpenAI HTTP request failed: {exc}") from exc
        if not isinstance(payload, dict):
            raise CloudSynthesisError("OpenAI HTTP response was not a JSON object")
        return payload

    def _parse_candidate_output(
        self,
        packet: dict[str, Any],
        response: dict[str, Any],
    ) -> dict[str, Any]:
        choices = response.get("choices") or []
        message = (choices[0] or {}).get("message") if choices else {}
        content = str((message or {}).get("content") or "").strip()
        if not content:
            raise CloudSynthesisError("OpenAI response missing message content")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise CloudSynthesisError("OpenAI response content was not valid JSON") from exc
        sentences = parsed.get("summary_sentences")
        if not isinstance(sentences, list) or not sentences:
            raise CloudSynthesisError("OpenAI response missing summary_sentences")
        normalized_sentences = _normalize_summary_sentences(sentences, packet=packet)
        usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
        return {
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "packet_id": str(packet.get("packet_id") or "unknown"),
            "packet_sha256": _packet_sha256(packet),
            "provider": self.provider,
            "no_paid_api_calls": False,
            "review_mode": "live_candidate",
            "summary_sentences": normalized_sentences,
            "usage": {
                "tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
            "cost_estimate_usd": None,
        }

