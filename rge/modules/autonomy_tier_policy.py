"""Autonomy tier policy for controlled release and batch promotion."""

from __future__ import annotations

import os
from typing import Any

TIER_SCHEMA_VERSION = "autonomy_tier_policy_v0.1.0"

# Tier 0 = read-only; Tier 1 = draft; Tier 2 = branch; Tier 3 = push; Tier 4 = merge; Tier 5 = publish
DEFAULT_TIER = 1
MAX_TIER = 5

TIER_NAMES = {
    0: "read_only",
    1: "draft_autonomy",
    2: "branch_autonomy",
    3: "feature_branch_push",
    4: "batch_mainline",
    5: "publish_autonomy",
}

TIER_ACTIONS: dict[int, dict[str, list[str]]] = {
    0: {
        "allowed": [
            "inspect_repo",
            "inspect_circuit_breaker",
            "write_reports",
            "recommend_actions",
            "release_governor_inspect",
            "release_governor_dry_run",
        ],
        "forbidden": [
            "generate_instruction_packet",
            "generate_draft_ticket",
            "create_branch",
            "local_commit",
            "push_branch",
            "merge_batch",
            "publish",
            "promote_canonical_ticket",
        ],
    },
    1: {
        "allowed": [
            "generate_instruction_packet",
            "generate_draft_ticket",
            "refresh_atlas_artifacts",
            "write_operator_reports",
            "release_governor_inspect",
            "release_governor_dry_run",
            "batch_report_generation",
        ],
        "forbidden": [
            "create_branch",
            "local_commit",
            "push_branch",
            "merge_batch",
            "publish",
            "promote_canonical_ticket",
        ],
    },
    2: {
        "allowed": [
            "create_feature_branch",
            "implement_draft_ticket",
            "run_targeted_tests",
            "local_commit",
            "release_governor_inspect",
            "release_governor_dry_run",
            "batch_report_generation",
        ],
        "forbidden": [
            "push_branch",
            "merge_batch",
            "publish",
            "promote_canonical_ticket",
        ],
    },
    3: {
        "allowed": [
            "push_feature_branch",
        ],
        "forbidden": [
            "merge_batch",
            "publish",
        ],
    },
    4: {
        "allowed": [
            "batch_merge",
            "promote_canonical_ticket",
        ],
        "forbidden": [
            "publish",
        ],
    },
    5: {
        "allowed": [
            "publish_public_export",
        ],
        "forbidden": [],
    },
}

TIER_ENV_FLAGS: dict[int, str | None] = {
    0: None,
    1: None,
    2: "RGE_ALLOW_BRANCH_AUTONOMY",
    3: "RGE_ALLOW_FEATURE_BRANCH_PUSH",
    4: "RGE_ALLOW_BATCH_MERGE",
    5: "RGE_ALLOW_PUBLISH_AUTONOMY",
}

ACTION_MIN_TIER: dict[str, int] = {
    "inspect_repo": 0,
    "inspect_circuit_breaker": 0,
    "write_reports": 0,
    "recommend_actions": 0,
    "release_governor_inspect": 0,
    "release_governor_dry_run": 0,
    "generate_instruction_packet": 1,
    "generate_draft_ticket": 1,
    "refresh_atlas_artifacts": 1,
    "write_operator_reports": 1,
    "batch_report_generation": 1,
    "create_feature_branch": 2,
    "implement_draft_ticket": 2,
    "run_targeted_tests": 2,
    "local_commit": 2,
    "push_feature_branch": 3,
    "batch_merge": 4,
    "promote_canonical_ticket": 4,
    "publish_public_export": 5,
}


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "0").strip().casefold() in {"1", "true", "yes"}


def configured_autonomy_tier() -> int:
    raw = os.environ.get("RGE_AUTONOMY_TIER", str(DEFAULT_TIER)).strip()
    try:
        tier = int(raw)
    except ValueError:
        tier = DEFAULT_TIER
    return max(0, min(tier, MAX_TIER))


def tier_env_enabled(tier: int) -> bool:
    if tier <= 1:
        return True
    flag = TIER_ENV_FLAGS.get(tier)
    if flag is None:
        return configured_autonomy_tier() >= tier
    return _truthy_env(flag) and configured_autonomy_tier() >= tier


def effective_autonomy_tier() -> int:
    configured = configured_autonomy_tier()
    effective = 0
    for tier in range(0, configured + 1):
        if tier <= 1 or tier_env_enabled(tier):
            effective = tier
    return effective


def action_allowed(action: str, *, tier: int | None = None) -> tuple[bool, str]:
    """Return (allowed, reason) for an autonomy action at the effective tier."""
    effective = tier if tier is not None else effective_autonomy_tier()
    required = ACTION_MIN_TIER.get(action)
    if required is None:
        return False, f"unknown autonomy action: {action}"
    if effective < required:
        return False, (
            f"action {action!r} requires tier {required} ({TIER_NAMES.get(required)}); "
            f"effective tier is {effective} ({TIER_NAMES.get(effective, 'unknown')})"
        )
    if required >= 2 and not tier_env_enabled(required):
        flag = TIER_ENV_FLAGS.get(required, "RGE_AUTONOMY_TIER")
        return False, (
            f"action {action!r} requires explicit env enablement ({flag}=1) "
            f"and RGE_AUTONOMY_TIER>={required}"
        )
    return True, "allowed"


def summarize_tier_policy() -> dict[str, Any]:
    tier = effective_autonomy_tier()
    configured = configured_autonomy_tier()
    allowed: list[str] = []
    forbidden: list[str] = []
    for action, min_tier in sorted(ACTION_MIN_TIER.items(), key=lambda item: item[1]):
        ok, _ = action_allowed(action, tier=tier)
        if ok:
            allowed.append(action)
        elif min_tier <= configured:
            forbidden.append(action)
    return {
        "schema_version": TIER_SCHEMA_VERSION,
        "configured_tier": configured,
        "effective_tier": tier,
        "tier_name": TIER_NAMES.get(tier, "unknown"),
        "default_tier": DEFAULT_TIER,
        "allowed_actions": allowed,
        "forbidden_actions": forbidden,
        "tier_env_flags": {
            str(key): value for key, value in TIER_ENV_FLAGS.items() if value
        },
    }
