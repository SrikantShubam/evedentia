from click.testing import CliRunner

from evidentia.cli import cli


def test_cli_help_renders():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "scan" in result.output
    assert "audit" in result.output
    assert "classify" in result.output
    assert "score" in result.output
