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


def _manual_idea(evidence_ids: list[str]) -> dict:
    return {
        "id": "i-1",
        "label": "Ops tool",
        "anchor_slug": "ops-tools",
        "incumbent": None,
        "cohort": "agencies",
        "pain_hypothesis": "Teams are willing to pay to reduce manual work.",
        "kill_condition": {"description": "No market", "gate_name": "parent_market_exists"},
        "evidence_ids": evidence_ids,
        "search_queries": ["agency ops pain", "agency ops budget"],
        "origin": "manual",
        "gate_profile": "consumer_app",
        "gate_profile_source": "explicit",
        "parent_idea_id": None,
    }


def test_manual_mode_rejects_empty_evidence_without_discover(tmp_path):
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"
    ideas_path = tmp_path / "ideas.jsonl"
    profile_path.write_text(json.dumps(_player_dict()), encoding="utf-8")
    ideas_path.write_text(json.dumps(_manual_idea([])) + "\n", encoding="utf-8")

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
    assert "MANUAL_IDEA_NO_EVIDENCE_FOUND" in result.output


def test_manual_mode_discovers_evidence_when_flag_enabled(tmp_path):
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"
    ideas_path = tmp_path / "ideas.jsonl"
    tournament_path = tmp_path / "tournament.json"
    profile_path.write_text(json.dumps(_player_dict()), encoding="utf-8")
    ideas_path.write_text(json.dumps(_manual_idea([])) + "\n", encoding="utf-8")

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
            "--discover-evidence",
            "--output",
            str(tournament_path),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(tournament_path.read_text(encoding="utf-8"))
    first_idea = payload["ideas"][0]["idea"]
    assert first_idea["evidence_ids"]
