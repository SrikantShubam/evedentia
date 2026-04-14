from datetime import datetime, timezone


HARD_GATES = (
    "willingness_to_pay",
    "distribution_channel",
    "data_feasibility",
)


def score_opportunity(opportunity: dict) -> dict:
    gates = [opportunity[gate] for gate in HARD_GATES]
    if any(gate != "pass" for gate in gates):
        return {"verdict": "HOLD", "score": 0}

    score = (
        opportunity.get("competition_gap", 0) * 0.4
        + opportunity.get("buildability", 0) * 0.3
        + opportunity.get("reachability_strength", 0) * 0.3
    )
    return {"verdict": "PURSUE", "score": round(score, 3)}


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
    age_days = max((reference - published_at).days, 0)
    decay_factor = max(0.0, 1 - min(age_days, 365) / 365)
    return round(base_score * decay_factor, 3)


def rank_opportunities(opportunities: list[dict], reference_timestamp: str | None = None) -> list[dict]:
    scored = []
    for item in opportunities:
        enriched = dict(item, **score_opportunity(item))
        enriched["score"] = apply_freshness_decay(enriched, reference_timestamp=reference_timestamp)
        scored.append(enriched)
    return sorted(scored, key=lambda item: item["score"], reverse=True)


def dedupe_by_cluster(items: list[dict]) -> list[dict]:
    best_by_cluster: dict[str, dict] = {}
    for item in items:
        cluster_id = item["cluster_id"]
        current = best_by_cluster.get(cluster_id)
        if current is None or item["score"] > current["score"]:
            best_by_cluster[cluster_id] = item
    return list(best_by_cluster.values())
