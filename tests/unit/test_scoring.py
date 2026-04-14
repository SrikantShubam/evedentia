from evidentia.scoring import score_opportunity


def test_hard_gate_failure_blocks_score():
    opportunity = {
        "willingness_to_pay": "fail",
        "distribution_channel": "pass",
        "data_feasibility": "pass",
    }

    result = score_opportunity(opportunity)

    assert result["verdict"] == "HOLD"
    assert result["score"] == 0


def test_pursue_requires_all_three_gates():
    opportunity = {
        "willingness_to_pay": "pass",
        "distribution_channel": "pass",
        "data_feasibility": "pass",
        "competition_gap": 0.8,
        "buildability": 0.6,
        "reachability_strength": 0.7,
    }

    result = score_opportunity(opportunity)

    assert result["verdict"] == "PURSUE"
    assert result["score"] > 0
