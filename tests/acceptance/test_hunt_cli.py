from __future__ import annotations

import json

from click.testing import CliRunner

from evidentia.cli import cli


def test_hunt_dry_run_writes_artifacts(tmp_path, monkeypatch):
    anchor_dir = tmp_path / "anchors"
    anchor_dir.mkdir(parents=True, exist_ok=True)
    (anchor_dir / "fixture-anchor.yaml").write_text(
        """
slug: fixture-anchor
market_name: Fixture Market
incumbents: [FixtureApp]
proof_of_market:
  verbatim_quote: "Fixture market exists"
  source_url: https://example.com/proof
  timestamp: 2026-04-17T00:00:00Z
cohort_hints: [women]
primary_channel_queries:
  - "site:reddit.com/r/fixtureapp missing feature"
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("evidentia.cli.anchors_root", lambda: anchor_dir)

    result = CliRunner().invoke(cli, ["hunt", "fixture-anchor", "--dry-run", "--limit", "5"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    run_dir = tmp_path / payload["run_dir"]
    for filename in ("anchor.json", "signals.json", "slices.json", "verdicts.json", "discard_log.json", "summary.md"):
        assert (run_dir / filename).exists(), filename
