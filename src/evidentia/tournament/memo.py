from __future__ import annotations

from evidentia.models import DecisionMemo, IdeaState, RealitySpike, TerminalVerdict
from evidentia.tournament.diagnosis import zero_winner_diagnosis


def _build_reality_spike(winner: IdeaState) -> RealitySpike:
    return RealitySpike(
        idea_id=winner.idea.id,
        target_customer_profile=winner.idea.cohort,
        outreach_message=f"Quick interview request for {winner.idea.label}",
        landing_page_headline=winner.idea.label,
        landing_page_subhead=winner.idea.pain_hypothesis,
        interview_questions=[
            "What is your current workaround?",
            "How often does this happen per week?",
            "What did you try before this?",
            "What would make you switch immediately?",
            "What budget range feels reasonable?",
        ],
        success_criteria="At least 5 qualified prospects confirm pain and budget intent.",
        fail_criteria="Fewer than 2 qualified prospects confirm urgency or budget.",
        weeks_to_run=2,
    )


def build_decision_memo(
    *,
    tournament_id: str,
    player_id: str,
    states: list[IdeaState],
    winner: IdeaState | None,
) -> DecisionMemo:
    shortlist = [state for state in states if state.terminal_verdict == TerminalVerdict.SHORTLIST]
    insufficient = [state for state in states if state.terminal_verdict == TerminalVerdict.INSUFFICIENT_EVIDENCE]
    killed = [state for state in states if state.terminal_verdict == TerminalVerdict.KILL]
    why = "No winner selected."
    arg_for = "No winner evidence available."
    arg_against = "No winner available."
    checklist = ["Collect stronger first-person spend evidence for weak gates."]
    spike = None
    diagnosis = None

    if winner is not None:
        why = f"{winner.idea.id} led on confidence score ({winner.confidence_score_so_far:.3f}) with full gate completion."
        arg_for = f"Highest confidence path came from {winner.idea.label}."
        arg_against = "Lowest-confidence passed gate needs stronger spend validation."
        checklist = ["Add direct buyer budget quotes", "Add alternate channel validation"]
        if winner.terminal_verdict == TerminalVerdict.PURSUE_SPIKE:
            spike = _build_reality_spike(winner)
    else:
        diagnosis = zero_winner_diagnosis(states)

    return DecisionMemo(
        tournament_id=tournament_id,
        player_id=player_id,
        winner=winner,
        shortlist=shortlist,
        insufficient_evidence=insufficient,
        killed=killed,
        why_winner_beat_alternatives=why,
        strongest_argument_for=arg_for,
        strongest_argument_against=arg_against,
        missing_evidence_checklist=checklist,
        reality_spike=spike,
        zero_winner_diagnosis=diagnosis,
    )
