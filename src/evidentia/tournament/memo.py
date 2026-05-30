from __future__ import annotations

from evidentia.models import (
    DecisionMemo,
    GateStatus,
    IdeaState,
    RealitySpike,
    RoundOutcome,
    TerminalVerdict,
)
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


def _passed_gates(state: IdeaState) -> list:
    return [
        gate
        for gate in state.gate_results
        if gate.status == GateStatus.COMPLETED and gate.outcome == RoundOutcome.PASS
    ]


def _highest_conf_gate(state: IdeaState):
    passed = [gate for gate in _passed_gates(state) if gate.confidence is not None]
    if not passed:
        return None
    return max(passed, key=lambda gate: gate.confidence or 0.0)


def _lowest_conf_gate(state: IdeaState):
    passed = [gate for gate in _passed_gates(state) if gate.confidence is not None]
    if not passed:
        return None
    return min(passed, key=lambda gate: gate.confidence or 1.0)


def _missing_evidence_checklist(state: IdeaState) -> list[str]:
    checklist: list[str] = []
    for gate in _passed_gates(state):
        if gate.confidence is None or gate.confidence >= 0.7:
            continue
        evidence_hint = ",".join(gate.evidence_ids[:2]) if gate.evidence_ids else "none"
        checklist.append(
            f"Raise confidence for gate={gate.gate_name}: add direct first-person evidence (current_evidence_ids={evidence_hint})."
        )
    if not checklist:
        checklist.append("No sub-0.7 passed gates on winner; collect backup evidence for spending and retention.")
    return checklist


def _why_winner_beat_alternatives(winner: IdeaState, states: list[IdeaState]) -> str:
    alternatives = [
        state
        for state in states
        if state.idea.id != winner.idea.id and state.terminal_verdict in {TerminalVerdict.PURSUE_SPIKE, TerminalVerdict.SHORTLIST}
    ]
    if not alternatives:
        return (
            f"winner={winner.idea.id} had no terminal-viable alternatives; "
            f"confidence={winner.confidence_score_so_far:.3f}."
        )
    runner_up = max(alternatives, key=lambda state: state.confidence_score_so_far)
    winner_pass = len(_passed_gates(winner))
    runner_pass = len(_passed_gates(runner_up))
    delta = winner.confidence_score_so_far - runner_up.confidence_score_so_far
    return (
        f"winner={winner.idea.id} beat runner_up={runner_up.idea.id} "
        f"by confidence_delta={delta:.3f} and pass_gate_delta={winner_pass - runner_pass}."
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
        why = _why_winner_beat_alternatives(winner, states)
        highest = _highest_conf_gate(winner)
        lowest = _lowest_conf_gate(winner)
        if highest is not None:
            evidence_ref = highest.evidence_ids[0] if highest.evidence_ids else "none"
            arg_for = (
                f"winner_gate={highest.gate_name} had confidence={highest.confidence:.2f} "
                f"supported_by_evidence_id={evidence_ref}."
            )
        if lowest is not None:
            evidence_ref = lowest.evidence_ids[0] if lowest.evidence_ids else "none"
            arg_against = (
                f"winner_gate={lowest.gate_name} had weakest pass confidence={lowest.confidence:.2f}; "
                f"flip_condition=add stronger evidence beyond evidence_id={evidence_ref}."
            )
        checklist = _missing_evidence_checklist(winner)
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
