from evidentia.models import (
    GateResult,
    GateStatus,
    Idea,
    IdeaState,
    KillCondition,
    RoundOutcome,
    TerminalVerdict,
)
from evidentia.tournament.verdict import derive_terminal_verdict


def _state(results: list[GateResult], confidence: float) -> IdeaState:
    idea = Idea(
        id="idea-1",
        label="Idea",
        anchor_slug="anchor",
        incumbent=None,
        cohort="cohort",
        pain_hypothesis="pain",
        kill_condition=KillCondition(description="kill if no market", gate_name="parent_market_exists"),
        evidence_ids=["sig-1"],
        search_queries=["q"],
        origin="manual",
        gate_profile="consumer_app",
        gate_profile_source="explicit",
    )
    return IdeaState(
        idea=idea,
        gate_results=results,
        confidence_score_so_far=confidence,
        is_complete=False,
        terminal_verdict=None,
    )


def _base_pass_results() -> list[GateResult]:
    return [
        GateResult("parent_market_exists", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.95, None, 0.0, None),
        GateResult("niche_not_already_owned", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.9, None, 0.0, None),
        GateResult("complaint_signal_exists", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.8, None, 0.0, None),
        GateResult("three_first_person_voices", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.75, None, 0.0, None),
        GateResult("reachable_channel", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.72, None, 0.0, None),
        GateResult("retention_plausible", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.7, None, 0.0, None),
        GateResult("player_fit", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.8, None, 0.0, None),
        GateResult("willingness_to_pay", GateStatus.COMPLETED, RoundOutcome.PASS, [], 0.75, None, 0.0, None),
    ]


def test_rule_1_structural_fail_is_kill():
    results = _base_pass_results()
    results[1] = GateResult("niche_not_already_owned", GateStatus.COMPLETED, RoundOutcome.FAIL, [], None, None, 0.0, None)
    assert derive_terminal_verdict(_state(results, 0.9)) == TerminalVerdict.KILL


def test_rule_2_evidence_fail_is_insufficient_evidence():
    results = _base_pass_results()
    results[2] = GateResult("complaint_signal_exists", GateStatus.COMPLETED, RoundOutcome.FAIL, [], None, None, 0.0, None)
    assert derive_terminal_verdict(_state(results, 0.9)) == TerminalVerdict.INSUFFICIENT_EVIDENCE


def test_rule_3_unfinished_required_gate_is_insufficient_evidence():
    results = _base_pass_results()
    results[4] = GateResult("reachable_channel", GateStatus.SKIPPED, None, [], None, None, 0.0, None)
    assert derive_terminal_verdict(_state(results, 0.9)) == TerminalVerdict.INSUFFICIENT_EVIDENCE


def test_rule_4_all_pass_with_high_confidence_is_pursue_spike():
    results = _base_pass_results()
    assert derive_terminal_verdict(_state(results, 0.45)) == TerminalVerdict.PURSUE_SPIKE


def test_rule_5_all_pass_with_low_confidence_is_shortlist():
    results = _base_pass_results()
    assert derive_terminal_verdict(_state(results, 0.2)) == TerminalVerdict.SHORTLIST
