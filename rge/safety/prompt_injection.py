"""Prompt-injection handling policy for untrusted source text.

Phase 0 stub: policy constants from ``docs/agents/10_SAFETY_MODEL.md``
sections 4-5. Deterministic sanitation checks arrive with the Phase 1 claim
validation ticket. All source text is untrusted data, never instructions;
prompt wording alone is not a defense.
"""

from __future__ import annotations

# Behaviors that injected source text must never cause.
FORBIDDEN_INJECTION_EFFECTS = (
    "change source credibility because source text asks for it",
    "delete claims",
    "export private notes",
    "alter system instructions",
    "trigger shell, Git, or network actions",
    "extract instructions embedded in source text as claims",
)

REJECTION_REASON_INJECTED_CONTENT = "unsafe_or_injected_content"
