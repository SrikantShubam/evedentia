from evidentia.cli import run_fixture_scan


def test_multi_source_fixture_scan_aggregates_and_dedupes_sources():
    payload = run_fixture_scan(
        {
            "hn": "tests/fixtures/hn_sample.json",
            "reddit": "tests/fixtures/reddit_sample.json",
            "github": "tests/fixtures/github_sample.json",
        }
    )

    assert len(payload["opportunities"]) == 3
    assert {item["source"] for opp in payload["opportunities"] for item in opp["verified_signals"]} == {
        "hn",
        "reddit",
        "github",
    }
