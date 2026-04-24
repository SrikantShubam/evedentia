from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GateSpec:
    gate_name: str
    gate_kind: str
    cost_tier: str


COST_FREE = "free"
COST_LLM_LIGHT = "llm_light"
COST_LLM_REASON = "llm_reason"
COST_LLM_PAID_SEARCH = "llm_paid_search"

PROFILES: dict[str, list[GateSpec]] = {
    "consumer_app": [
        GateSpec("parent_market_exists", "structural", COST_FREE),
        GateSpec("niche_not_already_owned", "structural", COST_FREE),
        GateSpec("complaint_signal_exists", "evidence", COST_FREE),
        GateSpec("three_first_person_voices", "evidence", COST_LLM_LIGHT),
        GateSpec("reachable_channel", "evidence", COST_LLM_LIGHT),
        GateSpec("retention_plausible", "evidence", COST_LLM_REASON),
        GateSpec("player_fit", "structural", COST_LLM_REASON),
        GateSpec("willingness_to_pay", "evidence", COST_LLM_PAID_SEARCH),
    ],
    "b2b_workflow": [
        GateSpec("parent_market_exists", "structural", COST_FREE),
        GateSpec("budget_owner_identifiable", "structural", COST_FREE),
        GateSpec("procurement_path_exists", "evidence", COST_FREE),
        GateSpec("three_first_person_voices", "evidence", COST_LLM_LIGHT),
        GateSpec("player_fit", "structural", COST_LLM_REASON),
        GateSpec("willingness_to_pay", "evidence", COST_LLM_PAID_SEARCH),
        GateSpec("switching_cost_defensible", "structural", COST_LLM_REASON),
    ],
    "browser_extension": [
        GateSpec("parent_market_exists", "structural", COST_FREE),
        GateSpec("store_category_not_saturated", "structural", COST_FREE),
        GateSpec("complaint_signal_exists", "evidence", COST_FREE),
        GateSpec("three_first_person_voices", "evidence", COST_LLM_LIGHT),
        GateSpec("reachable_channel", "evidence", COST_LLM_LIGHT),
        GateSpec("player_fit", "structural", COST_LLM_REASON),
        GateSpec("monetization_path_plausible", "structural", COST_LLM_REASON),
    ],
    "agency_service": [
        GateSpec("parent_market_exists", "structural", COST_FREE),
        GateSpec("repeat_purchase_evidence", "evidence", COST_FREE),
        GateSpec("three_first_person_voices", "evidence", COST_LLM_LIGHT),
        GateSpec("player_fit", "structural", COST_LLM_REASON),
        GateSpec("referral_dynamics", "evidence", COST_LLM_REASON),
        GateSpec("pricing_anchor_exists", "evidence", COST_LLM_LIGHT),
    ],
}

STRUCTURAL_GATES: dict[str, set[str]] = {
    profile: {spec.gate_name for spec in gates if spec.gate_kind == "structural"}
    for profile, gates in PROFILES.items()
}


def required_gates(profile_name: str) -> list[str]:
    if profile_name not in PROFILES:
        raise ValueError(f"unknown gate profile: {profile_name}")
    return [spec.gate_name for spec in PROFILES[profile_name]]
