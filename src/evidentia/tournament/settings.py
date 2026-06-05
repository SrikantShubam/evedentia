from __future__ import annotations

import os


SHORTLIST_CONFIDENCE_THRESHOLD = float(os.environ.get("EVIDENTIA_SHORTLIST_CONFIDENCE_THRESHOLD", "0.85"))
CONFIDENCE_FLOOR = float(os.environ.get("EVIDENTIA_CONFIDENCE_FLOOR", "0.5"))
CONFIDENCE_CEIL = float(os.environ.get("EVIDENTIA_CONFIDENCE_CEIL", "0.95"))

# Per-gate confidence baselines matching the hardcoded values in gates.py.
# Keys: gate name → {"pass": confidence when passed, "fail": confidence when failed}.
# Environment override per gate: EVIDENTIA_GATE_CONF_{GATE_NAME_UPPER}_PASS / _FAIL
GATE_CONFIDENCE_CONFIG: dict[str, dict[str, float]] = {
    "parent_market_exists": {"pass": 0.93, "fail": 0.55},
    "niche_not_already_owned": {"pass": 0.89, "fail": 0.55},
    "complaint_signal_exists": {"pass": 0.90, "fail": 0.55},
    "three_first_person_voices": {"pass": 0.92, "fail": 0.55},
    "reachable_channel": {"pass": 0.90, "fail": 0.55},
    "pricing_anchor_exists": {"pass": 0.90, "fail": 0.55},
    "retention_plausible": {"pass": 0.88, "fail": 0.55},
    "switching_cost_defensible": {"pass": 0.88, "fail": 0.55},
    "referral_dynamics": {"pass": 0.88, "fail": 0.55},
    "budget_owner_identifiable": {"pass": 0.91, "fail": 0.55},
    "monetization_path_plausible": {"pass": 0.91, "fail": 0.55},
    "willingness_to_pay": {"pass": 0.91, "fail": 0.55},
    "store_category_not_saturated": {"pass": 0.86, "fail": 0.55},
    "player_fit": {"pass": 0.93, "fail": 0.55},
    "repeat_purchase_evidence": {"pass": 0.90, "fail": 0.55},
    "procurement_path_exists": {"pass": 0.90, "fail": 0.55},
}


def gate_confidence_base(gate_name: str, passed: bool) -> float:
    """Return the baseline confidence for a gate outcome.

    Respects per-gate environment variable overrides of the form:
      EVIDENTIA_GATE_CONF_{UPPER_GATE_NAME}_PASS
      EVIDENTIA_GATE_CONF_{UPPER_GATE_NAME}_FAIL
    """
    config = GATE_CONFIDENCE_CONFIG.get(gate_name, {"pass": 0.88, "fail": 0.55})
    key = "pass" if passed else "fail"
    env_key = f"EVIDENTIA_GATE_CONF_{gate_name.upper()}_{key.upper()}"
    return float(os.environ.get(env_key, str(config[key])))


# Evidence provenance values that count as "first-person voice" for
# the three_first_person_voices gate.  Add new non-synthetic provenance
# strings here when the evidence pipeline introduces them.
FIRST_PERSON_PROVENANCES: frozenset[str] = frozenset({
    "verified",
    "cited_evidence",
    "seed",
    "reentry",
    "llm_inference",
    "llm_educated_guess",
})
