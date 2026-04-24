import json

from click.testing import CliRunner

from evidentia.cli import cli


def _player_dict(max_reentry_rounds: int = 1, max_llm_calls: int = 200) -> dict:
    return {
        "id": "agency-a",
        "team": "Edge Agency",
        "skills": ["python", "sales"],
        "budget_validate_usd": 2500,
        "budget_build_usd": 10000,
        "budget_reach_usd": 1500,
        "weeks_to_ship": 8,
        "risk": "med",
        "max_reentry_rounds": max_reentry_rounds,
        "max_llm_calls_per_tournament": max_llm_calls,
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


def test_seed_from_requires_narrow_flag(tmp_path):
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"
    ideas_path = tmp_path / "ideas.jsonl"
    parent_path = tmp_path / "parent.json"
    profile_path.write_text(json.dumps(_player_dict(max_llm_calls=1)), encoding="utf-8")
    ideas_path.write_text(json.dumps(_idea_dict()) + "\n", encoding="utf-8")

    run_parent = runner.invoke(
        cli,
        ["edge", "tournament", "run", "--ideas", str(ideas_path), "--player", str(profile_path), "--output", str(parent_path)],
    )
    assert run_parent.exit_code == 0

    seed_result = runner.invoke(
        cli,
        ["edge", "tournament", "run", "--seed-from", str(parent_path), "--player", str(profile_path)],
    )
    assert seed_result.exit_code != 0
    assert "--narrow" in seed_result.output


def test_seed_from_generates_reentry_ideas_when_narrow(tmp_path):
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"
    ideas_path = tmp_path / "ideas.jsonl"
    parent_path = tmp_path / "parent.json"
    child_path = tmp_path / "child.json"
    profile_path.write_text(json.dumps(_player_dict(max_llm_calls=1)), encoding="utf-8")
    ideas_path.write_text(json.dumps(_idea_dict()) + "\n", encoding="utf-8")

    run_parent = runner.invoke(
        cli,
        ["edge", "tournament", "run", "--ideas", str(ideas_path), "--player", str(profile_path), "--output", str(parent_path)],
    )
    assert run_parent.exit_code == 0

    seed_result = runner.invoke(
        cli,
        [
            "edge",
            "tournament",
            "run",
            "--seed-from",
            str(parent_path),
            "--narrow",
            "--player",
            str(profile_path),
            "--output",
            str(child_path),
        ],
    )
    assert seed_result.exit_code == 0
    child_payload = json.loads(child_path.read_text(encoding="utf-8"))
    assert child_payload["reentry_depth"] == 1
    assert child_payload["parent_tournament_id"] == json.loads(parent_path.read_text(encoding="utf-8"))["tournament_id"]
    assert child_payload["ideas"][0]["idea"]["parent_idea_id"] is not None


def test_seed_from_obeys_max_reentry_rounds(tmp_path):
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"
    ideas_path = tmp_path / "ideas.jsonl"
    parent_path = tmp_path / "parent.json"
    profile_path.write_text(json.dumps(_player_dict(max_reentry_rounds=0, max_llm_calls=1)), encoding="utf-8")
    ideas_path.write_text(json.dumps(_idea_dict()) + "\n", encoding="utf-8")

    run_parent = runner.invoke(
        cli,
        ["edge", "tournament", "run", "--ideas", str(ideas_path), "--player", str(profile_path), "--output", str(parent_path)],
    )
    assert run_parent.exit_code == 0

    seed_result = runner.invoke(
        cli,
        ["edge", "tournament", "run", "--seed-from", str(parent_path), "--narrow", "--player", str(profile_path)],
    )
    assert seed_result.exit_code != 0
    assert "max_reentry_rounds" in seed_result.output
