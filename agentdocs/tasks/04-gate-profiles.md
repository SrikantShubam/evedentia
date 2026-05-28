# Task: Gate Profiles

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 3](../plan.md#phase-3-tournament-engine)
**Status**: TODO
**Priority**: P1 (High)

## Objective

Create `tournament/profiles.py` with 4 named gate profiles. Each profile tags gates as `structural` or `evidence` with cost tiers in ascending order. Each profile's gate list is ordered cheapest-first.

## In Scope

- Register `consumer_app`, `b2b_workflow`, `browser_extension`, `agency_service` profiles
- Each gate tagged `structural` or `evidence` with cost tier (FREE, LLM_LIGHT, LLM_REASON, LLM_PAID_SEARCH)
- Unit tests per profile: correct gate order, correct tag assignment
- Profile lookup by name; error on unknown profile

## Out of Scope

- Gate implementations (individual gate functions — separate task)
- Engine dispatch logic

## Acceptance Criteria

- [ ] `consumer_app` has 8 gates in cost-ascending order
- [ ] `b2b_workflow` has 7 gates
- [ ] `browser_extension` has 7 gates
- [ ] `agency_service` has 6 gates
- [ ] Each gate correctly tagged as `structural` or `evidence`
- [ ] Unknown profile name raises `KeyError` with clear message
