import json

from click.testing import CliRunner

from evidentia.cli import cli


def test_scan_command_supports_live_mode(monkeypatch, tmp_path):
    output_path = tmp_path / "live_scan.json"

    monkeypatch.setattr(
        "evidentia.cli.run_live_scan",
        lambda domain, max_results=3: {
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
        },
    )

    result = CliRunner().invoke(
        cli,
        ["scan", "--live", "--domain", "fintech", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["opportunities"][0]["verdict"] == "PURSUE"
