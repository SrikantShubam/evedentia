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


def _idea_dict() -> dict:
    return {
        "id": "i-1",
        "label": "Agency onboarding assistant",
        "anchor_slug": "onboarding-tools",
        "incumbent": "IncumbentX",
        "cohort": "small agencies",
        "pain_hypothesis": "Teams are willing to pay monthly to reduce onboarding errors and manual work.",
        "kill_condition": {"description": "No market", "gate_name": "parent_market_exists"},
        "evidence_ids": ["sig-1", "sig-2", "sig-3", "sig-4"],
        "search_queries": ["agency onboarding budget", "agency onboarding complaints"],
        "origin": "manual",
        "gate_profile": "consumer_app",
        "gate_profile_source": "explicit",
        "parent_idea_id": None,
    }


def test_tournament_run_writes_events_ndjson(tmp_path):
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"
    ideas_path = tmp_path / "ideas.jsonl"
    tournament_path = tmp_path / "out" / "tournament.json"
    profile_path.write_text(json.dumps(_player_dict()), encoding="utf-8")
    ideas_path.write_text(json.dumps(_idea_dict()) + "\n", encoding="utf-8")

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
            "--output",
            str(tournament_path),
        ],
    )
    assert result.exit_code == 0
    events_path = tournament_path.parent / "events.ndjson"
    assert events_path.exists()
    lines = [line for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    first = json.loads(lines[0])
    assert "gate_name" in first
    assert "status" in first
    assert "idea_id" in first
