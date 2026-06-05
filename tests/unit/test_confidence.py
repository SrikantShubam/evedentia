import pytest

from evidentia.models import GateResult, GateStatus, Idea, IdeaState, KillCondition, RoundOutcome
from evidentia.tournament.confidence import clamp_confidence, confidence_product, is_rankable


def _idea_state_with_results(results: list[GateResult], confidence_score_so_far: float = 1.0) -> IdeaState:
    idea = Idea(
        id="idea-1",
        label="Idea",
        anchor_slug="a",
        incumbent=None,
        cohort="cohort",
        pain_hypothesis="pain",
        kill_condition=KillCondition(description="must pass", gate_name="parent_market_exists"),
        evidence_ids=["sig-1"],
        search_queries=["q1"],
        origin="manual",
        gate_profile="agency_service",
        gate_profile_source="explicit",
    )
    return IdeaState(
        idea=idea,
        gate_results=results,
        confidence_score_so_far=confidence_score_so_far,
        is_complete=False,
        terminal_verdict=None,
    )


def test_clamp_confidence():
    assert clamp_confidence(0.2) == 0.5
    assert clamp_confidence(0.9) == 0.9
    assert clamp_confidence(1.3) == 0.95


def test_confidence_product_geometric_mean():
    """confidence_product returns the geometric mean of passed-completed gate confidences."""
    state = _idea_state_with_results(
        [
            GateResult("parent_market_exists", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.9, None, 0.0, None),
            GateResult("repeat_purchase_evidence", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.5, None, 0.0, None),
            GateResult("three_first_person_voices", GateStatus.COMPLETED, RoundOutcome.FAIL, [], None, None, 0.0, None),
        ]
    )
    import math
    expected = math.sqrt(0.9 * 0.5)
    assert confidence_product(state) == pytest.approx(expected, rel=1e-9)


def test_confidence_product_no_passes_returns_zero():
    state = _idea_state_with_results(
        [
            GateResult("parent_market_exists", GateStatus.COMPLETED, RoundOutcome.FAIL, [], None, None, 0.0, None),
        ]
    )
    assert confidence_product(state) == 0.0


def test_confidence_product_single_pass_is_its_own_value():
    state = _idea_state_with_results(
        [
            GateResult("parent_market_exists", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.9, None, 0.0, None),
        ]
    )
    assert confidence_product(state) == 0.9


def test_is_rankable_false_if_required_gate_missing_or_not_completed():
    state = _idea_state_with_results(
        [
            GateResult("parent_market_exists", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.9, None, 0.0, None),
            GateResult("repeat_purchase_evidence", GateStatus.SKIPPED, None, [], None, None, 0.0, None),
        ]
    )
    assert is_rankable(state) is False
