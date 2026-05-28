# Task: Terminal Verdict Rules

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 3](../plan.md#phase-3-tournament-engine)
**Status**: TODO
**Priority**: P0 (Critical)

## Objective

Implement deterministic 4-way terminal verdict derivation in `tournament/verdict.py`. Pure function from `IdeaState` → `TerminalVerdict`. No LLM involvement. Also implement `tournament/confidence.py` for clamped posterior product and `is_rankable` logic.

## In Scope

- `confidence.py`: multiplicative product over COMPLETED+PASS gates; each clamped [0.5, 0.95]; `is_rankable` = all required gates COMPLETED
- `verdict.py`: 5 deterministic rules producing KILL, INSUFFICIENT_EVIDENCE, SHORTLIST, PURSUE_SPIKE
- `diagnosis.py`: zero-winner explanation (kill-gate histogram)
- Unit tests: every rule tested with seeded IdeaState fixtures
- Boundary tests: all-0.5, all-0.95, mixed confidences

## Out of Scope

- Engine dispatch (separate task)
- Memo construction (Phase 4)

## Acceptance Criteria

- [ ] Structural FAIL → KILL
- [ ] Evidence FAIL → INSUFFICIENT_EVIDENCE
- [ ] Any required gate SKIPPED → INSUFFICIENT_EVIDENCE
- [ ] All PASS + confidence ≥ threshold → PURSUE_SPIKE
- [ ] All PASS + confidence < threshold → SHORTLIST
- [ ] Confidence product correctly computed with clamping
- [ ] `is_rankable=False` when any required gate not COMPLETED
- [ ] Diagnosis template correctly cites kill-gate histogram
