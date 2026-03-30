from __future__ import annotations

import re

from human_ask_models import CallableDirectoryEntry


def tokenize_text(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", text.lower()) if token}


def value_matches_prompt(value: str, prompt_tokens: set[str]) -> bool:
    value_tokens = [token for token in tokenize_text(value) if len(token) >= 4]
    return bool(value_tokens and all(token in prompt_tokens for token in value_tokens))


def assess_prompt_scope(
    prompt: str,
    entry: CallableDirectoryEntry,
    high_risk_terms: dict[str, float] | set[str],
) -> dict[str, object]:
    prompt_tokens = tokenize_text(prompt)
    allowed_actions = [str(item) for item in entry.metadata.get("allowed_actions", [])]
    required_human_actions = [str(item) for item in entry.metadata.get("required_human_actions", [])]
    handled_resources = [str(item) for item in entry.metadata.get("handled_resources", [])]

    matched_allowed_actions = [
        action for action in allowed_actions if value_matches_prompt(action, prompt_tokens)
    ]
    matched_required_human_actions = [
        action for action in required_human_actions if value_matches_prompt(action, prompt_tokens)
    ]
    matched_resources = [
        resource for resource in handled_resources if value_matches_prompt(resource, prompt_tokens)
    ]
    matched_sensitive_terms = [term for term in high_risk_terms if term in prompt_tokens]
    scope_anchor_tokens = tokenize_text(
        " ".join(
            filter(
                None,
                [
                    entry.business_domain or "",
                    entry.role_id,
                    entry.display_name,
                ],
            )
        )
    )
    scope_anchor_match = bool(prompt_tokens & scope_anchor_tokens)
    in_scope = bool(matched_allowed_actions or matched_resources or scope_anchor_match)

    if matched_required_human_actions:
        status = "human_only_boundary"
        reason = "The request matched human-only actions from the loaded JD."
    elif in_scope:
        status = "in_scope"
        reason = "The request aligns with the loaded JD, allowed actions, or handled resources."
    else:
        status = "out_of_scope"
        reason = "The request does not align with allowed actions or handled resources in the loaded JD."

    return {
        "status": status,
        "reason": reason,
        "matched_allowed_actions": matched_allowed_actions,
        "matched_required_human_actions": matched_required_human_actions,
        "matched_resources": matched_resources,
        "matched_sensitive_terms": matched_sensitive_terms,
        "automation_ready": status == "in_scope",
    }
