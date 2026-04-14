from evidentia.scanners.reddit import scan_reddit_fixture


def test_reddit_fixture_returns_candidates_with_traceability():
    results = scan_reddit_fixture("tests/fixtures/reddit_sample.json")

    assert len(results) == 1
    assert results[0]["source"] == "reddit"
    assert results[0]["source_url"].startswith("https://")
    assert results[0]["verbatim_quote"]
