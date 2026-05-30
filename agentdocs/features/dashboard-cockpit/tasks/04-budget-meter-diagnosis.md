# Task: BudgetMeter + Diagnosis Components

## Agent
Subagent D

## Requirements
FR-6: BudgetMeter - live gauge component
FR-9: Diagnosis - zero-winner gate histogram + what-would-flip explanation

## Spec Reference
- spec.md FR-6, FR-9

## What to Build
### BudgetMeter (FR-6)
Build a BudgetMeter component that shows:
- LLM calls used / max (from max_llm_calls_per_tournament in PlayerProfile)
- Search queries used / max (from max_paid_queries_per_tournament)
- Total $ spend (sum of llm_cost_usd across all gate events)

Visual style: horizontal bars or gauge indicators, updates from SSE gate events.
Integrate into the poker board page header.

### Diagnosis Component (FR-9)
Build a Diagnosis component for zero-winner tournaments:
- Gate histogram: for each gate, show count of ideas killed on that gate
- Color coding: red for structural gates, yellow for evidence gates
- What-would-flip text: extracted from memo.zero_winner_diagnosis if available
- Only shown when no winner exists (all terminal_verdict != PURSUE_SPIKE)

Integrate Diagnosis into the poker board page (below final snapshot).

## API Endpoints
- SSE events provide llm_cost_usd per gate event
- GET /tournament/{id} -> payload has all idea states + memo data

## Files to Edit/Create
- docs/frontend/app/tournament/[id]/page.tsx (integrate components)
- Consider creating docs/frontend/components/BudgetMeter.tsx
- Consider creating docs/frontend/components/Diagnosis.tsx

## Acceptance
- [ ] BudgetMeter shows LLM calls / max as a bar
- [ ] BudgetMeter shows search queries / max as a bar
- [ ] BudgetMeter shows total spend updated from SSE
- [ ] Diagnosis shows gate histogram when no winner
- [ ] Diagnosis shows what-would-flip text from memo