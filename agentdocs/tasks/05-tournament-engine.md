# Task: Tournament Engine

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 3](../plan.md#phase-3-tournament-engine)
**Status**: TODO
**Priority**: P0 (Critical)

## Objective

Implement `tournament/engine.py` — cheapest-kill-first dispatch, budget-aware, emits structured NDJSON event log. Wires together gates, profiles, confidence scoring, and verdict rules.

## In Scope

- Load gate profile for each idea
- Dispatch gates in cost-ascending order (cheapest-kill-first)
- Budget tracking: decrement LLM calls and paid search from PlayerProfile caps
- Budget exhaustion → SKIPPED on remaining gates
- Emit NDJSON event log per gate execution (idea_id, gate, status, outcome, cost, confidence)
- Wire into CLI: `edge tournament run`
- Integration tests with seeded fixtures

## Out of Scope

- Re-entry (separate task)
- Decision memo (Phase 4)
- API/SSE streaming (Phase 5)

## Acceptance Criteria

- [ ] Ideas run through all gates in profile in correct order
- [ ] Structural gates execute before evidence gates at same cost tier
- [ ] Budget cap reached → remaining gates SKIPPED → `is_rankable=False`
- [ ] NDJSON event log produced with all required fields
- [ ] All existing tests pass
