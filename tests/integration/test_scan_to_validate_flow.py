"""End-to-end integration test: keyword → scan → validate → tournament.

Requires:
- SearXNG running at 127.0.0.1:8888
- Default player profile seeded by API startup

Run with: pytest tests/integration/ -v -m integration
Skip with:  pytest -m "not integration"
"""

import pytest
from fastapi.testclient import TestClient


# live: /scan hits real search backends (SearXNG or DDG fallback) — flaky offline/in CI.
pytestmark = [pytest.mark.integration, pytest.mark.live]


# SearXNG may not be running in CI or local dev
# Use --run-integration flag to enable


@pytest.fixture
def client():
    from evidentia.api import create_app
    return TestClient(create_app())


@pytest.fixture
def default_player(client):
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
    assert r.status_code == 200, r.text


def test_scan_web_search_source_returns_200(client):
    """web_search source returns valid scan response structure."""
    r = client.post("/scan", json={
        "keyword": "plastic-free",
        "sources": ["web_search"],
        "max_results": 3,
    })
    assert r.status_code == 200
    data = r.json()
    assert "opportunities" in data
    assert "discard_log" in data
    assert "source_attempts" in data
    assert len(data["source_attempts"]) > 0


def test_keyword_to_scan_to_validate_full_flow(client, default_player):
    """Complete flow: keyword → scan → validate → tournament result."""
    # 1. Scan for a niche keyword
    scan = client.post("/scan", json={
        "keyword": "biodegradable packaging for bakeries",
        "sources": ["web_search"],
        "max_results": 3,
    })
    assert scan.status_code == 200
    opps = scan.json().get("opportunities", [])

    if not opps:
        pytest.skip("SearXNG returned no opportunities for test query")

    # 2. Validate the best opportunity
    best_opp = opps[0]
    val = client.post("/validate", json={
        "keyword": "biodegradable packaging for bakeries",
        "opportunity": best_opp,
        "player_id": "default",
    })
    assert val.status_code == 200
    tournament = val.json()

    # 3. Verify tournament structure
    assert tournament["tournament_id"].startswith("scan-")
    assert len(tournament["ideas"]) >= 1

    idea_state = tournament["ideas"][0]
    assert idea_state["id"] is not None
    assert idea_state["label"] is not None
    assert idea_state.get("terminal_verdict") is not None

    # 4. Verify SSE endpoint exists for this tournament
    sse = client.get(f"/tournament/{tournament['tournament_id']}/sse")
    assert sse.status_code == 200


def test_scan_with_multiple_sources_including_web(client):
    """Scan works with mixed sources (web_search + hn)."""
    r = client.post("/scan", json={
        "keyword": "software",
        "sources": ["web_search", "hn"],
        "max_results": 3,
    })
    assert r.status_code == 200
    attempts = r.json().get("source_attempts", [])
    assert len(attempts) >= 1
    # At least one source should have been attempted
    sources_attempted = {a["source"] for a in attempts}
    assert "web_search" in sources_attempted
