# Feature: Dashboard Cockpit

## Status

- [ ] Draft
- [x] Review
- [x] Approved
- [ ] In Progress
- [ ] Complete

## Overview

A dark-theme Next.js dashboard that lets users run the full Edge idea tournament pipeline from the browser. Users enter a keyword, harvest real demand signals from HN/Reddit/GitHub, generate evidence-backed ideas, run them through the tournament engine with live SSE streaming, and export decision memos - all with startup-grade UX and clear CTAs.

## Live Demo Walkthrough

Using keyword "invoice reconciliation" as the concrete example:

1. User enters `invoice reconciliation` on homepage, clicks **scan ->**
2. Backend `POST /harvest` returns 20+ raw signals from HN/Reddit/GitHub
3. Backend `POST /generate` returns 5-10 evidence-backed ideas with kill conditions, gate profiles
4. User reviews ideas, picks best, clicks **Run Tournament**
5. Poker Board streams live SSE: gates resolve one by one, cards move right on PASS, fade on FAIL
6. BudgetMeter ticks up: `LLM calls: 12/200 | Search: 3/50 | $0.42`
7. Tournament completes, verdicts populate:
   - "AI invoicing for freelancers" -> **PURSUE_SPIKE** (confidence 0.91)
   - "Invoice OCR tool" -> **SHORTLIST** (confidence 0.62)
   - "Invoice marketplace" -> **KILL** (gate: `niche_not_already_owned`)
   - "Invoice API for agencies" -> **INSUFFICIENT_EVIDENCE** (gate: `three_first_person_voices` skipped)
8. User opens Decision Memo, sees winner, diagnosis, reality spike card labeled `LLM_GENERATED_TACTICAL_COPY`
9. From INSUFFICIENT_EVIDENCE idea, user clicks **Re-seed narrower tournament**, new narrower cohort created

## Goals

- Provide a browser-based interface for the full Edge tournament pipeline
- Replace the broken homepage Try It mockup with real API wiring
- Add swim-lane poker board with live SSE streaming
- Surface zero-winner diagnosis and re-entry flow from the UI
- Match startup-quality design: clear CTAs, dark theme, smooth animations

## Non-Goals

- Phase 7 tuning (thresholds remain server-side env vars)
- Multi-tenant auth or billing (internal tool assumption)
- Mobile-native experience (responsive but desktop-first)

## Requirements

### Functional Requirements

1. **[FR-1] Homepage Try It** - Accepts a domain keyword, calls POST /harvest then POST /generate, displays generated ideas in cards with label, cohort, pain_hypothesis, kill_condition
2. **[FR-2] Player Profile CRUD** - Save/Load player profiles via GET/POST /player with JSON editor
3. **[FR-3] Tournament Seed Form** - /tournament/new with anchor picker dropdown, harvest preview toggle, idea JSON editor, gate profile override
4. **[FR-4] Poker Board** - /tournament/[id] shows swim lanes per gate, IdeaCards move right on PASS, fade on FAIL, shimmer on SKIPPED. SSE-streamed live updates.
5. **[FR-5] IdeaCard** - Shows: idea label, current gate name, confidence score, top kill risk, strongest verbatim quote, running LLM cost
6. **[FR-6] BudgetMeter** - Live gauge: LLM calls used / max, search queries used / max, total $ spend. Updates from SSE events.
7. **[FR-7] Decision Memo** - /tournament/[id]/memo with all DecisionMemo fields, RealitySpikeCard with provenance label
8. **[FR-8] Evidence Trail** - /ideas/[id] shows every gate result, every verbatim quote, every posterior, every cost, tagged structural/evidence
9. **[FR-9] Diagnosis** - Zero-winner view: gate histogram (how many ideas killed on each gate) + what-would-flip explanation
10. **[FR-10] ReentryButton** - From any INSUFFICIENT_EVIDENCE idea in memo or board, one-click seed narrower tournament (blocked at max_reentry_rounds)

### Non-Functional Requirements

1. **[NFR-1]** CORS must allow localhost:3000, 127.0.0.1:3000, and any Vercel deployment domain
2. **[NFR-2]** Dark theme using existing design tokens (T.bg, T.surface, T.accent)
3. **[NFR-3]** SSE connection must auto-reconnect on drop
4. **[NFR-4]** Tournament page must handle empty/error states gracefully (no blank screen on bad tournament ID)

## Acceptance Criteria

- [ ] Homepage keyword, harvest signals, generate ideas, display in cards (no /scan dependency)
- [ ] Player profile save/load roundtrips through API
- [ ] Tournament seed form creates a tournament via API
- [ ] Poker board shows live SSE events as swim-lane cards
- [ ] BudgetMeter shows accurate running spend from SSE stream
- [ ] Decision memo loads all fields, reality spike has provenance label
- [ ] Zero-winner diagnosis displays gate histogram
- [ ] ReentryButton creates a narrower tournament with parent_idea_id set
- [ ] CORS preflight returns 200 with correct Allow-Origin header

## Dependencies

- API server running on port 8000 (evidentia.api)
- Existing API endpoints: /player, /harvest, /generate, /tournament, /tournament/{id}/sse, /tournament/{id}/memo, /tournament/{id}/idea/{id}
- Next.js 15 with app router (already set up at docs/frontend/)

## References

- Ultimate plan Phase 6 design section
- Backend API: src/evidentia/api.py
- Frontend: docs/frontend/
- CORS fix already applied to api.py