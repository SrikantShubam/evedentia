import json
from pathlib import Path

from fastapi.testclient import TestClient

from evidentia.api import create_app
from evidentia.cli import cli
from click.testing import CliRunner


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


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def test_api_tournament_end_to_end_and_sse(tmp_path):
    db_path = tmp_path / "evidentia.sqlite3"
    client = TestClient(create_app(db_path=db_path))
    profile = _player_dict()
    idea = _idea_dict()

    post_player = client.post("/player", json=profile)
    assert post_player.status_code == 200
    assert post_player.json()["id"] == profile["id"]

    post_tournament = client.post(
        "/tournament",
        json={
            "tournament_id": "api-t-1",
            "player_id": profile["id"],
            "ideas": [idea],
            "gate_profile": "consumer_app",
        },
    )
    assert post_tournament.status_code == 200
    tournament_payload = post_tournament.json()
    assert tournament_payload["tournament_id"] == "api-t-1"

    memo_response = client.get("/tournament/api-t-1/memo")
    assert memo_response.status_code == 200
    assert "tournament_id" in memo_response.json()

    tournament_response = client.get("/tournament/api-t-1")
    assert tournament_response.status_code == 200
    assert tournament_response.json()["tournament_id"] == "api-t-1"

    idea_response = client.get("/tournament/api-t-1/idea/i-1")
    assert idea_response.status_code == 200
    assert idea_response.json()["idea"]["id"] == "i-1"

    with client.stream("GET", "/tournament/api-t-1/sse") as response:
        assert response.status_code == 200
        body = b"".join(response.iter_bytes())
    text = body.decode("utf-8")
    assert "event: gate" in text
    assert "event: done" in text


def test_api_memo_matches_cli_memo_bytes(tmp_path):
    db_path = tmp_path / "evidentia.sqlite3"
    client = TestClient(create_app(db_path=db_path))
    profile = _player_dict()
    idea = _idea_dict()

    assert client.post("/player", json=profile).status_code == 200
    api_run = client.post(
        "/tournament",
        json={
            "tournament_id": "api-t-2",
            "player_id": profile["id"],
            "ideas": [idea],
            "gate_profile": "consumer_app",
        },
    )
    assert api_run.status_code == 200
    api_memo = client.get("/tournament/api-t-2/memo").json()

    runner = CliRunner()
    profile_path = tmp_path / "profile.json"
    ideas_path = tmp_path / "ideas.jsonl"
    tournament_path = tmp_path / "cli_tournament.json"
    memo_path = tmp_path / "cli_memo.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    ideas_path.write_text(json.dumps(idea) + "\n", encoding="utf-8")

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
            "--tournament-id",
            "api-t-2",
            "--output",
            str(tournament_path),
        ],
    )
    assert run_result.exit_code == 0
    memo_render = runner.invoke(
        cli,
        ["edge", "memo", "render", str(tournament_path), "--format", "json", "--output", str(memo_path)],
    )
    assert memo_render.exit_code == 0
    cli_memo = json.loads(Path(memo_path).read_text(encoding="utf-8"))

    assert _canonical_bytes(api_memo) == _canonical_bytes(cli_memo)
