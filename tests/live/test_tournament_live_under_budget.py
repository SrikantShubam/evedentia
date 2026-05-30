from __future__ import annotations

import pytest

from evidentia.anchor import load_all_anchors
from evidentia.cli import _run_hunt
from evidentia.models import Idea, KillCondition, PlayerProfile
from evidentia.providers import load_external_provider_env
from evidentia.tournament.engine import run_tournament


@pytest.mark.live
def test_tournament_live_under_budget(monkeypatch, tmp_path):
    env = load_external_provider_env()
    monkeypatch.chdir(tmp_path)

    anchors = load_all_anchors()
    if not anchors:
        pytest.skip("no verifiable anchors available")
    anchor = next((item for item in anchors if item.slug == "bible-study-apps"), anchors[0])
    hunt_payload = _run_hunt(anchor, limit=8, dry_run=False, env=env)
    if hunt_payload["signal_count"] < 3:
        pytest.skip("live harvest returned insufficient signals")

    run_dir = tmp_path / hunt_payload["run_dir"]
    signals_path = run_dir / "signals.json"
    if not signals_path.exists():
        pytest.skip("live hunt did not produce signals artifact")

    import json

    signals = (json.loads(signals_path.read_text(encoding="utf-8")).get("signals") or [])[:4]
    evidence_ids = [str(signal.get("signal_id")) for signal in signals if str(signal.get("signal_id", "")).strip()]
    if len(evidence_ids) < 3:
        pytest.skip("live hunt signals missing stable IDs")

    idea = Idea(
        id="live-idea-1",
        label=f"{anchor.market_name} assistant for narrowed cohort",
        anchor_slug=anchor.slug,
        incumbent=anchor.incumbents[0] if anchor.incumbents else None,
        cohort=(anchor.cohort_hints[0] if anchor.cohort_hints else "power users"),
        pain_hypothesis="Users report recurring workflow friction and are willing to pay for a focused fix.",
        kill_condition=KillCondition(description="No market", gate_name="parent_market_exists"),
        evidence_ids=evidence_ids,
        search_queries=anchor.primary_channel_queries[:2] or [f"{anchor.market_name} recurring complaint"],
        origin="manual",
        gate_profile="consumer_app",
        gate_profile_source="explicit",
    )
    player = PlayerProfile(
        id="live-player",
        team="Edge Agency",
        skills=["python", "sales"],
        budget_validate_usd=3000,
        budget_build_usd=15000,
        budget_reach_usd=2000,
        weeks_to_ship=8,
        risk="med",
        max_llm_calls_per_tournament=40,
        max_paid_queries_per_tournament=15,
    )
    result = run_tournament(
        ideas=[idea],
        player=player,
        tournament_id="live-budget-smoke",
        gate_profile="consumer_app",
    )
    assert result.total_llm_cost_usd <= 5.0
