import pytest

from evidentia.models import GateResult, GateStatus, Idea, IdeaState, KillCondition, RoundOutcome
from evidentia.tournament.diagnosis import zero_winner_diagnosis


def _state_with_fails(fails: list[str]) -> IdeaState:
    idea = Idea(
        id="i",
        label="Idea",
        anchor_slug="a",
        incumbent=None,
        cohort="c",
        pain_hypothesis="p",
        kill_condition=KillCondition(description="d", gate_name="parent_market_exists"),
        evidence_ids=["e1"],
        search_queries=["q"],
        origin="manual",
        gate_profile="consumer_app",
        gate_profile_source="explicit",
    )
    results = [
        GateResult(g, GateStatus.COMPLETED, RoundOutcome.FAIL, [], None, g, 0.0, None)
        for g in fails
    ]
    return IdeaState(idea=idea, gate_results=results, confidence_score_so_far=0.0, is_complete=True, terminal_verdict=None)


def test_diagnosis_counts_all_failed_gates():
    """Each failing gate is counted, not just the first per state."""
    states = [
        _state_with_fails(["niche_not_already_owned", "willingness_to_pay"]),
        _state_with_fails(["niche_not_already_owned"]),
    ]
    result = zero_winner_diagnosis(states)
    assert "niche_not_already_owned" in result
    # Total gate failures across all states should be 3 (2 niche + 1 wtp)
    assert "Total gate failures: 3" in result


def test_diagnosis_no_fails_returns_skipped_message():
    """When no gates failed, the message mentions skipped/errored."""
    idea = Idea(
        id="i",
        label="Idea",
        anchor_slug="a",
        incumbent=None,
        cohort="c",
        pain_hypothesis="p",
        kill_condition=KillCondition(description="d", gate_name="parent_market_exists"),
        evidence_ids=["e1"],
        search_queries=["q"],
        origin="manual",
        gate_profile="consumer_app",
        gate_profile_source="explicit",
    )
    state = IdeaState(idea=idea, gate_results=[], confidence_score_so_far=0.0, is_complete=False, terminal_verdict=None)
    result = zero_winner_diagnosis([state])
    assert "skipped" in result or "errored" in result
