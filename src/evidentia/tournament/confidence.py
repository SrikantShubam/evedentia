from __future__ import annotations

from evidentia.models import GateStatus, IdeaState, RoundOutcome
from evidentia.tournament.profiles import required_gates


def clamp_confidence(value: float) -> float:
    return max(0.5, min(0.95, value))


def confidence_product(state: IdeaState) -> float:
    score = 1.0
    for gate in state.gate_results:
        if gate.status == GateStatus.COMPLETED and gate.outcome == RoundOutcome.PASS and gate.confidence is not None:
            score *= clamp_confidence(gate.confidence)
    return score


def is_rankable(state: IdeaState) -> bool:
    required = set(required_gates(state.idea.gate_profile))
    statuses = {gate.gate_name: gate.status for gate in state.gate_results}
    for gate_name in required:
        if statuses.get(gate_name) != GateStatus.COMPLETED:
            return False
    return True
