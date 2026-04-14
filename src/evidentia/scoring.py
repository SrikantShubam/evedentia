from datetime import datetime, timezone


HARD_GATES = (
    "willingness_to_pay",
    "distribution_channel",
    "data_feasibility",
)


def score_opportunity(opportunity: dict) -> dict:
    gates = [opportunity[gate] for gate in HARD_GATES]
    if any(gate != "pass" for gate in gates):
        return {
            "verdict": "HOLD",
            "gate_verdict": "HOLD",
            "heuristic_score": 0.0,
            "freshness_factor": 0.0,
            "final_score": 0.0,
            "score": 0.0,
        }

    score = (
        opportunity.get("competition_gap", 0) * 0.4
        + opportunity.get("buildability", 0) * 0.3
        + opportunity.get("reachability_strength", 0) * 0.3
    )
    rounded_score = round(score, 3)
    return {
        "verdict": "PURSUE",
        "gate_verdict": "PURSUE",
        "heuristic_score": rounded_score,
        "freshness_factor": 1.0,
        "final_score": rounded_score,
        "score": rounded_score,
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
        if enriched["verdict"] == "PURSUE":
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
