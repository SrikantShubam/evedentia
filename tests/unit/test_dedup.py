from evidentia.scoring import dedupe_by_cluster


def test_dedup_keeps_best_signal_per_cluster():
    inputs = [
        {"opportunity_id": "opp_1", "cluster_id": "c1", "score": 0.3},
        {"opportunity_id": "opp_2", "cluster_id": "c1", "score": 0.7},
    ]

    results = dedupe_by_cluster(inputs)

    assert len(results) == 1
    assert results[0]["opportunity_id"] == "opp_2"


def test_dedup_breaks_equal_score_ties_deterministically():
    inputs = [
        {"opportunity_id": "opp_older", "cluster_id": "c1", "score": 0.7, "published_at": "2026-04-14T08:00:00Z"},
        {"opportunity_id": "opp_newer", "cluster_id": "c1", "score": 0.7, "published_at": "2026-04-14T10:00:00Z"},
    ]

    results = dedupe_by_cluster(inputs)

    assert len(results) == 1
    assert results[0]["opportunity_id"] == "opp_newer"
