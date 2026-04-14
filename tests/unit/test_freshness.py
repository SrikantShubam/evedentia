from evidentia.scoring import apply_freshness_decay, rank_opportunities


def test_freshness_decay_penalizes_older_opportunities():
    newer = {"score": 1.0, "published_at": "2026-04-14T00:00:00Z"}
    older = {"score": 1.0, "published_at": "2026-03-01T00:00:00Z"}

    newer_score = apply_freshness_decay(newer, reference_timestamp="2026-04-14T00:00:00Z")
    older_score = apply_freshness_decay(older, reference_timestamp="2026-04-14T00:00:00Z")

    assert newer_score > older_score


def test_rank_uses_freshness_after_gating():
    opportunities = [
        {
            "opportunity_id": "opp_old",
            "willingness_to_pay": "pass",
            "distribution_channel": "pass",
            "data_feasibility": "pass",
            "competition_gap": 0.8,
            "buildability": 0.8,
            "reachability_strength": 0.8,
            "published_at": "2026-03-01T00:00:00Z",
        },
        {
            "opportunity_id": "opp_new",
            "willingness_to_pay": "pass",
            "distribution_channel": "pass",
            "data_feasibility": "pass",
            "competition_gap": 0.8,
            "buildability": 0.8,
            "reachability_strength": 0.8,
            "published_at": "2026-04-14T00:00:00Z",
        },
    ]

    ranked = rank_opportunities(opportunities, reference_timestamp="2026-04-14T00:00:00Z")

    assert [item["opportunity_id"] for item in ranked] == ["opp_new", "opp_old"]
