# Phase 7 Dogfood + Tuning Retro

Date: 2026-04-24  
Branch: `feat/edge-tournament-phase0`

## Scope

- Validate engine + memo + API flow with fixture-backed tests.
- Attempt live tournament smoke under budget.
- Record tuning knobs and recommended next adjustments.

## Verification Evidence

- Fixture-backed suite:
  - `pytest -q tests/unit/test_classifier.py tests/unit/test_generator.py tests/unit/test_reviews_scanner.py tests/unit/test_cli_smoke.py tests/unit/test_models.py tests/unit/test_player_profile.py tests/unit/test_profiles.py tests/unit/test_confidence.py tests/unit/test_verdict_rules.py tests/unit/test_gates.py tests/unit/test_no_random_in_src.py tests/unit/test_memo_fields_mechanical.py tests/unit/test_reentry_narrowing.py tests/integration/test_tournament_engine_fixture.py tests/integration/test_profile_routing_low_conf_requires_flag.py tests/integration/test_memo_render.py tests/integration/test_manual_mode_requires_evidence.py tests/integration/test_tournament_event_log.py tests/integration/test_tournament_reentry_rules.py tests/integration/test_tournament_artifacts_export_parity.py tests/integration/test_api_tournament_endpoints.py tests/acceptance/test_tournament_engine_acceptance.py`
  - Result: `71 passed`.

- Live suite:
  - `pytest -q tests/live -m live`
  - Result: `5 skipped` due anchor proof verifiability constraints on currently available anchors.

## Observations

- Engine deterministic verdict rules are stable across fixture scenarios.
- Re-entry constraints (narrower cohort + new evidence + depth cap) are enforced.
- Memo fields are mechanical and evidence-linked (gate/evidence references present).
- API/DB and CLI memo parity is deterministic for fixture paths.

## Tuning Knobs Added

These can now be tuned without code edits:

- `EVIDENTIA_SHORTLIST_CONFIDENCE_THRESHOLD` (default `0.35`)
- `EVIDENTIA_CONFIDENCE_FLOOR` (default `0.5`)
- `EVIDENTIA_CONFIDENCE_CEIL` (default `0.95`)

Source: `src/evidentia/tournament/settings.py`.

## Recommended Next Tuning Pass

1. Run 3 live tournaments on verified anchors once proof URLs are updated.
2. Capture kill-gate histogram and spend per tournament from `events.ndjson`.
3. Raise threshold if weak ideas reach `PURSUE_SPIKE`; lower if all strong ideas stay `SHORTLIST`.
4. Adjust floor/ceil only if gate confidences collapse to narrow bands.

## Blockers

- Live gate remains environment-dependent because anchor proof URLs must pass verification first.
- Until verified live anchors are available, Phase 7 cannot be closed with empirical market outcomes.
