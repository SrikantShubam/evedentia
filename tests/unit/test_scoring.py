def _base_opp(**overrides):
    base = {
        "cluster_id": "c1",
        "source_url": "https://x/y",
        "timestamp": "2026-04-01T00:00:00Z",
        "willingness_to_pay": "pass",
        "distribution_channel": "pass",
        "data_feasibility": "pass",
        "competition_gap": 0.7,
        "buildability": 0.7,
        "reachability_strength": 0.7,
        "verified": True,
    }
    base.update(overrides)
    return base


def test_scoring_verdict_pursue():
    from evidentia.scoring import score_opportunity

    out = score_opportunity(_base_opp())
    assert out["verdict"] == "PURSUE"


def test_scoring_verdict_refine_weak_heuristics():
    from evidentia.scoring import score_opportunity

    out = score_opportunity(_base_opp(competition_gap=0.1, buildability=0.2, reachability_strength=0.3))
    assert out["verdict"] == "REFINE"
    assert out["refine_reason"] is not None


def test_scoring_verdict_refine_gate_fail_soft():
    from evidentia.scoring import score_opportunity

    out = score_opportunity(_base_opp(willingness_to_pay="fail"))
    assert out["verdict"] == "REFINE"


def test_scoring_verdict_kill_total_fail():
    from evidentia.scoring import score_opportunity

    out = score_opportunity(
        _base_opp(
            willingness_to_pay="fail",
            distribution_channel="fail",
            data_feasibility="fail",
            competition_gap=0.0,
            buildability=0.0,
            reachability_strength=0.0,
        )
    )
    assert out["verdict"] == "KILL"
