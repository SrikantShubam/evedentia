# Task: Dogfood & Tuning

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 7](../plan.md#phase-7-dogfood--tuning)
**Status**: TODO
**Priority**: P2 (Medium)

## Objective

Run 3 real tournaments on live markets (APIs, under budget). Capture metrics and tune thresholds.

## In Scope

- 3 live tournament runs on real markets
- Capture: gate-kill histogram, spend/tournament, confidence score sanity check, reality-spike runnability
- Tune: `SHORTLIST_CONFIDENCE_THRESHOLD`, posterior clamp range, profile gate lists, complaint-taxonomy labels, memo templates
- Retro in `docs/`

## Out of Scope

- New feature development
- Production deployment

## Acceptance Criteria

- [ ] 3 tournaments run under budget
- [ ] Gate-kill histogram produced for each
- [ ] Tuning adjustments documented with rationale
- [ ] Retro written to `docs/`
