# Task: Complaint Taxonomy & Harvester Polish

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 1](../plan.md#phase-1-complaint-taxonomy--harvester-polish)
**Status**: TODO
**Priority**: P1 (High)

## Objective

Extend `scanners/reviews.py` to emit `complaint_type` per signal via `classifier.py`, with `UNKNOWN_WITH_REASON` allowed. Confirm `auditor.py` substring verification still enforced.

## In Scope

- Add `complaint_type` classification task to `classifier.py`
- Extend `scanners/reviews.py` to emit `complaint_type` per signal
- Allow `UNKNOWN_WITH_REASON` with free-text reason
- Fixture set covering ≥6 complaint types + UNKNOWN_WITH_REASON
- Acceptance test: fixture anchor yields ≥20 verified signals with URL + quote + complaint_type or UNKNOWN_WITH_REASON

## Out of Scope

- Other classifier tasks (cohort_fit, spend_signal, player_fit — Phase 2/3)
- New scanner sources
- Live-network acceptance (live smoke only)

## Acceptance Criteria

- [ ] Classifier returns valid `ComplaintType` for known patterns
- [ ] Classifier returns `UNKNOWN_WITH_REASON` with reason for ambiguous input
- [ ] Fixture with ≥20 signals: every signal has URL + verbatim quote + complaint_type
- [ ] All existing tests pass
