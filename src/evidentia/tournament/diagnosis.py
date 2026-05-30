from __future__ import annotations

from collections import Counter

from evidentia.models import IdeaState


def zero_winner_diagnosis(states: list[IdeaState]) -> str:
    failed_gates = Counter()
    for state in states:
        for result in state.gate_results:
            if result.outcome and result.outcome.value == "FAIL":
                failed_gates[result.gate_name] += 1
                break
    if not failed_gates:
        return "No winner: required gates were skipped or errored; gather missing evidence and rerun."
    gate_name, count = failed_gates.most_common(1)[0]
    return f"No winner: {count}/{len(states)} ideas failed first at gate '{gate_name}'. Add evidence targeting this gate."
