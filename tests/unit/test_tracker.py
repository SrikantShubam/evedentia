from evidentia.tracker import empty_metrics, load_metrics, save_metrics


def test_metrics_shape():
    metrics = empty_metrics()
    assert metrics["visits"] == 0
    assert metrics["signups"] == 0


def test_metrics_round_trip(tmp_path):
    path = tmp_path / "metrics.json"
    payload = {"visits": 4, "signups": 2, "revenue_proxy": 1}

    save_metrics(path, payload)

    loaded = load_metrics(str(path))

    assert loaded["status"] == "ok"
    assert loaded["metrics"] == payload
    assert loaded["missing_fields"] == []


def test_load_metrics_rejects_missing_required_keys(tmp_path):
    path = tmp_path / "metrics.json"
    save_metrics(path, {"visits": 4, "signups": 2})

    try:
        load_metrics(str(path))
    except ValueError as exc:
        assert "missing required metrics" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_load_metrics_preserves_partial_report_metadata(tmp_path):
    path = tmp_path / "metrics.json"
    save_metrics(
        path,
        {
            "status": "partial",
            "proof_level": "dry-run",
            "metrics": {"visits": 4, "signups": 2},
            "missing_fields": ["revenue_proxy"],
        },
    )

    loaded = load_metrics(str(path))

    assert loaded["status"] == "partial"
    assert loaded["proof_level"] == "dry-run"
    assert loaded["missing_fields"] == ["revenue_proxy"]
