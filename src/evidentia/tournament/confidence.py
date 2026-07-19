from __future__ import annotations

from evidentia.models import GateStatus, IdeaState, RoundOutcome
from evidentia.tournament.settings import CONFIDENCE_CEIL, CONFIDENCE_FLOOR
from evidentia.tournament.profiles import required_gates


def clamp_confidence(value: float) -> float:
    return max(CONFIDENCE_FLOOR, min(CONFIDENCE_CEIL, value))


def confidence_product(state: IdeaState) -> float:
    """Geometric mean of passed-completed gate confidences.

    Using geometric mean instead of raw product ensures that the score
    stays in a meaningful range regardless of the number of gates.
    A product of N gate confidences (each ≤ 0.95) decays toward zero,
    making PURSUE_SPIKE unreachable for profiles with many gates.
    """
    score = 1.0
    count = 0
    for gate in state.gate_results:
        if gate.status == GateStatus.COMPLETED and gate.outcome == RoundOutcome.PASS and gate.confidence is not None:
            score *= clamp_confidence(gate.confidence)
            count += 1
    if count == 0:
        return 0.0
    return score ** (1.0 / count)


def is_rankable(state: IdeaState) -> bool:
    required = set(required_gates(state.idea.gate_profile))
    statuses = {gate.gate_name: gate.status for gate in state.gate_results}
    for gate_name in required:
        if statuses.get(gate_name) != GateStatus.COMPLETED:
            return False
    return True
