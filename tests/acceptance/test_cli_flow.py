from click.testing import CliRunner

from evidentia.cli import cli


def test_cli_exposes_scan_spec_build_ship_track():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    for command in ["scan", "spec", "build", "ship", "track"]:
        assert command in result.output
