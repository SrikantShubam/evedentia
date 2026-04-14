import json

from click.testing import CliRunner

from evidentia.cli import cli


def test_spec_command_writes_structured_spec(tmp_path):
    input_path = tmp_path / "opportunity.json"
    output_path = tmp_path / "spec.json"
    input_path.write_text(
        json.dumps(
            {
                "opportunity_id": "opp_001",
                "title": "Invoice chase automation",
                "verified_signals": [
                    {
                        "source_url": "https://example.com/post",
                        "verbatim_quote": "I need this",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["spec", "--input", str(input_path), "--output", str(output_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["approved"] is False
    assert payload["sources"][0]["source_url"] == "https://example.com/post"


def test_build_command_blocks_unapproved_spec(tmp_path):
    spec_path = tmp_path / "spec.json"
    output_dir = tmp_path / "build"
    spec_path.write_text(
        json.dumps(
            {
                "opportunity_id": "opp_001",
                "title": "Invoice chase automation",
                "approved": False,
                "sources": [],
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["build", "--spec", str(spec_path), "--output-dir", str(output_dir)],
    )

    assert result.exit_code != 0
    assert not (output_dir / "package.json").exists()


def test_build_command_creates_artifact_for_approved_spec(tmp_path):
    spec_path = tmp_path / "spec.json"
    output_dir = tmp_path / "build"
    spec_path.write_text(
        json.dumps(
            {
                "opportunity_id": "opp_001",
                "title": "Invoice chase automation",
                "approved": True,
                "sources": [],
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["build", "--spec", str(spec_path), "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 0
    assert (output_dir / "package.json").exists()


def test_ship_command_blocks_unapproved_spec(tmp_path):
    spec_path = tmp_path / "spec.json"
    deploy_path = tmp_path / "deploy.json"
    spec_path.write_text(
        json.dumps(
            {
                "opportunity_id": "opp_001",
                "title": "Invoice chase automation",
                "approved": False,
                "sources": [],
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["ship", "--spec", str(spec_path), "--output", str(deploy_path)],
    )

    assert result.exit_code != 0
    assert not deploy_path.exists()


def test_ship_command_writes_deployment_metadata_for_approved_spec(tmp_path):
    spec_path = tmp_path / "spec.json"
    deploy_path = tmp_path / "deploy.json"
    spec_path.write_text(
        json.dumps(
            {
                "opportunity_id": "opp_001",
                "title": "Invoice chase automation",
                "approved": True,
                "sources": [],
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["ship", "--spec", str(spec_path), "--output", str(deploy_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(deploy_path.read_text(encoding="utf-8"))
    assert payload["status"] == "deployed"
    assert payload["project_id"] == "opp_001"


def test_track_command_reads_persisted_metrics(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({"visits": 12, "signups": 3, "revenue_proxy": 1}),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["track", "--input", str(metrics_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["visits"] == 12
    assert payload["signups"] == 3
