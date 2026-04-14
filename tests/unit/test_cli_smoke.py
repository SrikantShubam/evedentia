from click.testing import CliRunner

from evidentia.cli import cli


def test_cli_help_renders():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "scan" in result.output
