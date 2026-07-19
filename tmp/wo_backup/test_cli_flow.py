from click.testing import CliRunner

from evidentia.cli import cli


def test_cli_exposes_core_commands_only():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    for command in ["scan", "audit", "classify", "score"]:
        assert command in result.output
    for removed in ["spec", "build", "ship", "track"]:
        assert removed not in result.output
