# ACTIVE_ARCHITECTURE.md

**Current System Summary**

Evidentia is an LLM-powered idea tournament engine featuring a FastAPI backend and a Next.js 15 glassmorphism dashboard. The core loop is: harvest signals → generate ideas → run deterministic tournament with gates (per-gate LLM scoring under player budgets) → produce a DecisionMemo with the winner plus a RealitySpike (tactical validation plan). This is the single source of truth for the running implementation.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /harvest | Accepts signals and stores them |
| POST | /generate | Generates candidate ideas from harvested signals |
| POST | /tournament | Creates tournament, runs all gates, returns full result |
| GET | /tournament/{id} | Returns tournament payload (note: IdeaState entries are flattened — id and label promoted to top level alongside nested idea) |
| GET | /tournament/{id}/sse | SSE stream of real-time gate evaluation events |
| GET | /tournament/{id}/memo | Decision memo containing winner, RealitySpike, and full rationale |
| GET | /tournament/{id}/idea/{idea_id} | Single idea's complete gate trail and scores |
| POST | /player | Upsert a player profile (JSON body) |
| GET | /player/{id} | Retrieve a player profile by ID |

## Key Data Shapes

**Idea**  
`id: str`, `label: str`, `anchor_slug: str | None`, `incumbent: str | None`, `cohort: str`, `pain_hypothesis: str`, `kill_condition: KillCondition`, `evidence_ids: list[str]`, `search_queries: list[str]`, `origin: str`, `gate_profile: str`, `gate_profile_source: str`, `parent_idea_id: str | None`, `evidence_provenance: dict[str, str]`

**IdeaState**  
`id` (promoted from nested), `label` (promoted from nested), `idea: Idea` (nested), `gate_results: list[GateResult]`, `confidence_score_so_far: float`, `is_complete: bool`, `terminal_verdict: TerminalVerdict | None`

**GateResult**  
`gate_name: str`, `status: GateStatus`, `outcome: RoundOutcome | None`, `evidence_ids: list[str]`, `confidence: float | None`, `killed_by: str | None`, `llm_cost_usd: float`, `error: str | None`

**TournamentResult**  
`tournament_id: str`, `player_id: str`, `gate_profile: str`, `started_at: str`, `finished_at: str | None`, `ideas: list[IdeaState]`, `memo: DecisionMemo | None`, `total_llm_cost_usd: float`, `stopped_reason: str`, `is_rankable: bool`, `parent_tournament_id: str | None`, `reentry_depth: int`, `schema_version: int`

**DecisionMemo**  
`tournament_id: str`, `player_id: str`, `winner: IdeaState | None`, `shortlist: list[IdeaState]`, `insufficient_evidence: list[IdeaState]`, `killed: list[IdeaState]`, `why_winner_beat_alternatives: str`, `strongest_argument_for: str`, `strongest_argument_against: str`, `missing_evidence_checklist: list[str]`, `reality_spike: RealitySpike | None`, `zero_winner_diagnosis: str | None`, `schema_version: int`

**RealitySpike** (embedded in DecisionMemo)  
`idea_id: str`, `target_customer_profile: str`, `outreach_message: str`, `landing_page_headline: str`, `landing_page_subhead: str`, `interview_questions: list[str]` (exactly 5), `success_criteria: str`, `fail_criteria: str`, `weeks_to_run: int`, `provenance: str`

**PlayerProfile** (for POST/GET /player)  
`id: str`, `team: str`, `skills: list[str]`, `budget_validate_usd: int`, `budget_build_usd: int`, `budget_reach_usd: int`, `weeks_to_ship: int`, `risk: "low"|"med"|"high"`, `max_llm_calls_per_tournament: int`, `max_paid_queries_per_tournament: int`, `max_reentry_rounds: int`

Other supporting types: `DemandSignal`, `Anchor`, `TerminalVerdict`, `GateStatus`, `RoundOutcome`, `Provenance`, `KillCondition`.

## Proof Level Stance

The original IMPLEMENTATION_PLAN.md envisioned a deterministic CLI core. Current reality uses per-gate LLM calls for scoring and confidence (within [0.5, 0.95] bounds), with deterministic gate sequencing, terminal verdicts (KILL / INSUFFICIENT_EVIDENCE / SHORTLIST / PURSUE_SPIKE), re-entry rules, and budget enforcement. Fixture-proof tests exist in the tournament engine (e.g., `tests/integration/test_tournament_engine_fixture.py`, acceptance suites exercising full flows against saved inputs). Dry-run paths are present for generation/harvest. Live proof is delivered via the dashboard + SSE streaming of gate events. All proof levels are labeled explicitly in code, tests, and outputs (fixture / dry-run / live); no live retrieval is mischaracterized as deterministic fixture proof.

## Frontend Architecture

Next.js 15 App Router with Tailwind v4. All glassmorphism effects are implemented via inline styles using design tokens exported from `lib/tokens.ts` (`glassBg`, `glassBorder`, `glassAccentBg`, `glassAccentBorder`, plus surface/accent colors). No external UI component libraries. The dashboard consumes the FastAPI endpoints (especially tournament SSE for real-time gate progress, memo, and per-idea trails) and renders IdeaState / DecisionMemo artifacts.

## Dev Stack

- Python 3.10+
- FastAPI (with sse-starlette for `/sse`)
- SQLite (via `src/evidentia/db.py`; stores tournaments, players, gate event logs)
- `uv` for Python environment and dependency management
- Next.js 15 (frontend in `docs/frontend/`)
- SSE for streaming tournament gate evaluations to the UI

This document reflects the running system (backend + live dashboard) as of the latest implementation. Consult `IMPLEMENTATION_PLAN.md` and `final_pivot.md` for historical context and phased intent; treat this file as the active runtime architecture.
