import json

from click.testing import CliRunner

from evidentia.cli import cli


def test_scan_command_writes_ranked_verified_opportunities(tmp_path):
    output_path = tmp_path / "scan_output.json"

    result = CliRunner().invoke(
        cli,
        ["scan", "--fixture", "tests/fixtures/hn_sample.json", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(payload["opportunities"]) == 1
    top = payload["opportunities"][0]
    assert top["verdict"] == "PURSUE"
    assert top["score"] > 0
    assert top["verified_signals"][0]["source_url"].startswith("https://")
    assert top["verified_signals"][0]["verbatim_quote"]


def test_scan_command_records_discards_and_blocks_non_pursue_inputs(tmp_path):
    output_path = tmp_path / "scan_output.json"

    result = CliRunner().invoke(
        cli,
        ["scan", "--fixture", "tests/fixtures/hn_bad_sample.json", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["discard_log"] == [
        {
            "source_url": "https://news.ycombinator.com/item?id=3",
            "verbatim_quote": "Missing from the page",
            "reason": "quote_not_found",
        }
    ]
    assert [item["verdict"] for item in payload["opportunities"]] == ["HOLD"]
