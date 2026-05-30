import json

import pytest
from click.testing import CliRunner

from evidentia.cli import cli
from evidentia.models import Idea, KillCondition, PlayerProfile
from evidentia.outputs import read_player_profile, write_player_profile


def _sample_profile_dict() -> dict:
    return {
        "id": "agency-a",
        "team": "Edge Agency",
        "skills": ["python", "ads"],
        "budget_validate_usd": 2500,
        "budget_build_usd": 10000,
        "budget_reach_usd": 1500,
        "weeks_to_ship": 8,
        "risk": "med",
    }


def test_player_profile_roundtrip_file(tmp_path):
    profile = PlayerProfile(**_sample_profile_dict())
    output_path = tmp_path / "profile.json"

    write_player_profile(output_path, profile)
    loaded = read_player_profile(output_path)

    assert loaded.id == profile.id
    assert loaded.team == profile.team
    assert loaded.max_llm_calls_per_tournament == 200


def test_player_profile_rejects_invalid_risk():
    payload = _sample_profile_dict()
    payload["risk"] = "unknown"
    with pytest.raises(ValueError):
        PlayerProfile(**payload)


def test_idea_requires_evidence_ids():
    with pytest.raises(ValueError):
        Idea(
            id="idea-1",
            label="Label",
            anchor_slug="anchor-x",
            incumbent=None,
            cohort="agencies",
            pain_hypothesis="Manual workflow is expensive.",
            kill_condition=KillCondition(description="No repeat buyer", gate_name="repeat_purchase_evidence"),
            evidence_ids=[],
            search_queries=["agency workflow pain"],
            origin="manual",
            gate_profile="agency_service",
            gate_profile_source="explicit",
        )


def test_edge_player_commands_roundtrip(tmp_path):
    runner = CliRunner()
    source_path = tmp_path / "input_profile.json"
    output_path = tmp_path / "outputs" / "profile.json"
    source_path.write_text(json.dumps(_sample_profile_dict()), encoding="utf-8")

    init_result = runner.invoke(
        cli,
        ["edge", "player", "init-from-file", str(source_path), "--output", str(output_path)],
    )
    assert init_result.exit_code == 0
    assert output_path.exists()

    show_result = runner.invoke(
        cli,
        ["edge", "player", "show", "--profile", str(output_path)],
    )
    assert show_result.exit_code == 0
    parsed = json.loads(show_result.output)
    assert parsed["id"] == "agency-a"
    assert parsed["weeks_to_ship"] == 8
