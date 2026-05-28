# Edge — Adversarial Idea Tournament

## Status

- [ ] Draft
- [ ] Review
- [ ] Approved
- [ ] In Progress
- [ ] Complete

## Overview

A generate-then-validate system for product/venture ideas. Ideas are born with explicit kill conditions, evaluated cheapest-kill-first through a multi-gate tournament, and rated by multiplicative confidence score that respects the agency's capacity to capture them. Zero survivors is a legitimate, diagnosed outcome. Engine-first, cockpit after.

## Novel Tenets

1. **Player Profile is a first-class input** — scoring is agency-relative
2. **Every idea has an explicit kill condition** mapped to a named gate
3. **Cheapest-kill-first** gate ordering (free checks before paid LLM/search)
4. **Confidence, not probability** — clamped-posterior product, rigorous without pretending to be P(success)
5. **Binary per round, 4-way terminal verdict** — gates PASS/FAIL, verdict derived deterministically by rules
6. **Configurable gate profiles** — `consumer_app`, `b2b_workflow`, `browser_extension`, `agency_service`
7. **Zero-winner is a first-class diagnosed state**
8. **Decision memo is the primary output** — mechanically assembled from evidence
9. **Reality spike, not PRD** — PURSUE_SPIKE produces an 8-field test plan
10. **Anti-hallucination is structural** — enforced at model + verifier + LLM-wrapper

## Goals

- Replace ad-hoc idea validation with a deterministic, player-aware tournament engine
- Produce decision memos that are mechanically assembled from evidence, not LLM free-form
- Enable zero-winner outcomes as a legitimate diagnosed state
- Support survivor re-entry (bounded, traceable, narrower-cohort enforced)
- Build engine first; API and cockpit only after real-market proof

## Non-Goals

- No multi-tenant auth/billing in v1
- No outbound communication (reading public web only)
- No training/ML-based speaker diarization or identity resolution
- No real-time collaboration features
- No PRD generation — only reality-spike tactical copy

## Requirements

### Functional Requirements

1. [FR-1] **Player Profile** — CLI can init-from-file and show a player profile with budgets, skills, timeline, risk, and caps
2. [FR-2] **Gate profiles** — minimum 4 named profiles (`consumer_app`, `b2b_workflow`, `browser_extension`, `agency_service`) with structural/evidence gate tags and cost tiers
3. [FR-3] **Cheapest-kill-first execution** — gates dispatch in cost-ascending order; structural gates before evidence gates at same cost tier
4. [FR-4] **Confidence score** — multiplicative clamped posterior product over PASSED gates; each gate confidence clamped [0.5, 0.95]
5. [FR-5] **Terminal verdict** — deterministic 4-way derivation (KILL, INSUFFICIENT_EVIDENCE, SHORTLIST, PURSUE_SPIKE) from IdeaState; no LLM involvement
6. [FR-6] **Decision memo** — mechanically assembled fields; only reality-spike tactical copy is LLM-generated and explicitly labeled
7. [FR-7] **Zero-winner diagnosis** — template-filled explanation citing kill-gate histogram
8. [FR-8] **Survivor re-entry** — bounded (default 1, hard cap 3), narrower-cohort + new-evidence enforced, SHORTLIST never re-enters
9. [FR-9] **Budget guardrails** — per-tournament hard ceilings on LLM calls and paid search queries; exhausted → SKIPPED → unrankable
10. [FR-10] **Manual idea discipline** — evidence IDs required (pre-attached or via `--discover-evidence`); no-evidence ideas rejected before gate 1

### Non-Functional Requirements

1. [NFR-1] All acceptance tests are fixture-backed; live tests in `tests/live/` with `-m live`, never in CI
2. [NFR-2] No `random`/`uuid4` in production paths; unsorted set iteration banned in output paths
3. [NFR-3] Every LLM call produces schema-validated JSON; invalid → one corrective retry → ERROR
4. [NFR-4] Decision-memo evidence fields are mechanically assembled; only reality-spike tactical copy may be LLM-generated
5. [NFR-5] Incomplete tournaments (budget-truncated) cannot produce a winner — only INSUFFICIENT_EVIDENCE outcomes

## Core Data Model

```python
class RoundOutcome(str, Enum): PASS, FAIL
class GateStatus(str, Enum): COMPLETED, SKIPPED, ERROR
class TerminalVerdict(str, Enum): KILL, INSUFFICIENT_EVIDENCE, SHORTLIST, PURSUE_SPIKE
class ComplaintType(str, Enum): 14 types + UNKNOWN_WITH_REASON

@dataclass class PlayerProfile: id, team, skills, budgets, weeks_to_ship, risk, caps, max_reentry_rounds
@dataclass class KillCondition: description, gate_name
@dataclass class Idea: id, label, anchor, cohort, pain_hypothesis, kill_condition, evidence_ids, search_queries, origin, gate_profile, parent_idea_id
@dataclass class GateResult: gate_name, status, outcome, evidence_ids, confidence, killed_by, llm_cost_usd, error
@dataclass class IdeaState: idea, gate_results, confidence_score_so_far, is_complete, terminal_verdict
@dataclass class RealitySpike: idea_id, target_customer_profile, outreach_message, landing_page_copy, interview_questions, success/fail_criteria, weeks_to_run
@dataclass class DecisionMemo: tournament_id, player_id, winner, shortlist, insufficient_evidence, killed, why_winner_beat_alternatives, strongest_argument_for/against, missing_evidence_checklist, reality_spike, zero_winner_diagnosis
@dataclass class TournamentResult: tournament_id, player_id, gate_profile, ideas, memo, total_cost, stopped_reason, is_rankable, parent_tournament_id, reentry_depth
```

## Terminal Verdict Derivation

Deterministic rules in `tournament/verdict.py`:

```
Rule 1: any structural gate COMPLETED+FAIL                → KILL
Rule 2: any evidence gate COMPLETED+FAIL                  → INSUFFICIENT_EVIDENCE
Rule 3: any required gate not COMPLETED                   → INSUFFICIENT_EVIDENCE
Rule 4: all required COMPLETED+PASS, confidence ≥ 0.35    → PURSUE_SPIKE
Rule 5: all required COMPLETED+PASS, confidence < 0.35    → SHORTLIST
```

Incomplete tournaments (`is_rankable == False`) cannot produce a winner.

## Acceptance Criteria

- [ ] Strong-evidence fixture → ≥1 PURSUE_SPIKE/SHORTLIST; winner confidence ≥ threshold iff PURSUE_SPIKE
- [ ] Happy-incumbent fixture → all KILL; diagnosis cites `niche_not_already_owned`
- [ ] No-spend fixture → all INSUFFICIENT_EVIDENCE; diagnosis cites `willingness_to_pay`
- [ ] Budget-exhaustion fixture → is_rankable=False, winner=None, partial state preserved
- [ ] Profile routing fixture → B2B runs B2B gates, not consumer; low-confidence inference forces explicit flag
- [ ] Re-entry fixture → narrower-cohort + new-evidence enforced; max_reentry_rounds hard-capped
- [ ] Memo for strong fixture includes winner + shortlist + reality spike (labeled LLM_GENERATED_TACTICAL_COPY)
- [ ] Memo for zero-winner fixture includes diagnosis + missing evidence checklist
- [ ] Manual idea with no evidence → rejected before gate 1
- [ ] All unit/integration/acceptance tests fixture-backed, pass in CI
- [ ] Live test suite runs manually, never in CI

## Phases

### Phase 0 — Models & Player Profile
- Extend `models.py` with new types; `PlayerProfile` load/save as JSON; `edge player` CLI

### Phase 1 — Complaint taxonomy + harvester polish
- Extend scanners with `complaint_type` classification; `UNKNOWN_WITH_REASON` allowed; fixture set covering ≥6 types

### Phase 2 — Generator emits kill conditions + profiles
- `generator.py` outputs `kill_condition` + `gate_profile` + inference confidence; manual-mode adapter; profile-inference threshold enforcement

### Phase 3 — Tournament engine, CLI-only
- All gate modules pure; 4 profiles registered; cheapest-kill-first dispatch; budget-aware; re-entry; deterministic verdicts

### Phase 4 — Decision memo + reality spike
- Mechanical memo construction; CLI render to md/json

**Engine gate**: Do not start Phase 5 until Phase 4 passes real-market live smoke.

### Phase 5 — API surface
- FastAPI + SQLite; endpoints for player, harvest, generate, tournament, SSE stream, memo

### Phase 6 — Cockpit / Poker Board
- Implement designed UI pages; Playwright E2E fixture-backed

### Phase 7 — Dogfood + tuning
- 3 real tournaments; tune thresholds, profiles, taxonomy

## Dependencies

- LLM/search provider with fallback chain (existing `providers.py`)
- Page-fetch-and-quote verifier (existing `auditor.py`)
- Platform scanners: HN, Reddit, GitHub, reviews (existing)
- Signal clusterer (existing `clusterer.py`)
- CLI framework (Click, existing)

## Anti-Hallucination Contract

- Every signal must have `source_url` + non-empty `verbatim_quote` (Pydantic validator)
- Quote must substring-match fetched page (auditor enforces)
- LLM classifies only — never invents signals
- Every LLM call produces schema-validated JSON; invalid → one retry → ERROR
- No `random`/`uuid4` in production paths; unsorted set iteration banned in output paths
- Failed verification → `discard_log.json` with reason code

## References

- Full product plan: [`ultimate plan.md`](../../ultimate%20plan.md)
- Active phase tracking: `main/docs/ACTIVE_PLAN.md`
- Existing codebase: `main/src/evidentia/`
