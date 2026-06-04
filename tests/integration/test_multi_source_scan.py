from evidentia.cli import run_fixture_scan
from evidentia.scanners import LIVE_SCANNERS


def test_multi_source_fixture_scan_aggregates_and_dedupes_sources():
    payload = run_fixture_scan(
        {
            "hn": "tests/fixtures/hn_sample.json",
            "reddit": "tests/fixtures/reddit_sample.json",
            "github": "tests/fixtures/github_sample.json",
        }
    )

    assert len(payload["opportunities"]) >= 2
    observed_sources = {item["source"] for opp in payload["opportunities"] for item in opp["verified_signals"]}
    assert {"hn", "reddit"}.issubset(observed_sources)


def test_live_scanners_registry_is_complete_and_callable():
    assert set(LIVE_SCANNERS.keys()) == {"hn", "reddit", "github", "web_search"}
    for source, fn in LIVE_SCANNERS.items():
        assert callable(fn), f"LIVE_SCANNERS['{source}'] is not callable - got {fn!r}"
