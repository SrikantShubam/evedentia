# Evidentia Architecture

## Current System (June 2026)

Evidentia is an LLM-powered idea tournament engine with a FastAPI backend and Next.js glassmorphism dashboard. Ideas are harvested from sources, generated from anchors, then prosecuted through hard gates by LLM judges. Results stream via SSE to a poker-board UI.

**Status: ACTIVE.** Engine gate passed (2/3 markets). All Phases 0-5 complete. API, frontend, and database layers are available for use. CI configured via GitHub Actions.

New in Phase 1-3: `edge research` (competitive intelligence), `edge interrogate` (artifact querying), `edge bridge` (research→validate pipeline).

## Tech Stack

- **Backend:** Python 3.10, FastAPI, SQLite, SSE streaming via sse-starlette
- **Frontend:** Next.js 15 (App Router), React 19, Tailwind CSS v4, Framer Motion
- **Design:** Dark theme (#0a0a0a), glassmorphism (backdrop-filter blur), accent #e2ff5d, design tokens in `lib/tokens.ts`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /player | Create or update a player profile |
| GET | /player/{id} | Get player profile |
| POST | /harvest | Harvest demand signals for an anchor |
| POST | /generate | Generate ideas from an anchor or pursue entries |
| POST | /tournament | Create a tournament, run gates, return result |
| GET | /tournament/{id} | Get tournament payload (flattened — id/label at top level) |
| GET | /tournament/{id}/sse | SSE stream of gate events (event: "gate", event: "done") |
| GET | /tournament/{id}/memo | Decision memo with winner + RealitySpike |
| GET | /tournament/{id}/idea/{id} | Single idea gate trail |

## Key Data Shapes

### TournamentPayload
```json
{
  "tournament_id": "string",
  "player_id": "string",
  "gate_profile": "string",
  "total_llm_cost_usd": 0.0,
  "reentry_depth": 0,
  "ideas": [IdeaState],
  "memo": DecisionMemo | null
}
```

### IdeaState (flattened)
```json
{
  "id": "string",
  "label": "string",
  "idea": { "id": "string", "label": "string", "anchor_slug": "string", ... },
  "gate_results": [GateResult],
  "confidence_score_so_far": 0.0,
  "is_complete": false,
  "terminal_verdict": "PURSUE_SPIKE" | "KILL" | "INSUFFICIENT_EVIDENCE" | null
}
```

### GateResult
```json
{
  "gate_name": "string",
  "status": "COMPLETED" | "ERROR",
  "outcome": "PASS" | "FAIL" | null,
  "evidence_ids": ["string"],
  "confidence": 0.0 | null,
  "killed_by": "string" | null,
  "llm_cost_usd": 0.0,
  "error": "string" | null
}
```

### DecisionMemo
```json
{
  "tournament_id": "string",
  "player_id": "string",
  "winner": IdeaState | null,
  "shortlist": [IdeaState],
  "insufficient_evidence": [IdeaState],
  "killed": [IdeaState],
  "zero_winner_diagnosis": "string" | null,
  "best_reentry_narrowing": "string" | null,
  "reality_spike": RealitySpike | null
}
```

### RealitySpike
```json
{
  "idea_id": "string",
  "target_customer_profile": "string",
  "outreach_message": "string",
  "landing_page_headline": "string",
  "landing_page_subhead": "string",
  "interview_questions": ["string x5"],
  "success_criteria": "string",
  "fail_criteria": "string",
  "weeks_to_run": 6,
  "provenance": "LLM_GENERATED_TACTICAL_COPY"
}
```

## Frontend Routes

| Route | Component | Description |
|-------|-----------|-------------|
| / | DashboardHomepage | Dashboard with scan, results grid, validation engine |
| /about | (static) | Old marketing content, pipeline docs |
| /tournament/new | NewTournamentPage | Create tournament with seed ideas |
| /tournament/[id] | TournamentBoardPage | Live poker board with SwimLanes + SSE |
| /tournament/[id]/memo | (dynamic) | Decision memo + RealitySpikeCard |
| /ideas/[id] | (dynamic) | Evidence trail timeline per idea |
| /player | PlayerProfiles | CRUD for player profiles |

## Proof Level Stance

The original plan (IMPLEMENTATION_PLAN.md) called for a strict fixture-first, deterministic CLI with no LLM until live proof. The current system is a pragmatic deviation: LLM calls are used per-gate for scoring. The system distinguishes:

- **Fixture proof:** Engine tests against saved tournament inputs/outputs. Tests exist under tests/.
- **Dry-run proof:** API runs locally without live retrieval (uses local anchor data).
- **Live proof:** Dashboard displays real tournament results from the running API.

All proof levels are labeled explicitly in outputs. No claims of production readiness without human approval.

## Dev Setup

```
# Backend
cd C:\experiments\evidentia\main
PYTHONPATH=src python scripts/start_api.py

# Frontend
cd docs/frontend
npx next dev
```
