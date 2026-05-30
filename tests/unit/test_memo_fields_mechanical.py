from evidentia.models import (
    GateResult,
    GateStatus,
    Idea,
    IdeaState,
    KillCondition,
    RoundOutcome,
    TerminalVerdict,
)
from evidentia.tournament.memo import build_decision_memo


def _state(
    idea_id: str,
    confidence: float,
    verdict: TerminalVerdict,
    gates: list[GateResult],
) -> IdeaState:
    idea = Idea(
        id=idea_id,
        label=f"idea {idea_id}",
        anchor_slug="anchor",
        incumbent="IncumbentX",
        cohort="small agencies",
        pain_hypothesis="Teams are willing to pay monthly.",
        kill_condition=KillCondition(description="No market", gate_name="parent_market_exists"),
        evidence_ids=["sig-1", "sig-2", "sig-3"],
        search_queries=["query one"],
        origin="manual",
        gate_profile="consumer_app",
        gate_profile_source="explicit",
    )
    return IdeaState(
        idea=idea,
        gate_results=gates,
        confidence_score_so_far=confidence,
        is_complete=True,
        terminal_verdict=verdict,
    )


def test_memo_fields_are_mechanical_and_evidence_linked():
    winner = _state(
        "winner",
        0.42,
        TerminalVerdict.PURSUE_SPIKE,
        [
            GateResult("parent_market_exists", GateStatus.COMPLETED, RoundOutcome.PASS, ["sig-parent"], 0.9, None, 0.0, None),
            GateResult("reachable_channel", GateStatus.COMPLETED, RoundOutcome.PASS, ["sig-reach"], 0.65, None, 0.0, None),
            GateResult("willingness_to_pay", GateStatus.COMPLETED, RoundOutcome.PASS, ["sig-pay"], 0.8, None, 0.0, None),
        ],
    )
    runner_up = _state(
        "runner",
        0.31,
        TerminalVerdict.SHORTLIST,
        [
            GateResult("parent_market_exists", GateStatus.COMPLETED, RoundOutcome.PASS, ["sig-r-parent"], 0.88, None, 0.0, None),
            GateResult("reachable_channel", GateStatus.COMPLETED, RoundOutcome.PASS, ["sig-r-reach"], 0.7, None, 0.0, None),
        ],
    )

    memo = build_decision_memo(
        tournament_id="t-1",
        player_id="p-1",
        states=[winner, runner_up],
        winner=winner,
    )

    assert "confidence_delta=" in memo.why_winner_beat_alternatives
    assert "pass_gate_delta=" in memo.why_winner_beat_alternatives
    assert "winner_gate=parent_market_exists" in memo.strongest_argument_for
    assert "evidence_id=sig-parent" in memo.strongest_argument_for
    assert "winner_gate=reachable_channel" in memo.strongest_argument_against
    assert any("gate=reachable_channel" in item for item in memo.missing_evidence_checklist)


def test_zero_winner_memo_has_diagnosis():
    killed = _state(
        "k-1",
        0.0,
        TerminalVerdict.KILL,
        [GateResult("niche_not_already_owned", GateStatus.COMPLETED, RoundOutcome.FAIL, [], None, "niche_not_already_owned", 0.0, None)],
    )
    memo = build_decision_memo(
        tournament_id="t-2",
        player_id="p-2",
        states=[killed],
        winner=None,
    )
    assert memo.winner is None
    assert memo.zero_winner_diagnosis is not None
