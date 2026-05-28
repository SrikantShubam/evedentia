# Handoff — 01-player-profile (coder-b)

**Branch**: `feat/coder-b/01-player-profile`  
**Date**: 2026-05-28  
**Status**: DONE (fixture proof)  
**Test verification**: `python -m pytest tests/ -q` → **99 passed, 1 skipped, 0 failures** (32s)

---

## Deliverable

Implemented the Player Profile CLI entrypoint per canonical workflow (`edge player → ...`):

- `edge player init-from-file <path>`  
  Loads flat profile JSON, constructs `PlayerProfile` (triggers validation), writes wrapped artifact to `outputs/profile.json` (or `--output` override).

- `edge player show` (default `--profile outputs/profile.json`)  
  Prints the current profile as formatted JSON (inner player_profile dict).

## Validation (hard gates per AGENTS.md)

All validation lives in `PlayerProfile.__post_init__` (models.py:131):

- `risk` ∈ {"low", "med", "high"} (else ValueError)
- budgets (`validate`/`build`/`reach`) ≥ 0 (else "budgets must be non-negative")
- Additional: id/team non-empty, weeks_to_ship > 0, max_* > 0, max_reentry_rounds ∈ [0,3]

`load_player_profile_from_path` (helpers.py:28) does `PlayerProfile(**payload)` → validation fires on any load.

## Files (phase ownership)

- `src/evidentia/models.py` — PlayerProfile dataclass + __post_init__ guards
- `src/evidentia/outputs.py` — write_player_profile (schema_version wrapper), read_player_profile
- `src/evidentia/tournament/helpers.py` — load_player_profile_from_path / load_player_profile_any
- `src/evidentia/cli.py` — edge_player_group with init-from-file + show (click wiring)
- `tests/unit/test_player_profile.py` — roundtrip CLI test + `test_player_profile_rejects_invalid_risk` + new `test_player_profile_rejects_negative_budgets`
- `agentdocs/tasks/01-player-profile.md` — status + AC checkboxes updated

## Test Results (actual)

```
99 passed, 1 skipped, 1 14 warnings in 32.09s
```

New budget test exercises all three negative fields and matches the exact error string from model.

Existing CLI roundtrip test exercises:
- init-from-file (flat JSON source → wrapped output)
- show (reads wrapped, emits inner .to_dict())
- Both exit_code==0, content assertions pass

## Acceptance vs Reality

- Valid load/save: ✅ (write wraps, read unwraps, roundtrip fields match)
- Invalid rejected: ✅ (pytest covers risk + all budgets <0)
- show prints: ✅ (json.dumps indent=2 of profile dict)
- Round-trip byte-match: ⚠️ not literal (source flat vs persisted wrapped + defaults filled). Semantic fidelity verified in test.

## Handoff Notes (per AGENTS.md)

- This is **fixture proof** (deterministic tests against saved inputs via CliRunner + model). Not dry-run or live.
- No SQLite (out of scope, Phase 5).
- Error UX: ValueError bubbles to Click → stacktrace on bad profile. Acceptable for phase 0; later commands (validate) use it internally via load_player_profile_any.
- No change to hard-gate vs heuristic distinction (player profile only supplies budgets/risk).
- Quarantined code untouched.

## Next

Ready for consumer of profile: `edge generate` / `edge validate run --player outputs/profile.json`

Handoff artifact for orchestrator / coder-a or subsequent phases.

---

**Proof command (repro)**:
```powershell
python -m pytest tests/unit/test_player_profile.py -q --tb=line
python -m pytest tests/ -q
```
