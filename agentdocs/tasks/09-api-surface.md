# Task: API Surface

**Feature**: [../spec.md](../spec.md)
**Plan Phase**: [Phase 5](../plan.md#phase-5-api-surface-engine-gate-dependent)
**Status**: BLOCKED
**Priority**: P2 (Medium)

## Objective

Add FastAPI + SQLite backend. Endpoints for player profiles, harvest, generate, tournament execution, SSE streaming, memo retrieval.

## In Scope

- `fastapi`, `uvicorn`, `sse-starlette` dependencies
- `db.py`: SQLite migrations for player_profiles, tournaments, idea_states, gate_results
- `api.py`: POST endpoints for player, harvest, generate, tournament; GET for memo; SSE for live tournament progress

## Out of Scope

- Frontend UI (Phase 6)
- Authentication/authorization (internal tool)
- Multi-tenant support

## Dependencies

- Blocked by: Phase 4 engine gate (real-market live smoke must pass first)
