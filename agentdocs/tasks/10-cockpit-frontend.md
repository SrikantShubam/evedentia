# Task: Cockpit / Poker Board Frontend

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 6](../plan.md#phase-6-cockpit-engine-gate-dependent)
**Status**: BLOCKED
**Priority**: P2 (Medium)

## Objective

Build the Poker Board UI: swim lanes per gate, SSE-streamed live updates, decision memo export, zero-winner diagnosis view.

## In Scope

- `app/player/page.tsx` — Player Profile CRUD
- `app/tournament/new/page.tsx` — seed form (anchor/manual list, profile picker)
- `app/tournament/[id]/page.tsx` — Poker Board with swim lanes, IdeaCards, SSE streaming
- `app/ideas/[id]/page.tsx` — evidence trail drill-down
- `app/tournament/[id]/memo.tsx` — printable memo with reality-spike card labeled
- `<Diagnosis>`, `<BudgetMeter>`, `<ReentryFromMemo>` components
- Playwright E2E tests (fixture-backed)

## Out of Scope

- Authentication/authorization
- Real-time collaboration
- Mobile responsiveness

## Dependencies

- Blocked by: Phase 5 API surface
