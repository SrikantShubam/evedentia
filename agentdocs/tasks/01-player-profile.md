# Task: Player Profile CLI

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 0](../plan.md#phase-0-models--player-profile)
**Status**: TODO
**Priority**: P0 (Critical)

## Objective

Implement `PlayerProfile` load/save as JSON in `outputs/profile.json` and add CLI commands: `edge player init-from-file profile.json` and `edge player show`.

## In Scope

- Load PlayerProfile from JSON file
- Save to `outputs/profile.json` (no SQLite yet)
- `edge player init-from-file <path>` — validates and stores
- `edge player show` — prints current profile
- Unit tests for validation (budget ranges, risk values, cap parsing)

## Out of Scope

- SQLite persistence (Phase 5)
- Tournament integration (Phase 3)
- Multiple profiles

## Acceptance Criteria

- [ ] Valid profile JSON loads and saves correctly
- [ ] Invalid budget (<0) or risk (not low/med/high) rejected with clear error
- [ ] `edge player show` prints formatted profile
- [ ] Round-trip: init → show → byte-match original JSON
