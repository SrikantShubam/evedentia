from __future__ import annotations

from collections import Counter

from evidentia.models import IdeaState


def zero_winner_diagnosis(states: list[IdeaState]) -> str:
    failed_gates = Counter()
    for state in states:
        for result in state.gate_results:
            if result.outcome and result.outcome.value == "FAIL":
                failed_gates[result.gate_name] += 1
    if not failed_gates:
        return "No winner: required gates were skipped or errored; gather missing evidence and rerun."
    gate_name, count = failed_gates.most_common(1)[0]
    total_fails = sum(failed_gates.values())
    return (
        f"No winner: gate '{gate_name}' failed most frequently ({count}/{len(states)} states). "
        f"Total gate failures: {total_fails}. "
        "Add evidence targeting the most-failed gates."
    )
