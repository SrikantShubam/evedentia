import json

from click.testing import CliRunner

from evidentia.cli import cli


def test_scan_command_supports_live_mode(monkeypatch, tmp_path):
    output_path = tmp_path / "live_scan.json"

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


def test_scan_command_fails_when_all_live_sources_fail(monkeypatch, tmp_path):
    output_path = tmp_path / "live_scan.json"

    def fake_run_live_scan(domain, sources=None, max_results=3):
        raise Exception("all live sources failed")

    monkeypatch.setattr("evidentia.cli.run_live_scan", fake_run_live_scan)

    result = CliRunner().invoke(
        cli,
        ["scan", "--live", "--domain", "fintech", "--output", str(output_path)],
    )

    assert result.exit_code != 0
    assert not output_path.exists()


def test_scan_command_discards_malformed_live_candidates(monkeypatch, tmp_path):
    output_path = tmp_path / "live_scan.json"

    def fake_run_live_scan(domain, sources=None, max_results=3):
        return {
            "opportunities": [],
            "discard_log": [
                {
                    "source_url": "https://news.ycombinator.com/item?id=1",
                    "verbatim_quote": "would pay for this",
                    "reason": "missing_candidate_field:source_text",
                }
            ],
            "source_attempts": [{"source": "hn", "status": "ok", "count": 1}],
        }

    monkeypatch.setattr("evidentia.cli.run_live_scan", fake_run_live_scan)

    result = CliRunner().invoke(
        cli,
        ["scan", "--live", "--domain", "fintech", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["discard_log"][0]["reason"] == "missing_candidate_field:source_text"
