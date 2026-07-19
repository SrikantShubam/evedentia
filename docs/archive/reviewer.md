# PLAN-DRIFT POSTMORTEM — Evidentia (Critical)

**Reviewer:** Senior Consultant (21 findings)
**Date:** 2026-05-25

---

## 1. THE NUMBERS

| Metric | Value |
|---|---|
| Plan documents on disk | 7+ (each "supersedes" the last) |
| Competing CLI workflows | 3 (scan pipeline / hunt pipeline / tournament pipeline) |
| Phases built out-of-order | 5-7 built BEFORE Phase 3-4 gate was met |
| Test-first commits | 0 of 28 commits |
| Retirement directives ignored | 3 modules (`scoring.py`, `critic.py`, `loop.py`) still alive |
| Tournament acceptance tests written | 1 of 5 required scenarios |
| Live markets validated before Phase 5 | 0 |
| Total LOC in src | 3691 |
| `cli.py` as % of src | 30.2% (1114 lines) |

---

## 2. THE PLAN DIED SEVEN TIMES

The directory has **7+ planning documents** at different levels of granularity:

- `final_pivot.md` — "scan → spec → build → ship → track" (SQLite, Pydantic, hard gates)
- `IMPLEMENTATION_PLAN.md` — TDD with failing tests first, per-task checkboxes
- `NEXT_PIVOT.md` — "never mind, niche hunter" (delete builder/ship/track, add anchors)
- `NEXT_PIVOT_WORKORDERS.md` — WO-1..9, delete drifted modules, fix bugs
- `NEXT_PIVOT_WORKORDERS_P2.md` — WO-10..19, the niche hunter loop
- `CODEX_WORKORDERS.md` — WO-1..9 for the original pipeline bugs
- `ultimate plan.md` — "never mind, adversarial tournament engine" (engine-first, cockpit deferred)

Each one says it supersedes the previous one. Each one is **partially implemented**. The codebase is a museum of abandoned directions still wired in.

---

## 3. THE PHASE 5-7 DISASTER

`ultimate plan.md` restriction #12, in bold:

> **Do not start Phase 5 until Phase 4's engine gate is met on real markets.**

The April 24 work log says:

> *"Executed the remaining 'ultimate plan' work across tournament engine, memo mechanics, API/database, and cockpit routes."*

That is **Phases 0-7 in a single day** — models, engine, memo, API (`api.py`, `db.py`), frontend cockpit, and Phase 7 tuning settings — before the engine ever ran against a real market. The Phase 4 engine gate (2-3 live tournaments) was never met. The Phase 7 dogfood retro says "live tests skipped due to anchor proof verifiability constraints."

You built **Phase 7 tuning knobs** for an engine that has never been validated on real data. You shipped the cockpit before anyone sat in the engine.

---

## 4. THE SURVIVING DEAD

`ultimate plan.md` section "Retire (explicit disposition)":

> `scoring.py` (267) — **retire**; replaced by `tournament/gates.py` + `tournament/confidence.py`
> `critic.py` (296) — **retire**; replaced by `tournament/engine.py` + `tournament/memo.py`
> `loop.py` (149) — **retire**; folded into `tournament/engine.py`

All three files still exist. `cli.py:28` still imports from `scoring.py`. The critic pipeline (`_run_hunt` → `cluster_signals` → `critique_slice`) still runs alongside the tournament engine. You have **two complete scoring engines** wired into the same CLI. The old one was supposed to be deleted. It was not. No deprecation warning. No migration. Just silent dead code nobody will touch because nobody knows if removing it will break something.

**Confirmed imports of retired modules:**

| Retired module | Imported by | Line |
|---|---|---|
| `scoring.py` | `cli.py` | 28 |
| `critic.py` | `cli.py` | 12 |
| `critic.py` | `loop.py` | 9 |
| `loop.py` | `cli.py` | 1072 |

---

## 5. THE THREE-HEADED CLI

```
evidentia scan --fixture ...     # Phase 0-1: original pipeline
evidentia anchor list            # Phase 2: niche hunter
evidentia hunt bible-app         # Phase 2: niche hunter
evidentia loop --iterations 10   # Phase 2: niche hunter orchestrator
evidentia edge tournament run    # Phase 3: tournament engine
evidentia edge memo render       # Phase 4: decision memo
```

Three different workflow paradigms in one CLI. Three different input formats. Three different output schemas. If a new developer asks "how do I run this?", the honest answer is "which version?"

---

## 6. 21 FINDINGS

---

### Finding 1 — Plan proliferation
**Severity:** CRITICAL

7+ planning documents, each superseding the previous, but code from ALL of them persists simultaneously. The CLI has THREE workflow paradigms co-existing. Documents in `main/` that serve no execution purpose: `COMPARATIVE_ANALYSIS.md`, `SCAN_REVIEW.md`, `REVIEW_REPORT.md` — these are analysis artifacts, not plans. They clutter the working directory alongside active implementation guides.

---

### Finding 2 — Phase 5-7 built before Phase 3-4 gate met
**Severity:** CRITICAL

`ultimate plan.md` restriction #12: "Do not start Phase 5 until Phase 4's engine gate is met on real markets." Yet `api.py` (172 lines), `db.py` (193 lines), `docs/frontend/` (cockpit routes), and `tournament/settings.py` (Phase 7 tuning) were all built in the same commit range as the engine (`a88c620`, `0bba4dd`, `f8e7157`). The engine was never validated on live data. The Phase 7 retro confirms: "Live tests skipped due anchor proof-verification availability."

---

### Finding 3 — Retired code still imported and active
**Severity:** HIGH

Three modules the plan says to retire are still imported in production code paths:

| Module | Plan directive | Current status |
|---|---|---|
| `scoring.py` (225 lines) | "retire; replaced by tournament/gates.py + confidence.py" | Imported by `cli.py`, `test_scoring.py` tests exist |
| `critic.py` (246 lines) | "retire; replaced by tournament/engine.py + memo.py" | Imported by `cli.py` and `loop.py` |
| `loop.py` (127 lines) | "retire; folded into tournament/engine.py" | Imported by `cli.py` behind conditional import |

---

### Finding 4 — Three competing CLI workflows
**Severity:** HIGH

The CLI exposes three unrelated workflow paradigms that represent three different product visions:

1. **Original pipeline:** `scan --fixture`/`scan --live` → `audit` → `classify` → `score` — built for `final_pivot.md`
2. **Niche hunter:** `anchor list` → `anchor verify` → `hunt` → `generate` → `loop` → `best` — built for `NEXT_PIVOT.md`
3. **Tournament engine:** `edge player init-from-file` → `edge tournament run` → `edge memo render` — built for `ultimate plan.md`

Each has its own data models, output format, and execution flow. None is deprecated. None is canonical.

---

### Finding 5 — Zero test-first commits
**Severity:** HIGH

`IMPLEMENTATION_PLAN.md` explicitly says: "Write the failing test before implementation in every task." Git history shows **zero commits** with the pattern "Add test for..." followed by "Implement...". Every commit is "Add <feature>" or "Implement <feature>". Tests were written after — or alongside — implementation, never before. This means no code was driven by a failing test.

---

### Finding 6 — Live pipeline produces 100% HOLD
**Severity:** CRITICAL

`SCAN_REVIEW.md` documents this thoroughly: on a legitimate query (`expense tracking`), the pipeline returned 9/9 HOLD. The classifier prompt embeds example values that the LLM copies verbatim. The `_normalize_gate` function defaults unknown labels to `"fail"`. The system scores 3/10 in the scan review. Fix work orders (WO-5, WO-6) exist but their effectiveness has not been re-validated against live data.

---

### Finding 7 — Auditor does no page fetching
**Severity:** CRITICAL

`auditor.py:verify_quote` is a substring check against the scanner's API response text — not the actual page at `source_url`. For items where `source_text` is the post title, the function verifies the title against itself — a tautology. WO-3 exists to fix this. The fix may or may not be applied (the current `auditor.py` has `_fetch_page_text` — needs verification that it's wired correctly).

---

### Finding 8 — `LIVE_SCANNERS["hn"] = None` existed
**Severity:** HIGH

`REVIEW_REPORT.md` FP-03: the HN live scanner was registered as `None` in the `LIVE_SCANNERS` dict. Fixed in WO-2 (commit `3b19d8e`). Current `scanners/__init__.py` shows correct registration. This is **confirmed fixed** — but it should never have shipped.

---

### Finding 9 — `can_deploy` type bug existed
**Severity:** HIGH

`REVIEW_REPORT.md` FP-05: `can_deploy({"approved": "true"})` would return a string, which is truthy, bypassing the deploy gate. Fix was attempted in WO-2. Current code needs verification that the strict `is True` check is in place.

---

### Finding 10 — Models unused in production
**Severity:** MEDIUM

`SourceEvidence` (Pydantic `BaseModel` at `models.py:53`) and `ProductSpec` (Pydantic `BaseModel` at `models.py:346`) exist in `models.py` but have zero production usage. `SourceEvidence` was used by the deleted `spec_writer.py`. `ProductSpec` was used by the deleted `builder.py`/`deployer.py`. Both are dead code taking up space and confusing the model layer. The entire Pydantic model path is dead; the production pipeline uses `@dataclass` exclusively.

---

### Finding 11 — `rich` dependency removed undocumented
**Severity:** LOW

`CODEX_WORKORDERS.md` WO-9 explicitly decided to **wire** `rich` into `cli.py`, not remove it. The current `pyproject.toml` has no `rich` dependency. `cli.py` still uses `click.echo` for everything. The decision was reversed without documentation. Either the WO decided wrong and should document the reversal, or the fix is incomplete.

---

### Finding 12 — Scoring weights extracted
**Severity:** MEDIUM (positive)

`CODEX_WORKORDERS.md` WO-8 was executed correctly: `scoring.py` now has `WEIGHT_COMPETITION_GAP`, `WEIGHT_BUILDABILITY`, `WEIGHT_REACHABILITY` as module-level constants with a sum-to-1.0 assert. This is one work order that was completed as specified.

---

### Finding 13 — `api.py` imports private CLI function
**Severity:** HIGH

File: `src/evidentia/api.py`, line 11:

```python
from evidentia.cli import _run_hunt
```

A production FastAPI server importing a **private** function (prefixed with underscore, indicating "implementation detail, do not call externally") from a CLI module. If anyone refactors `_run_hunt`'s signature or behavior, the API silently breaks at runtime. The correct architecture is for both CLI and API to call a shared service layer. Neither exists.

---

### Finding 14 — Two serialization paradigms in one file
**Severity:** MEDIUM

`models.py` mixes two incompatible serialization patterns:

| Type | Pattern | Status |
|---|---|---|
| `DemandSignal` | `@dataclass` + manual `to_dict()` | Active |
| `Anchor`, `Slice`, `SliceVerdict` | `@dataclass` + manual `to_dict()` | Active |
| `PlayerProfile`, `Idea`, etc. | `@dataclass` + manual `to_dict()` | Active |
| `SourceEvidence` | Pydantic `BaseModel` | **Dead code** |
| `ProductSpec` | Pydantic `BaseModel` | **Dead code** |

Every new contributor must learn two serialization patterns. The Pydantic types add import cost, maintenance burden, and cognitive overhead for zero benefit.

---

### Finding 15 — Phase 5 deps are hard requirements
**Severity:** HIGH

`pyproject.toml:16-18`:

```
dependencies = [
  "fastapi>=0.115,<1",
  "uvicorn[standard]>=0.30,<1",
  "sse-starlette>=2.1,<3",
]
```

These are Phase 5 dependencies (API server, SSE streaming) listed as **required** installs. A user running `pip install evidentia` to use the CLI gets FastAPI + uvicorn + SSE dependencies pulled in automatically. These should be `[project.optional-dependencies] server = [...]`. Every CI install is slower. Every developer installs server code they don't need. This violates the explicit instruction not to start Phase 5 until the engine gate is met.

---

### Finding 16 — Tournament outputs missing `schema_version`
**Severity:** MEDIUM

Every artifact in the NEXT_PIVOT pipeline writes `schema_version` (`outputs.py:85-89`). The tournament output (`tournament.json`, `memo.json`) does not. The NEXT_PIVOT_WORKORDERS_P2 guardrail #4 states:

> "No new artifact without a schema_version. All JSON artifacts get 'schema_version': 1"

The tournament violates this. There is no way to distinguish a v1 tournament result from a hypothetical v2, making future schema migrations impossible without manual inspection. `TournamentResult.to_dict()` and memo serialization must add `schema_version`.

---

### Finding 17 — `rich` removed instead of wired per WO
**Severity:** LOW

`CODEX_WORKORDERS.md` WO-9: "Decision: wire it up (do not remove)." Current `pyproject.toml` has no `rich` dependency. The decision to wire was reversed without documentation. `cli.py` still uses `click.echo`. The work order was neither executed as specified nor documented as overridden.

---

### Finding 18 — `pyyaml` dependency appeared undocumented
**Severity:** LOW

`pyproject.toml` has `pyyaml>=6.0,<7` — used for anchor YAML loading. No plan document mentions this dependency. It appeared silently. Common dependency, correct choice, but represents undisclosed scope change.

---

### Finding 19 — `cli.py` is a 1114-line god module (30.2% of src)
**Severity:** MEDIUM

| Module | Lines | % of src |
|---|---|---|
| `cli.py` | 1114 | 30.2% |
| Rest of src (13 files) | 2577 | 69.8% |

This single file contains: CLI command definitions, hunt orchestration, semantic clustering with Jaccard similarity, signal classification rejection rules, hypothesis generation, prosecution logic, tournament seeding validation, cohort narrowing, markdown rendering, and NDJSON event writing. The plan calls for thin CLI commands. This is the opposite.

---

### Finding 20 — Tournament acceptance tests: 1 of 5 required scenarios exist
**Severity:** HIGH

`ultimate plan.md` Phase 3 specifies 5 acceptance scenarios:

| Scenario | Exists? | File |
|---|---|---|
| Strong-evidence fixture → PURSUE_SPIKE / SHORTLIST | ❌ | — |
| Happy-incumbent fixture → all KILL; diagnosis cites niche_not_already_owned | ❌ | — |
| No-spend fixture → INSUFFICIENT_EVIDENCE; diagnosis cites willingness_to_pay | ❌ | — |
| Budget-exhaustion → is_rankable=False, winner=None | ❌ | — |
| Profile routing: B2B fixture runs B2B gates, not consumer | ✅ | `test_tournament_engine_acceptance.py` |

Only 1 of 5 acceptance tests exists. The acceptance criteria is the "definition of done" for Phase 3. Phase 3 is not done.

---

### Finding 21 — API has two pipeline paradigms wired in
**Severity:** HIGH

`api.py` exposes both workflow paradigms through HTTP:

| Endpoint | Pipeline | Origin |
|---|---|---|
| `POST /harvest` | Hunt pipeline (anchor → listen → cluster → critique) | Phase 2 (NEXT_PIVOT) |
| `POST /generate` | Idea generator | Phase 2 (NEXT_PIVOT) |
| `POST /tournament` | Tournament engine | Phase 3 (ultimate plan) |

The API is the most visible integration point and it has TWO competing pipelines wired in. When one is eventually deleted, the API must either break backward compatibility or maintain dead endpoints. This is the same problem as the three-headed CLI, now exposed over HTTP.

---

## 7. THE FIXES (Non-negotiable)

### Fix 1 — Pick one plan. Burn the others.
Decide which plan is canonical. Move the rest to `docs/archive/` with a single `ARCHIVE_INDEX.md` that says "these are historical records, not implementation guides." Stop pretending 7 plans are better than 1 plan.

### Fix 2 — Retire the dead.
Check `ultimate plan.md` section "Retire." If the retirement table says delete a module, delete it. If `cli.py` imports from it, remove the import. If a test depends on it, rewrite the test.

Deliverable: `grep -r "from evidentia.(scoring|critic|loop)" src/` returns empty.

### Fix 3 — CLI surgery. One workflow, one namespace.
Pick one:
- **If the tournament engine is the future**: delete `scan`, `hunt`, `hunt-all`, `loop`, `generate`, `best` commands. Deprecate first, remove after one sprint.
- **If the niche hunter is the future**: delete `edge` commands. Keep `anchor` → `hunt` → `loop`.

Having both guarantees neither works well. The team's attention is split between three competing abstractions for the same problem.

### Fix 4 — The engine gate. Real markets, no excuses.
Do not touch `api.py`, `db.py`, `docs/frontend/`, or `tournament/settings.py` until:
1. Three live tournaments have run against real verified anchors within budget.
2. The kill-gate histogram and spend records are in a commit, not a work log.
3. At least one `PURSUE_SPIKE` has been reviewed by a human and judged non-embarrassing.

Until then, Phase 5-7 code is speculative infrastructure for a system that may not work. This is what restriction #12 was for. You violated it.

### Fix 5 — Stop writing plans. Write tests.
For every new module, the test file must exist and fail before the implementation is written. Enforce this with a pre-merge check: `git diff --name-only HEAD~1` must show test files appearing before or in the same commit as the implementation they test.

### Fix 6 — decouple API from CLI.
Extract `_run_hunt` into a shared service module. Both `cli.py` and `api.py` import from the service, not from each other. Private functions (underscore-prefixed) are not a public API.

### Fix 7 — Add `schema_version` to tournament outputs.
Add `schema_version: 1` to `tournament.json`, `memo.json`, and all tournament-related JSON artifacts. Without this, future schema changes are untrackable.

### Fix 8 — Move Phase 5 deps to optional.
`fastapi`, `uvicorn`, `sse-starlette` belong in `[project.optional-dependencies] server`. The base install should be CLI-only. This is the minimum bar for a project that hasn't validated its core engine.

### Fix 9 — Write the 4 missing acceptance tests.
`test_tournament_strong_evidence`, `test_tournament_happy_incumbent_zero_winner`, `test_tournament_no_spend_zero_winner`, `test_tournament_budget_exhausted_unrankable`. Without these, Phase 3 is incomplete.

### Fix 10 — Split `cli.py`.
1114 lines is not a CLI file. Extract: hunt logic → `hunt.py`, clustering helpers → `clusterer.py`, tournament seeding → `tournament/cli.py`. `cli.py` should be command definitions only.

---

## 8. THE REAL COST

The project has been in development for **10 days** across three pivots (April 14 → April 17 → April 24) and has produced:

- 3691 lines of Python across 14 source modules
- 56 test files
- 7 planning documents
- 3 abandoned workflow paradigms
- Zero live-market validated outputs
- Phases 5-7 built before Phase 3-4 were validated
- 21 documented plan-execution deviations

The problem is not technical. The problem is that every time a plan says "validate before building," the team builds anyway. Every time a plan says "retire this module," the team keeps importing it. Every time a plan says "write the test first," the team writes the feature first.

Plans are not being executed. They are being referenced after the fact to justify whatever was built. That is not plan-driven development. That is retrospective storytelling with markdown files.
