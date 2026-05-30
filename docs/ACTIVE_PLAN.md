# ACTIVE PLAN — Evidentia

## Product

Generate → Validate two-part system.

Canonical workflow: `edge player → edge generate → edge validate → edge memo`

## Subsystems

- **Generator** (`edge generate from-anchor`, `edge generate from-reentry`) — produces candidate ideas with kill_condition, gate_profile, evidence_ids
- **Validator** (`edge validate run`) — player-aware gate execution, budget control, deterministic verdicts, memo assembly

## What is Archived

- `docs/archive/reviewer.md` — one-time plan-drift review; not an ongoing plan
- All prior plans (`final_pivot.md`, `IMPLEMENTATION_PLAN.md`, `NEXT_PIVOT.md`, etc.) are in `docs/archive/` — historical records, not implementation guides

## What is Quarantined

Until live proof is established:
- `src/evidentia/api.py`, `db.py` — server/API code
- `docs/frontend/` — cockpit UI

API vocabulary (tournament routes) may remain inconsistent with the
public generate→validate language until quarantine is lifted.

## Test Contract

- 5 validator acceptance tests (all 5 present and passing)
  - `test_acceptance_strong_evidence_has_terminal_viable_winner` → PURSUE_SPIKE / SHORTLIST
  - `test_acceptance_happy_incumbent_zero_winner_diagnosis_mentions_niche_gate` → all KILL; niche_not_already_owned
  - `test_acceptance_no_spend_zero_winner_diagnosis_mentions_wtp` → INSUFFICIENT_EVIDENCE; willingness_to_pay
  - `test_acceptance_budget_exhausted_unrankable_has_no_winner` → is_rankable=False, winner=None
  - `test_acceptance_profile_routing_uses_b2b_gates` → B2B runs B2B gates
- Generator acceptance tests (present and passing)
  - `test_generate_from_anchor_produces_jsonl_consumable_by_validate` → from-anchor produces valid JSONL
  - `test_generate_from_reentry_produces_jsonl_consumable_by_validate` → from-reentry produces valid JSONL

## Assumptions

1. The engine is the only execution path. Scan/hunt/loop/legacy pipelines are dead.
2. Player profiles control gate routing and budgets.
3. LLM calls for gate evaluation happen within player budget.
4. All tournament outputs carry `schema_version: 1`.
5. CLI is the canonical interface. Server/API/UI are deferred.
