# Implementation Plan: Edge — Adversarial Idea Tournament

**Spec**: [spec.md](spec.md)
**Status**: Draft
**Last Updated**: 2026-05-28

## Approach Summary

Engine-first, cockpit deferred. Build the tournament engine — all gate modules, deterministic verdict derivation, budget-aware dispatch, re-entry rules — as a pure CLI tool before adding any API or frontend surface. Every acceptance test is fixture-backed; live tests live in `tests/live/` with `-m live` and never run in CI. Phases 0-4 are committed scope; Phases 5-6 (API + cockpit) proceed only after real-market live smoke passes the engine gate.

## Architecture

### Components

| Component | Purpose | New/Modified |
|-----------|---------|--------------|
| `models.py` | All data types: PlayerProfile, Idea, GateResult, DecisionMemo, etc. | Modified |
| `providers.py` | LLM + search fallback chain | Existing |
| `auditor.py` | Quote verification (substring match) | Existing |
| `scanners/` | HN, Reddit, GitHub, reviews signal harvesters | Modified |
| `classifier.py` | Complaint type, cohort fit, player fit classification | Modified |
| `generator.py` | Idea generation with kill conditions + gate profiles | Modified |
| `clusterer.py` | Signal clustering by niche | Existing |
| `tournament/gates.py` | Pure gate functions per profile | New |
| `tournament/profiles.py` | Gate profile definitions with cost tiers | New |
| `tournament/engine.py` | Cheapest-kill-first dispatcher, budget-aware | New |
| `tournament/confidence.py` | Clamped posterior product + is_rankable | New |
| `tournament/verdict.py` | Deterministic 4-way terminal verdict | New |
| `tournament/diagnosis.py` | Zero-winner explanation | New |
| `tournament/memo.py` | Mechanical memo + reality spike generator | New |
| `outputs.py` | Tournament + memo + discard artifacts | Modified |
| `cli.py` | `edge player`, `edge tournament`, `edge memo` commands | Modified |
| `api.py`, `db.py` | FastAPI + SQLite (Phase 5) | New |
| `docs/frontend/` | Cockpit UI (Phase 6) | New |

## Implementation Phases

### Phase 0: Models & Player Profile

**Goal**: Extend data model with all new types; PlayerProfile load/save; CLI stub

- [ ] [00-setup-models](./tasks/00-setup-models.md)
- [ ] [01-player-profile](./tasks/01-player-profile.md)

### Phase 1: Complaint Taxonomy & Harvester Polish

**Goal**: Classify complaint types across all scanner outputs

- [ ] [02-complaint-taxonomy](./tasks/02-complaint-taxonomy.md)

### Phase 2: Generator Emits Kill Conditions & Profiles

**Goal**: Generator outputs structured kill conditions and gate profile inferences

- [ ] [03-generator-enhancement](./tasks/03-generator-enhancement.md)

### Phase 3: Tournament Engine

**Goal**: Full CLI-only tournament engine with all gate modules, verdicts, re-entry

- [ ] [04-gate-profiles](./tasks/04-gate-profiles.md)
- [ ] [05-tournament-engine](./tasks/05-tournament-engine.md)
- [ ] [06-verdict-rules](./tasks/06-verdict-rules.md)
- [ ] [07-re-entry](./tasks/07-re-entry.md)

### Phase 4: Decision Memo & Reality Spike

**Goal**: Mechanical memo builder + reality spike generator

- [ ] [08-decision-memo](./tasks/08-decision-memo.md)

### Phase 5: API Surface (engine gate dependent)

**Goal**: FastAPI + SQLite endpoints

- [ ] [09-api-surface](./tasks/09-api-surface.md)

### Phase 6: Cockpit (engine gate dependent)

**Goal**: Poker Board frontend with SSE streaming

- [ ] [10-cockpit-frontend](./tasks/10-cockpit-frontend.md)

### Phase 7: Dogfood & Tuning

**Goal**: Real-market validation and threshold tuning

- [ ] [11-dogfood-tuning](./tasks/11-dogfood-tuning.md)

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Engine before API/UI | CLI-only until Phase 4 passes live smoke | Prevents building UI around unproven engine; avoids wasted work |
| Fixture-backed tests | All acceptance tests use saved fixtures | Deterministic, no network dependency, CI-safe |
| Live tests as `-m live` | Separate marker, never in CI | Enables real-market testing without polluting CI pipeline |
| String-backed enums | `Provenance`, `RoundOutcome`, etc. use `.value` strings | JSON round-trip compatible without custom serializers |
| Player Profile as first-class input | Structured dataclass with budgets/skills/risk | Enables agency-relative scoring |
| Deterministic verdict derivation | Pure rules, no LLM | Prevents verdict drift; auditable |
| Confidence as multiplicative product | Clamped [0.5, 0.95] | Conservative; weak-link math without pretending to be P(success) |

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM provider failures | High | Medium | Existing fallback chain in `providers.py`; retry logic; ERROR status non-fatal |
| Budget exhaustion mid-tournament | Medium | Medium | Partial state preserved; SKIPPED gates tracked; is_rankable=False |
| Real-market live smoke fails | High | Medium | Diagnosis identifies weak gates; tune thresholds; narrow scope |
| Re-entry violations (not narrower) | Medium | Low | Post-validation in generator; classifier verifies "narrower" boolean |
| Scanner network blocks | Low | Medium | Fixture-backed acceptance tests; live tests opt-in |

## Testing Strategy

### Unit Tests

- Each gate function tested individually with seeded fixtures
- Verdict derivation rules (5 rules, 5 test cases minimum)
- Confidence calculation (boundary: all 0.5, all 0.95, mixed)
- Re-entry validation (narrower check, new-evidence check, depth cap)

### Integration Tests

- Full tournament engine with fixture input
- Memo export byte-match
- Profile routing (low-confidence inference forces explicit flag)

### End-to-End Tests (fixture-backed)

- Strong evidence → PURSUE_SPIKE
- Happy incumbent → KILL all
- No spend → INSUFFICIENT_EVIDENCE
- Budget exhausted → unrankable
- Re-entry narrower or rejected

### Live Tests (manual, `-m live`, never in CI)

- Harvest live anchor smoke
- Tournament live under budget

## Success Metrics

- All unit/integration/acceptance tests pass in CI
- Engine gate: real-market live smoke on 2-3 markets produces meaningful kills/promotions
- Zero-winner diagnosed correctly (not hidden)
- Decision memo fields are mechanically assembled (grep-checkable: no LLM free-form in evidence fields)

## Changelog

### 2026-05-28

- Initial plan created from `ultimate plan.md`
