"""Acceptance test: edge research CLI command."""
import json

from click.testing import CliRunner

from evidentia.cli import cli


def test_edge_research_help():
    """edge research --help should show usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["edge", "research", "--help"])
    assert result.exit_code == 0
    assert "query" in result.output.lower() or "QUERY" in result.output


def test_edge_research_dry_run_no_env():
    """edge research without env vars should still complete (partial results)."""
    runner = CliRunner()
    # Run without any API keys — should return partial results, not crash
    result = runner.invoke(
        cli,
        ["edge", "research", "test query", "--max-competitors", "1"],
    )
    # Should NOT crash — partial results with empty report is acceptable
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "query" in payload
    assert payload["query"] == "test query"
