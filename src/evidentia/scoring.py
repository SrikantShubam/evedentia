from datetime import datetime, timezone

from evidentia.models import Verdict


HARD_GATES = (
    "willingness_to_pay",
    "distribution_channel",
    "data_feasibility",
)

WEIGHT_COMPETITION_GAP = 0.4
WEIGHT_BUILDABILITY = 0.3
WEIGHT_REACHABILITY = 0.3

assert abs(WEIGHT_COMPETITION_GAP + WEIGHT_BUILDABILITY + WEIGHT_REACHABILITY - 1.0) < 1e-9, (
    "scoring weights must sum to 1.0"
)

QUALIFICATION_STATES = ("REJECT", "DISCOVER", "QUALIFY", "PURSUE", "DEFER")

_MISSING_FOR_PASS = {
    "willingness_to_pay": [
        "explicit budget owner",
        "clear replacement-spend intent",
    ],
    "distribution_channel": [
        "named reachable channel",
        "repeatable acquisition path",
    ],
    "data_feasibility": [
        "obtainable source data",
        "viable wedge workflow inputs",
    ],
}


def _to_float(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number < 0.0:
        return 0.0
    if number > 1.0:
        return 1.0
    return number


def _supporting_signal_ids(opportunity: dict) -> list[str]:
    ids: list[str] = []
    for idx, signal in enumerate(opportunity.get("verified_signals", []), start=1):
        signal_id = signal.get("signal_id")
        if signal_id:
            ids.append(str(signal_id))
            continue
        source_url = signal.get("source_url")
        if source_url:
            ids.append(str(source_url))
            continue
        ids.append(f"signal_{idx}")
    return ids


def _qualification_state_from_gates(gate_values: dict[str, str]) -> str:
    if all(value == "pass" for value in gate_values.values()):
        return "PURSUE"
    pass_count = sum(1 for value in gate_values.values() if value == "pass")
    if pass_count >= 2:
        return "QUALIFY"
    return "DISCOVER"


def _build_gate_rationale(gate: str, status: str, supporting_signal_ids: list[str]) -> dict:
    if status == "pass":
        return {
            "status": "pass",
            "basis": "observed",
            "reason": f"{gate} evidence is adequate for the current record.",
            "supporting_signal_ids": supporting_signal_ids,
            "missing_for_pass": [],
        }
    return {
        "status": "fail",
        "basis": "inferred",
        "reason": f"{gate} evidence is incomplete or absent.",
        "supporting_signal_ids": [],
        "missing_for_pass": list(_MISSING_FOR_PASS[gate]),
    }


def evaluate_spec_readiness(opportunity: dict) -> dict:
    source_trace = [str(signal.get("source_url", "")) for signal in opportunity.get("verified_signals", []) if signal.get("source_url")]
    text_blob = " ".join(
        [
            str(opportunity.get("title", "")),
            " ".join(str(signal.get("verbatim_quote", "")) for signal in opportunity.get("verified_signals", [])),
        ]
    ).lower()

    buyer_definition = None
    buyer_hints = ("team", "startup", "business", "freelancer", "developer", "accounting", "finance", "company")
    if any(hint in text_blob for hint in buyer_hints):
        buyer_definition = "buyer actor identified in evidence text"

    workflow_definition = None
    workflow_hints = ("invoice", "expense", "reconcile", "tracking", "follow-up", "reminder", "workflow")
    if any(hint in text_blob for hint in workflow_hints):
        workflow_definition = "recurring workflow friction is visible in evidence text"

    distribution_path = "channel evidence passed hard-gate review" if opportunity.get("distribution_channel") == "pass" else None
    build_scope = "wedge scope appears feasible from available data" if opportunity.get("data_feasibility") == "pass" else None
    wedge_definition = str(opportunity.get("title", "")).strip() or None

    blocked_by: list[str] = []
    if opportunity.get("qualification_state") != "PURSUE":
        blocked_by.append("qualification_state_not_pursue")
    if not source_trace:
        blocked_by.append("missing_verified_signals")
    if buyer_definition is None:
        blocked_by.append("buyer_definition_missing")
    if workflow_definition is None:
        blocked_by.append("workflow_definition_missing")
    if distribution_path is None:
        blocked_by.append("distribution_path_missing")
    if build_scope is None:
        blocked_by.append("build_scope_missing")

    return {
        "ready_for_spec": len(blocked_by) == 0,
        "wedge_definition": wedge_definition,
        "buyer_definition": buyer_definition,
        "workflow_definition": workflow_definition,
        "distribution_path": distribution_path,
        "build_scope": build_scope,
        "blocked_by": blocked_by,
        "source_trace": source_trace,
    }


def score_opportunity(opportunity: dict) -> dict:
    gate_values = {gate: opportunity[gate] for gate in HARD_GATES}
    supporting_signal_ids = _supporting_signal_ids(opportunity)
    gate_rationale = {
        gate: _build_gate_rationale(gate, status=value, supporting_signal_ids=supporting_signal_ids)
        for gate, value in gate_values.items()
    }
    qualification_state = _qualification_state_from_gates(gate_values)
    gate_failures = [gate for gate, value in gate_values.items() if value != "pass"]
    missing_evidence = []
    for gate in gate_failures:
        missing_evidence.extend(gate_rationale[gate]["missing_for_pass"])

    competition_gap = _to_float(opportunity.get("competition_gap", 0.0))
    buildability = _to_float(opportunity.get("buildability", 0.0))
    reachability_strength = _to_float(opportunity.get("reachability_strength", 0.0))
    heuristic_floor = min(competition_gap, buildability, reachability_strength)
    heuristic_score = (
        competition_gap * WEIGHT_COMPETITION_GAP
        + buildability * WEIGHT_BUILDABILITY
        + reachability_strength * WEIGHT_REACHABILITY
    )

    verdict = Verdict.REFINE.value
    refine_reason: str | None = None
    next_test: str | None = None
    score = 0.0

    if gate_failures:
        if competition_gap == 0.0 and buildability == 0.0 and reachability_strength == 0.0:
            verdict = Verdict.KILL.value
        else:
            verdict = Verdict.REFINE.value
            refine_reason = f"hard_gate_failed:{','.join(gate_failures)}"
            next_test = "TODO: slice-level REFINE handler, see NEXT_PIVOT.md"
    elif heuristic_floor >= 0.4:
        verdict = Verdict.PURSUE.value
        score = round(heuristic_score, 3)
    else:
        verdict = Verdict.REFINE.value
        refine_reason = "weak_heuristics:min_below_0.4"
        next_test = "TODO: slice-level REFINE handler, see NEXT_PIVOT.md"
        score = round(heuristic_score, 3)

    return {
        "verdict": verdict,
        "gate_verdict": verdict,
        "refine_reason": refine_reason,
        "next_test": next_test,
        "qualification_state": qualification_state,
        "gate_failures": gate_failures,
        "gate_rationale": gate_rationale,
        "missing_evidence": sorted(set(missing_evidence)),
        "next_action": "review_refine_or_pursue",
        "heuristic_score": round(heuristic_score, 3),
        "freshness_factor": 1.0 if score > 0 else 0.0,
        "final_score": score,
        "score": score,
    }


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def apply_freshness_decay(opportunity: dict, reference_timestamp: str | None = None) -> float:
    base_score = float(opportunity["score"])
    published_at = _parse_timestamp(opportunity.get("published_at"))
    if published_at is None:
        return base_score

    reference = _parse_timestamp(reference_timestamp) if reference_timestamp else datetime.now(timezone.utc)
    age_days = max((reference - published_at).total_seconds() / 86400, 0.0)
    decay_factor = max(0.0, 1 - min(age_days, 365) / 365)
    return round(base_score * decay_factor, 6)


def rank_opportunities(opportunities: list[dict], reference_timestamp: str | None = None) -> list[dict]:
    scored = []
    for item in opportunities:
        enriched = dict(item, **score_opportunity(item))
        if float(enriched.get("score", 0.0)) > 0:
            final_score = apply_freshness_decay(enriched, reference_timestamp=reference_timestamp)
            heuristic_score = float(enriched["heuristic_score"])
            freshness_factor = round(final_score / heuristic_score, 3) if heuristic_score else 0.0
            enriched["freshness_factor"] = freshness_factor
            enriched["final_score"] = final_score
            enriched["score"] = final_score
        else:
            enriched["freshness_factor"] = 0.0
            enriched["final_score"] = 0.0
            enriched["score"] = 0.0
        scored.append(enriched)
    return sorted(scored, key=lambda item: item["score"], reverse=True)


def _dedupe_key(item: dict) -> tuple[float, float, str]:
    published_at = _parse_timestamp(item.get("published_at"))
    published_value = published_at.timestamp() if published_at else float("-inf")
    return (float(item["score"]), published_value, str(item.get("opportunity_id", "")))


def dedupe_by_cluster(items: list[dict]) -> list[dict]:
    best_by_cluster: dict[str, dict] = {}
    for item in items:
        cluster_id = item["cluster_id"]
        current = best_by_cluster.get(cluster_id)
        if current is None or _dedupe_key(item) > _dedupe_key(current):
            best_by_cluster[cluster_id] = item
    return list(best_by_cluster.values())


def dedupe_by_content_fingerprint(items: list[dict]) -> list[dict]:
    """Remove duplicates where the first 200 chars of source_text are identical."""
    seen: dict[str, dict] = {}
    for item in items:
        fingerprint = str(item.get("source_text", ""))[:200].strip()
        if not fingerprint:
            continue
        current = seen.get(fingerprint)
        if current is None or _dedupe_key(item) > _dedupe_key(current):
            seen[fingerprint] = item

    no_fp = [item for item in items if not str(item.get("source_text", ""))[:200].strip()]
    return list(seen.values()) + no_fp
