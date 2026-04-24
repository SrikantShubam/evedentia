import json

from click.testing import CliRunner

from evidentia.cli import cli


def _player_dict() -> dict:
    return {
        "id": "agency-a",
        "team": "Edge Agency",
        "skills": ["python", "sales"],
        "budget_validate_usd": 2500,
        "budget_build_usd": 10000,
        "budget_reach_usd": 1500,
        "weeks_to_ship": 8,
        "risk": "med",
    }


def test_low_confidence_profile_requires_explicit_profile_flag(tmp_path):
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"
    ideas_path = tmp_path / "ideas.jsonl"
    profile_path.write_text(json.dumps(_player_dict()), encoding="utf-8")
    idea = {
        "id": "i-1",
        "label": "Ops tool",
        "anchor_slug": "ops-tools",
        "incumbent": None,
        "cohort": "agencies",
        "pain_hypothesis": "Teams are willing to pay to reduce manual work.",
        "kill_condition": {"description": "No market", "gate_name": "parent_market_exists"},
        "evidence_ids": ["sig-1", "sig-2", "sig-3"],
        "search_queries": ["agency ops pain"],
        "origin": "manual",
        "gate_profile": "consumer_app",
        "gate_profile_source": "inferred:0.65",
        "parent_idea_id": None,
    }
    ideas_path.write_text(json.dumps(idea) + "\n", encoding="utf-8")

    result = runner.invoke(
        cli,
        [
            "edge",
            "tournament",
            "run",
            "--ideas",
            str(ideas_path),
            "--player",
            str(profile_path),
        ],
    )
    assert result.exit_code != 0
    assert "requires --profile" in result.output
