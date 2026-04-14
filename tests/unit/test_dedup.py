from evidentia.scoring import dedupe_by_cluster


def test_dedup_keeps_best_signal_per_cluster():
    inputs = [
        {"opportunity_id": "opp_1", "cluster_id": "c1", "score": 0.3},
        {"opportunity_id": "opp_2", "cluster_id": "c1", "score": 0.7},
    ]

    results = dedupe_by_cluster(inputs)

    assert len(results) == 1
    assert results[0]["opportunity_id"] == "opp_2"
