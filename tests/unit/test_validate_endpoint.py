"""Tests for the POST /validate endpoint.

Verifies:
- Scan opportunities are correctly mapped to Idea objects
- Tournament is created and gate prosecution runs
- Error cases return appropriate HTTP status codes
- Edge cases (minimal fields, label fallback, evidence ID generation)
"""

import pytest
from fastapi.testclient import TestClient


# --- Fixtures ---

@pytest.fixture
def client():
    """FastAPI TestClient with fresh in-memory DB."""
    from evidentia.api import create_app
    app = create_app()
    return TestClient(app)


@pytest.fixture
def default_player(client):
    """Ensure the 'default' player profile exists."""
    r = client.post("/player", json={
        "id": "default",
        "team": "test",
        "skills": ["research"],
        "budget_validate_usd": 500,
        "budget_build_usd": 2000,
        "budget_reach_usd": 300,
        "weeks_to_ship": 8,
        "risk": "low",
    })
    assert r.status_code == 200, f"Failed to create default player: {r.text}"
    return r.json()


def _opp(**overrides):
    """Build a minimal but valid scan opportunity dict."""
    data = {
        "opportunity_id": "test-opp-1",
        "title": "Biodegradable packaging for bakeries",
        "hypothesis": {
            "headline": "Eco packaging for small bakeries",
            "wedge_statement": "Bakeries need cheap biodegradable packaging",
            "hypothesis_type": "replacement_wedge",
        },
        "verdict": "REFINE",
        "final_score": 0.72,
        "verified_signals": [{"source_url": "https://example.com/a"}],
        "gate_failures": ["distribution_channel"],
    }
    data.update(overrides)
    return data


# --- Happy Path ---

def test_validate_constructs_idea_and_returns_tournament(client, default_player):
    """Valid opportunity → 200 with tournament result."""
    r = client.post("/validate", json={
        "keyword": "plastic-free packaging",
        "opportunity": _opp(),
        "player_id": "default",
    })
    assert r.status_code == 200, r.text
    data = r.json()

    assert "tournament_id" in data
    assert len(data["ideas"]) == 1

    idea_state = data["ideas"][0]
    assert idea_state["id"] == "test-opp-1"
    assert idea_state["label"] == "Eco packaging for small bakeries"
    assert idea_state["terminal_verdict"] is not None


def test_validate_tournament_id_is_unique(client, default_player):
    """Two calls produce different tournament IDs."""
    r1 = client.post("/validate", json={
        "keyword": "test",
        "opportunity": _opp(opportunity_id="a1"),
        "player_id": "default",
    })
    r2 = client.post("/validate", json={
        "keyword": "test",
        "opportunity": _opp(opportunity_id="a2"),
        "player_id": "default",
    })
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["tournament_id"] != r2.json()["tournament_id"]


# --- Error Cases ---

def test_validate_missing_player_returns_404(client):
    """Unknown player_id → 404."""
    r = client.post("/validate", json={
        "keyword": "test",
        "opportunity": _opp(),
        "player_id": "nonexistent_player_xyz",
    })
    assert r.status_code == 404


def test_validate_empty_keyword_rejected(client):
    """Empty keyword → 400 or 422."""
    r = client.post("/validate", json={
        "keyword": "",
        "opportunity": _opp(),
    })
    assert r.status_code in (400, 422)


# --- Field Mapping ---

def test_validate_label_falls_back_to_title(client, default_player):
    """When no label or hypothesis.headline, title is used."""
    r = client.post("/validate", json={
        "keyword": "test",
        "opportunity": _opp(
            hypothesis=None,  # no hypothesis
        ),
        "player_id": "default",
    })
    assert r.status_code == 200
    idea_state = r.json()["ideas"][0]
    assert idea_state["label"] == "Biodegradable packaging for bakeries"


def test_validate_minimal_opportunity_still_works(client, default_player):
    """Opportunity with only title + verdict still produces valid Idea."""
    r = client.post("/validate", json={
        "keyword": "something-niche",
        "opportunity": {
            "title": "Just a title",
            "verdict": "KILL",
            "final_score": 0.0,
        },
        "player_id": "default",
    })
    assert r.status_code == 200
    idea_state = r.json()["ideas"][0]
    assert idea_state["label"] == "Just a title"
    assert idea_state.get("cohort") == "unknown"

    # Check nested idea dict
    nested = idea_state.get("idea", {})
    assert nested.get("anchor_slug") == "something-niche"
    assert nested.get("origin") == "scan"


def test_validate_cohort_from_hypothesis_type(client, default_player):
    """cohort comes from hypothesis.hypothesis_type."""
    r = client.post("/validate", json={
        "keyword": "test",
        "opportunity": _opp(),
        "player_id": "default",
    })
    assert r.status_code == 200
    nested = r.json()["ideas"][0].get("idea", {})
    assert nested.get("cohort") == "replacement_wedge"


def test_validate_evidence_ids_from_signals(client, default_player):
    """evidence_ids are generated from verified_signals count."""
    r = client.post("/validate", json={
        "keyword": "test",
        "opportunity": _opp(verified_signals=[
            {"source_url": "https://a.com"},
            {"source_url": "https://b.com"},
            {"source_url": "https://c.com"},
        ]),
        "player_id": "default",
    })
    assert r.status_code == 200
    nested = r.json()["ideas"][0].get("idea", {})
    eids = nested.get("evidence_ids", [])
    assert len(eids) == 3
    assert "sig-1" in eids
    assert "sig-3" in eids


def test_validate_evidence_ids_default_when_no_signals(client, default_player):
    """evidence_ids defaults to ['sig-1'] when no verified_signals."""
    r = client.post("/validate", json={
        "keyword": "test",
        "opportunity": _opp(verified_signals=[]),
        "player_id": "default",
    })
    assert r.status_code == 200
    nested = r.json()["ideas"][0].get("idea", {})
    assert nested.get("evidence_ids") == ["sig-1"]


def test_validate_kill_condition_from_verdict(client, default_player):
    """kill_condition.description includes the scan verdict."""
    r = client.post("/validate", json={
        "keyword": "test",
        "opportunity": _opp(verdict="REFINE", final_score=0.65),
        "player_id": "default",
    })
    assert r.status_code == 200
    nested = r.json()["ideas"][0].get("idea", {})
    kc = nested.get("kill_condition", {})
    assert "REFINE" in str(kc.get("description", ""))
    assert "0.65" in str(kc.get("description", ""))


def test_validate_kill_condition_gate_name_from_failures(client, default_player):
    """kill_condition.gate_name comes from gate_failures[0]."""
    r = client.post("/validate", json={
        "keyword": "test",
        "opportunity": _opp(gate_failures=["willingness_to_pay"]),
        "player_id": "default",
    })
    assert r.status_code == 200
    nested = r.json()["ideas"][0].get("idea", {})
    assert nested.get("kill_condition", {}).get("gate_name") == "willingness_to_pay"
    assert nested.get("origin") == "scan"
    assert nested.get("gate_profile") == "consumer_app"
    assert nested.get("gate_profile_source") == "inferred:scan"
    assert nested.get("search_queries") == ["test"]


def test_validate_origin_is_always_scan(client, default_player):
    """Constructed Idea always has origin='scan'."""
    r = client.post("/validate", json={
        "keyword": "anything",
        "opportunity": _opp(),
        "player_id": "default",
    })
    assert r.status_code == 200
    nested = r.json()["ideas"][0].get("idea", {})
    assert nested.get("origin") == "scan"
