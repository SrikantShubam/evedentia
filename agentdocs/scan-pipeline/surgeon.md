# Agent Task: SURGEON — POST /validate Endpoint

## Role
You remove what's dead. You add exactly what's asked. You verify with tests. You commit when green.

## Pre-Read Contract (MUST read these files before touching any code)

Read these files IN ORDER:

1. `src/evidentia/api.py` — all endpoints, request models, imports
2. `src/evidentia/models.py` — Idea, IdeaState, TournamentResult dataclasses
3. `src/evidentia/tournament/engine.py` — `run_tournament` function signature
4. `src/evidentia/db.py` — `get_player_profile`, `save_tournament_result`

## What to Build

### Add `POST /validate` endpoint to `src/evidentia/api.py`

**Request model:**

```python
class ValidateRequest(BaseModel):
    keyword: str                          # Original search keyword (required, non-empty)
    opportunity: dict                     # Scan opportunity object
    player_id: str = "default"            # Player profile ID
    gate_profile: str | None = None       # Gate profile override
```

**Endpoint:**

```
POST /validate
  Request: ValidateRequest
  Response: TournamentResult.to_dict() — flattened with id/label at top level of each idea state
  Errors: 404 if player not found, 400 if keyword empty
```

**Idea construction mapping (CRITICAL — verify with tests):**

```
Idea fields from opportunity dict:

  id       = opp["opportunity_id"] or f"opp-{timestamp}"
  label    = first truthy of: opp.label, opp.title, opp.hypothesis.headline, keyword
  anchor_slug = keyword.lower().replace(" ", "-")[:50]
  incumbent = "unknown"
  cohort   = first truthy of: opp.cohort, opp.hypothesis.hypothesis_type, "unknown"
  pain_hypothesis = first truthy of: opp.pain_hypothesis, opp.hypothesis.wedge_statement, "No hypothesis recorded"
  kill_condition = {
    description: f"Scan verdict: {verdict}. Score: {score}",
    gate_name: (opp.gate_failures or ["scan_gate"])[0]
  }
  evidence_ids = [f"sig-{i+1}" for i in range(len(signals))] or ["sig-1"]
  search_queries = [keyword]
  origin = "scan"
  gate_profile = request.gate_profile or "consumer_app"
  gate_profile_source = "inferred:scan"
```

**Flow:**
1. Validate keyword is non-empty
2. Look up player profile (404 if not found)
3. Construct Idea from opportunity + keyword using mapping above
4. Generate unique tournament_id: `f"scan-{YYYYMMDD}-{HHMMSS}-{idea_id[:8]}"`
5. Call `run_tournament(ideas=[idea], player=profile, tournament_id=tid, gate_profile=...)`
6. Save result to DB
7. Return result.to_dict()

**Add deprecation comments** to the old tournament routes (GET /tournament/{id}, etc.):
```
# DEPRECATED: Dashboard now uses inline TournamentPanel. Kept for backward compat.
```

## Tests to Pass

```bash
cd C:\experiments\evidentia\main
PYTHONPATH=src pytest tests/unit/test_validate_endpoint.py -v
```

## Smoke Test

```bash
PYTHONPATH=src python -c "from evidentia.api import create_app; app=create_app(); print('OK')"
```

## Commit

```bash
git add -A
git commit -m "feat: add POST /validate endpoint for scan-opportunity-to-tournament flow"
```

## PR

```bash
gh pr create --base feat/edge-tournament-phase0 --head feat/edge-tournament-phase0 --title "feat: POST /validate endpoint" --body "Converts scan opportunities into valid tournament Ideas server-side. See tests/unit/test_validate_endpoint.py."
```

## Exit Gate (you're done when)

- [ ] All 16 tests in `test_validate_endpoint.py` pass
- [ ] `from evidentia.api import create_app` loads without error
- [ ] Deprecation comments added to old tournament routes
- [ ] No new imports fail
