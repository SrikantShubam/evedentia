# Task: Decision Memo & Reality Spike

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 4](../plan.md#phase-4-decision-memo--reality-spike)
**Status**: TODO
**Priority**: P1 (High)

## Objective

Build `tournament/memo.py` — mechanical memo field construction. Only the `RealitySpike` tactical copy is LLM-generated and explicitly labeled. CLI: `edge memo render <tournament_id> --format md|json`.

## In Scope

- Mechanical fields: `why_winner_beat_alternatives`, `strongest_argument_for/against`, `missing_evidence_checklist`, `zero_winner_diagnosis` — all template-filled from IdeaState/confidence data
- `RealitySpike` LLM call: input = Idea + PlayerProfile + top 3 evidence signals; output = structured 8-field plan with `provenance="LLM_GENERATED_TACTICAL_COPY"`
- CLI render to md and json
- Acceptance test: memo for strong fixture includes winner + shortlist + reality spike (labeled); memo for zero-winner includes diagnosis

## Out of Scope

- API memo endpoint (Phase 5)
- Cockpit memo display (Phase 6)

## Acceptance Criteria

- [ ] Winner memo includes why_winner_beat_alternatives (template-filled, not free-form)
- [ ] strongest_argument_for cites specific evidence signal IDs
- [ ] Reality spike has `provenance="LLM_GENERATED_TACTICAL_COPY"`
- [ ] Zero-winner memo includes diagnosis with kill-gate histogram
- [ ] Missing evidence checklist covers gates with confidence < 0.7
- [ ] `edge memo render` produces byte-match identical output for same tournament
