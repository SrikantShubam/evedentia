import json

from click.testing import CliRunner

from evidentia.cli import cli
from evidentia.providers import ProviderError


def test_scan_command_supports_multi_source_live_mode(monkeypatch, tmp_path):
    output_path = tmp_path / "multi_live_scan.json"

    monkeypatch.setattr(
        "evidentia.cli.run_live_scan",
        lambda domain, sources=None, max_results=3: {
            "opportunities": [
                {
                    "opportunity_id": "opp_001",
                    "title": "Live invoice automation",
                    "verdict": "PURSUE",
                    "score": 0.8,
                    "verified_signals": [
                        {
                            "source": "hn",
                            "source_url": "https://news.ycombinator.com/item?id=1",
                            "verbatim_quote": "would pay for this",
                            "published_at": "2026-04-14T00:00:00Z",
                        },
                        {
                            "source": "reddit",
                            "source_url": "https://www.reddit.com/r/startups/comments/abc123",
                            "verbatim_quote": "would pay for this",
                            "published_at": "2026-04-14T00:00:00Z",
                        },
                    ],
                }
            ],
            "discard_log": [],
        },
    )

    result = CliRunner().invoke(
        cli,
        ["scan", "--live", "--domain", "fintech", "--sources", "hn,reddit", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    sources = {item["source"] for item in payload["opportunities"][0]["verified_signals"]}
    assert sources == {"hn", "reddit"}


def test_scan_command_keeps_partial_results_when_one_live_source_fails(monkeypatch, tmp_path):
    output_path = tmp_path / "partial_live_scan.json"

    def fake_run_live_scan(domain, sources=None, max_results=3):
        return {
            "opportunities": [
                {
                    "opportunity_id": "opp_001",
                    "title": "Live invoice automation",
                    "verdict": "PURSUE",
                    "score": 0.8,
                    "verified_signals": [
                        {
                            "source": "hn",
                            "source_url": "https://news.ycombinator.com/item?id=1",
                            "verbatim_quote": "would pay for this",
                            "published_at": "2026-04-14T00:00:00Z",
                        }
                    ],
                }
            ],
            "discard_log": [],
            "source_attempts": [
                {"source": "hn", "status": "ok", "count": 1},
                {
                    "source": "reddit",
                    "status": "transport_error",
                    "error_type": "ProviderError",
                    "message": "timeout",
                },
            ],
        }

    monkeypatch.setattr("evidentia.cli.run_live_scan", fake_run_live_scan)

    result = CliRunner().invoke(
        cli,
        ["scan", "--live", "--domain", "fintech", "--sources", "hn,reddit", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["opportunities"][0]["verified_signals"][0]["source"] == "hn"
    assert payload["source_attempts"][1]["status"] == "transport_error"
