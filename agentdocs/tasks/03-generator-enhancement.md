# Task: Generator Emits Kill Conditions & Profiles

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 2](../plan.md#phase-2-generator-emits-kill-conditions--profiles)
**Status**: TODO
**Priority**: P1 (High)

## Objective

Update `generator.py` to output `kill_condition` (gate name must be in chosen profile), `gate_profile`, and inference confidence. Add manual-mode adapter with `--discover-evidence`. Enforce profile-inference threshold: if <0.7, CLI refuses without explicit `--profile`.

## In Scope

- Generator emits `kill_condition` with `description` + `gate_name`
- Generator emits `gate_profile` with inference confidence
- Validator rejects ideas with empty `evidence_ids`
- Manual-mode: accept JSONL ideas with optional `--discover-evidence` budgeted harvest
- CLI enforces `--profile` flag when inference confidence < 0.7

## Out of Scope

- Tournament integration (Phase 3)
- Re-entry generator (Phase 3)

## Acceptance Criteria

- [ ] Generated ideas always have non-empty `evidence_ids`
- [ ] Generated ideas have `kill_condition` with gate_name matching chosen profile
- [ ] Low-confidence inference (<0.7) without `--profile` exits nonzero with message
- [ ] Manual idea with no evidence IDs and no `--discover-evidence` is rejected
