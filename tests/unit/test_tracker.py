from evidentia.tracker import empty_metrics, load_metrics, save_metrics


def test_metrics_shape():
    metrics = empty_metrics()
    assert metrics["visits"] == 0
    assert metrics["signups"] == 0


def test_metrics_round_trip(tmp_path):
    path = tmp_path / "metrics.json"
    payload = {"visits": 4, "signups": 2, "revenue_proxy": 1}

    save_metrics(path, payload)

    assert load_metrics(str(path)) == payload
