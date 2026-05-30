# Handoff for Review — Evidentia Reset

## Current State (May 25, 2026)

**Product framing**: Generate → Validate two-part system.
**Canonical workflow**: `edge player → edge generate → edge validate → edge memo`
**Test count**: 84 pass, 1 skip (live harvest — no credentials). **0 failures.**

---

## What Was Done

### Phase 1 — Audit & Archive
- Discovered 21 plan-vs-execution discrepancies (see `docs/archive/reviewer.md`)
- Archived 13 superseded plan docs into `docs/archive/` with INDEX.md
- Created `docs/ACTIVE_PLAN.md` as the single governing doc

### Phase 2 — CLI Consolidation
- Stripped 10 legacy commands from root CLI (`scan`, `audit`, `classify`, `score`, `anchor`, `hunt`, `hunt-all`, `generate`, `loop`, `best`)
- Hard-cut public interface to edge-only:
  - `edge player init-from-file` / `edge player show`
  - `edge generate from-anchor` / `edge generate from-reentry`
  - `edge validate run` / `edge validate export`
  - `edge memo render`
  - `edge tournament run/export` — **deprecated**, delegates to `validate`

### Phase 3 — Module Cleanup
- **Deleted**: `scoring.py`, `critic.py`, `loop.py` and their test files
- **Trimmed**: `outputs.py` — kept only player-profile functions
- **Moved**: Tournament orchestration logic from `cli.py` into `tournament/helpers.py`
- **Exported**: `is_narrower_cohort` as public from `tournament.helpers`

### Phase 4 — API/Server Quarantine
- Rewrote `api.py` as a `create_app()` factory with `db_path` injection
- Decoupled from CLI (no `from evidentia.cli import _run_hunt`)
- Added `/`, `/health`, `/anchors` endpoints
- Fixed `now_utc` keyword args for `upsert_player_profile` and `save_tournament_result`
- Moved server deps (`fastapi`, `uvicorn`, `sse-starlette`, `pydantic`) to `[project.optional-dependencies] server` in `pyproject.toml`

### Phase 5 — Schema Versioning
- All 4 tournament artifact types now carry `"schema_version": 1`:
  - `tournament.json`
  - `memo.json`
  - `discard_log.json`
  - `zero_winner_diagnosis.json`
  - `events.ndjson`

### Phase 6 — Product Rename
- `edge tournament run` → `edge validate run`
- `edge tournament export` → `edge validate export`
- Added `edge generate from-anchor` and `edge generate from-reentry`
- Rewrote `README.md` and `AGENTS.md` to describe generate→validate system
- Updated 10 test files to use `validate` instead of `tournament` in CLI paths

---

## Module Map

```
src/evidentia/
├── __init__.py
├── __main__.py              # python -m evidentia
├── anchor.py                # Anchor loading from YAML
├── api.py                   # QUARANTINED — FastAPI app factory
├── classifier.py            # Gate evaluation via LLM
├── cli.py                   # Canonical CLI (edge tree)
├── confidence.py            # Confidence clamping, rankability
├── db.py                    # QUARANTINED — SQLite persistence
├── generator.py             # Idea generation from anchors
├── models.py                # Pydantic models (Idea, PlayerProfile, etc.)
├── outputs.py               # Player profile read/write
├── profiles.py              # Gate profiles (consumer_app, b2b_saas, etc.)
├── providers.py             # LLM provider chain
├── tournament/
│   ├── __init__.py
│   ├── engine.py            # Core tournament engine
│   ├── gates.py             # Individual gate implementations
│   └── helpers.py           # Shared orchestration helpers
└── verdict_rules.py         # Verdict derivation from gate results
```

---

## Remaining Stale Docs in `docs/` (not yet archived)

These are still in `docs/` root and tell the wrong product story:

| File | Problem |
|---|---|
| `codex_workload_v1_architecture.md` | Describes old architecture, not generate→validate |
| `codex_workload_v1_review.md` | Review of old Codex workload, not current product |
| `next_pivot_v1_architecture.md` | Refers to tournament-as-product direction |
| `phase7_dogfood_retro.md` | Retro on unrelated phase 7 |
| `worklog_2026-04-24.md` | Stale worklog entry |
| `frontend/` (directory) | Quarantined UI — should be moved or clearly marked |

Decision needed: archive these to `docs/archive/`, delete them, or leave as historical reference?

---

## Open Questions / Missing Details

### Q1: `edge generate from-anchor` — LLM provider wiring

The `generate_ideas_from_anchor()` function in `generator.py:268` accepts `env`, `provider`, `model`, and `provider_chain` parameters, but the CLI command (`edge generate from-anchor`) passes none of these. This means generation will fail at runtime unless the provider is auto-configured inside `generator.py`.

**Options:**
1. Inside the CLI command, call `load_external_provider_env()` from `providers.py` before calling `generate_ideas_from_anchor`
2. Make `generator.py` auto-load the environment internally when none is provided
3. Add `edge generate from-anchor --provider` and `--model` flags

**I recommend option 1** — the CLI should wire up the environment, not the generator.

### Q2: Gate profiles and player routing

The `edge generate from-anchor` command currently has no `--profile` override flag, but `generator.py` may infer gate profiles with low confidence. The validate command rejects low-confidence profiles unless `--profile` is passed. Should the generate command also enforce or surface this?

### Q3: Generator output shape ↔ Validator input shape

`generate_ideas_from_anchor()` returns `list[dict]` — plain dicts. The validator's `materialize_ideas()` calls `Idea(**row)` on each row. Are the raw dicts from `generator.py` guaranteed to have all fields `Idea.__init__` expects? Specifically:
- `gate_profile_source` — is it present?
- `parent_idea_id` — is it `None` or absent?
- Are all enum-like fields (e.g., `origin`) valid values?

**Suggested fix**: If not already done, add a test that pipes `edge generate from-anchor` output directly into `edge validate run` to prove the round-trip works.

### Q4: `edge generate from-anchor` — player requirement

The command requires `--player` (defaults to `outputs/profile.json`). Does anchor-driven generation actually need a player profile? The `generate_ideas_from_anchor()` signature takes `anchor` and environment but does not take a `PlayerProfile`. The player requirement may be unnecessary for generation.

### Q5: Anchor YAML resolution

The command does `anchor_dir / "{slug}.yaml"`. Is the slug guaranteed to match the YAML filename 1:1? Some anchors might have different extensions or naming conventions. Checking `anchors_root()` for the listing first would be more robust.

### Q6: 5 acceptance tests exist — ACTIVE_PLAN.md is stale

The `docs/ACTIVE_PLAN.md` says "5 validator acceptance tests (1 exists; 4 to write)". In reality all 5 are written and passing. This should be corrected.

### Q7: Generator acceptance tests — not yet written

The ACTIVE_PLAN calls for generator acceptance tests:
- `from-anchor produces valid JSONL`
- `from-reentry produces valid JSONL from parent tournament`

These don't exist yet. Without them, the generator half of the product is untested at the acceptance level.

---

## Test Coverage

- **Unit tests**: 17 files, covering classifier, gates, confidence, models, profiles, verdict rules, providers, auditor, packaging, imports, reentry narrowing, player profile, no-random, no-legacy, API boundaries
- **Integration tests**: 10 files, covering manual mode, CLI flow, memo render, profile routing, tournament artifacts, event log, engine fixtures, reentry rules, API endpoints
- **Acceptance tests**: 2 files, covering CLI flow (help, canonical surface, legacy isolation, module entrypoint) and tournament engine (5 scenarios)
- **Live tests**: 2 files — 1 harvest smoke (skipped w/o env), 1 tournament budget (passes w/ live LLM)

---

## Quarantine Status

| Component | Status | Gate to lift |
|---|---|---|
| `api.py` | Quarantined (optional deps) | Live generate-then-validate proof |
| `db.py` | Quarantined (used by API) | Live proof |
| `docs/frontend/` | Quarantined | Live proof |

---

## Quick Verification

```powershell
cd C:\experiments\evidentia\main
$env:PYTHONIOENCODING="utf-8"
python -m pytest tests/ -v --tb=short
```

Expected: 84 passed, 1 skipped.

```powershell
# Smoke test the canonical workflow
$env:PYTHONPATH="src"
python -m evidentia.cli --help
python -m evidentia.cli edge --help
python -m evidentia.cli edge generate --help
python -m evidentia.cli edge validate --help
```
