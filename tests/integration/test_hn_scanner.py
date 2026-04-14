from evidentia.scanners.hn import scan_hn_fixture


def test_hn_fixture_returns_verified_candidates():
    results = scan_hn_fixture("tests/fixtures/hn_sample.json")

    assert len(results) >= 1
    assert results[0]["source"] == "hn"
    assert results[0]["source_url"].startswith("https://")
    assert results[0]["verbatim_quote"]
    assert results[0]["published_at"]
    assert results[0]["cluster_id"]
