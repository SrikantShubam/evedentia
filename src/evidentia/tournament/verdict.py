from __future__ import annotations

from evidentia.models import GateStatus, RoundOutcome, TerminalVerdict
from evidentia.models import IdeaState
from evidentia.tournament.profiles import STRUCTURAL_GATES, required_gates


SHORTLIST_CONFIDENCE_THRESHOLD = 0.35


def derive_terminal_verdict(
    state: IdeaState,
    *,
    shortlist_confidence_threshold: float = SHORTLIST_CONFIDENCE_THRESHOLD,
) -> TerminalVerdict:
    profile_name = state.idea.gate_profile
    required = required_gates(profile_name)
    structural = STRUCTURAL_GATES[profile_name]
    results = {result.gate_name: result for result in state.gate_results}

    for gate_name in required:
        gate = results.get(gate_name)
        if gate is None:
            continue
        if gate.outcome == RoundOutcome.FAIL and gate_name in structural:
            return TerminalVerdict.KILL

    for gate_name in required:
        gate = results.get(gate_name)
        if gate is None:
            continue
        if gate.outcome == RoundOutcome.FAIL and gate_name not in structural:
            return TerminalVerdict.INSUFFICIENT_EVIDENCE

    for gate_name in required:
        gate = results.get(gate_name)
        if gate is None:
            return TerminalVerdict.INSUFFICIENT_EVIDENCE
        if gate.status != GateStatus.COMPLETED:
            return TerminalVerdict.INSUFFICIENT_EVIDENCE

    if state.confidence_score_so_far >= shortlist_confidence_threshold:
        return TerminalVerdict.PURSUE_SPIKE
    return TerminalVerdict.SHORTLIST
