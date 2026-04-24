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


def test_edge_memo_render_json_and_md(tmp_path):
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"
    ideas_path = tmp_path / "ideas.jsonl"
    tournament_path = tmp_path / "tournament.json"
    memo_json_path = tmp_path / "memo.json"
    memo_md_path = tmp_path / "memo.md"

    profile_path.write_text(json.dumps(_player_dict()), encoding="utf-8")
    ideas_path.write_text(json.dumps(_idea_dict()) + "\n", encoding="utf-8")

    run_result = runner.invoke(
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
    assert run_result.exit_code == 0

    json_result = runner.invoke(
        cli,
        ["edge", "memo", "render", str(tournament_path), "--format", "json", "--output", str(memo_json_path)],
    )
    assert json_result.exit_code == 0
    memo_payload = json.loads(memo_json_path.read_text(encoding="utf-8"))
    assert "tournament_id" in memo_payload

    md_result = runner.invoke(
        cli,
        ["edge", "memo", "render", str(tournament_path), "--format", "md", "--output", str(memo_md_path)],
    )
    assert md_result.exit_code == 0
    md_text = memo_md_path.read_text(encoding="utf-8")
    assert "Decision Memo" in md_text
    assert "LLM_GENERATED_TACTICAL_COPY" in md_text
