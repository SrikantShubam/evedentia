# Task: Survivor Re-entry

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 3](../plan.md#phase-3-tournament-engine)
**Status**: TODO
**Priority**: P1 (High)

## Objective

Implement bounded survivor re-entry: only `INSUFFICIENT_EVIDENCE` ideas are eligible seeds. Enforce narrower-cohort + new-evidence rules. Cap at `PlayerProfile.max_reentry_rounds`.

## In Scope

- Re-entry CLI: `edge tournament run --seed-from <tournament_id> --narrow`
- `parent_idea_id` tracking on re-entered ideas
- Narrower-cohort enforcement (post-validation: new cohort must add constraints)
- New-evidence requirement (at least one new `evidence_id` not on parent)
- Depth tracking via `reentry_depth`; block at `max_reentry_rounds`
- SHORTLIST ideas never eligible for re-entry

## Out of Scope

- Decision memo updates for re-entry (Phase 4)
- UI for one-click re-entry (Phase 6)

## Acceptance Criteria

- [ ] `INSUFFICIENT_EVIDENCE` idea re-enters with narrower cohort
- [ ] SHORTLIST idea re-entry rejected with error
- [ ] Re-entry without narrower cohort rejected
- [ ] Re-entry without new evidence rejected
- [ ] Re-entry beyond max depth rejected
- [ ] Re-entered idea carries `parent_idea_id` and incremented `reentry_depth`
