from evidentia.scoring import rank_opportunities


def test_rank_uses_heuristics_only_after_gates():
    opportunities = [
        {
            "opportunity_id": "opp_a",
            "willingness_to_pay": "pass",
            "distribution_channel": "pass",
            "data_feasibility": "pass",
            "competition_gap": 0.2,
            "buildability": 0.9,
            "reachability_strength": 0.4,
        },
        {
            "opportunity_id": "opp_b",
            "willingness_to_pay": "pass",
            "distribution_channel": "pass",
            "data_feasibility": "pass",
            "competition_gap": 0.9,
            "buildability": 0.3,
            "reachability_strength": 0.8,
        },
    ]

    ranked = rank_opportunities(opportunities)

    assert [item["opportunity_id"] for item in ranked] == ["opp_b", "opp_a"]
    assert ranked[1]["verdict"] == "PURSUE"
    assert ranked[0]["verdict"] == "PURSUE"


def test_rank_does_not_resurrect_failed_gate():
    opportunities = [
        {
            "opportunity_id": "opp_blocked",
            "willingness_to_pay": "fail",
            "distribution_channel": "pass",
            "data_feasibility": "pass",
            "competition_gap": 1.0,
            "buildability": 1.0,
            "reachability_strength": 1.0,
            "published_at": "2026-04-14T00:00:00Z",
        },
        {
            "opportunity_id": "opp_valid",
            "willingness_to_pay": "pass",
            "distribution_channel": "pass",
            "data_feasibility": "pass",
            "competition_gap": 0.1,
            "buildability": 0.1,
            "reachability_strength": 0.1,
            "published_at": "2026-04-13T00:00:00Z",
        },
    ]

    ranked = rank_opportunities(opportunities, reference_timestamp="2026-04-14T00:00:00Z")

    blocked = next(item for item in ranked if item["opportunity_id"] == "opp_blocked")
    assert blocked["verdict"] == "HOLD"
    assert blocked["score"] == 0
