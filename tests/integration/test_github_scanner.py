from evidentia.scanners.github import scan_github_fixture


def test_github_fixture_returns_candidates_with_traceability():
    results = scan_github_fixture("tests/fixtures/github_sample.json")

    assert len(results) == 1
    assert results[0]["source"] == "github"
    assert results[0]["source_url"].startswith("https://")
    assert results[0]["verbatim_quote"]
