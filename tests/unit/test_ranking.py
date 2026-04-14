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
