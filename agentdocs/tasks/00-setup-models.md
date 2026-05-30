# Task: Models & Data Types Setup

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 0](../plan.md#phase-0-models--player-profile)
**Status**: TODO
**Priority**: P0 (Critical)

## Objective

Add all new data types to `models.py`: `PlayerProfile`, `Idea`, `KillCondition`, `GateResult`, `IdeaState`, `RealitySpike`, `DecisionMemo`, `TournamentResult`, `RoundOutcome`, `GateStatus`, `TerminalVerdict`, `ComplaintType`. Keep retired types nullable for read-back compat.

## In Scope

- Add `RoundOutcome`, `GateStatus`, `TerminalVerdict`, `ComplaintType` enums
- Add `PlayerProfile`, `KillCondition`, `Idea`, `GateResult`, `IdeaState` dataclasses
- Add `RealitySpike`, `DecisionMemo`, `TournamentResult` dataclasses
- Keep retired types (`Verdict` enum, `scoring.py` types) nullable during transition
- All new types must serialize/deserialize cleanly to/from JSON

## Out of Scope

- Retiring old types (deferred until Phase 3 confirms no references)
- Any behavioral logic (gates, engine, verdicts)

## Acceptance Criteria

- [ ] All new enums and dataclasses defined and importable
- [ ] `PlayerProfile` round-trips through JSON
- [ ] `Idea` with `KillCondition`, `evidence_ids`, `gate_profile` constructs and serializes
- [ ] `TerminalVerdict` has exactly 4 members: KILL, INSUFFICIENT_EVIDENCE, SHORTLIST, PURSUE_SPIKE
- [ ] `ComplaintType` has 14 named types + `UNKNOWN_WITH_REASON`
- [ ] All 98 existing tests still pass

## Dependencies

None (Phase 0 — foundation)
