"""Acceptance tests for edge interrogate and edge bridge commands."""
import json
from pathlib import Path

from click.testing import CliRunner

from evidentia.cli import cli


def _sample_research_report(tmp_path: Path) -> Path:
    report = {
        "query": "test query",
        "competitors_analyzed": ["AppA", "AppB"],
        "total_reviews": 15,
        "complaints": [
            {"review_text": "too expensive", "complaint_type": "PRICING", "severity": 8, "confidence": 0.8},
            {"review_text": "hard to use", "complaint_type": "UX", "severity": 7, "confidence": 0.8},
            {"review_text": "missing export", "complaint_type": "MISSING_FEATURE", "severity": 5, "confidence": 0.8},
        ],
        "barrier_hypotheses": [
            {"description": "High regulation", "barrier_type": "regulation", "confidence": 0.7, "provenance": "LLM_EDUCATED_GUESS"},
        ],
        "top_opportunities": [
            {"gap_description": "Multiple users report PRICING issues", "evidence_count": 3, "severity": "MEDIUM", "exploitability": "MEDIUM"},
        ],
        "provenance_summary": "test provenance",
    }
    path = tmp_path / "research.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def _sample_tournament_payload(tmp_path: Path) -> Path:
    payload = {
        "tournament_id": "t-test",
        "player_id": "p1",
        "ideas": [
            {
                "id": "i-1",
                "label": "Test Idea 1",
                "terminal_verdict": "KILL",
                "gate_results": [
                    {"gate_name": "parent_market_exists", "outcome": "PASS", "evidence_ids": ["sig-1"]},
                    {"gate_name": "niche_not_already_owned", "outcome": "FAIL", "killed_by": "dominant incumbent"},
                ],
            },
            {
                "id": "i-2",
                "label": "Test Idea 2",
                "terminal_verdict": "PURSUE_SPIKE",
                "gate_results": [
                    {"gate_name": "parent_market_exists", "outcome": "PASS", "evidence_ids": ["sig-2"]},
                    {"gate_name": "willingness_to_pay", "outcome": "PASS", "evidence_ids": ["sig-3"]},
                ],
            },
        ],
        "memo": {
            "winner": {"id": "i-2", "label": "Test Idea 2"},
        },
    }
    path = tmp_path / "tournament.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_edge_interrogate_competitors(tmp_path):
    """edge interrogate research.json 'how many competitors' returns count."""
    runner = CliRunner()
    report_path = _sample_research_report(tmp_path)
    result = runner.invoke(cli, ["edge", "interrogate", str(report_path), "how many competitors are there"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["count"] == 2
    assert "AppA" in data["competitors"]


def test_edge_interrogate_why_killed(tmp_path):
    """edge interrogate tournament.json 'why did idea die' returns killed ideas."""
    runner = CliRunner()
    tourney_path = _sample_tournament_payload(tmp_path)
    result = runner.invoke(cli, ["edge", "interrogate", str(tourney_path), "why did i-1 die?"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "killed_ideas" in data
    assert data["killed_ideas"][0]["idea_id"] == "i-1"
    assert data["killed_ideas"][0]["failed_gates"][0]["gate"] == "niche_not_already_owned"


def test_edge_interrogate_winner(tmp_path):
    """edge interrogate tournament.json 'who won' returns winner."""
    runner = CliRunner()
    tourney_path = _sample_tournament_payload(tmp_path)
    result = runner.invoke(cli, ["edge", "interrogate", str(tourney_path), "who won"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["winner"]["id"] == "i-2"


def test_edge_bridge_creates_ideas(tmp_path):
    """edge bridge research.json --output ideas.jsonl creates valid ideas."""
    runner = CliRunner()
    report_path = _sample_research_report(tmp_path)
    output_path = tmp_path / "ideas.jsonl"
    result = runner.invoke(cli, ["edge", "bridge", str(report_path), "--output", str(output_path)])
    assert result.exit_code == 0
    assert "1 ideas written" in result.output

    lines = output_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    idea = json.loads(lines[0])
    assert idea["id"] == "research-0"
    assert idea["origin"] == "research_bridge"


def test_edge_bridge_empty_report(tmp_path):
    """edge bridge on report with no opportunities raises error."""
    runner = CliRunner()
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"query": "test", "top_opportunities": []}), encoding="utf-8")
    result = runner.invoke(cli, ["edge", "bridge", str(empty), "--output", str(tmp_path / "out.jsonl")])
    assert result.exit_code != 0
