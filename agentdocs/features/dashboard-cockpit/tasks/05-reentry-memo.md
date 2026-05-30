# Task: ReentryButton + Memo Polish

## Agent
Subagent E

## Requirements
FR-7: Decision Memo with RealitySpikeCard (provenance labeled)
FR-10: ReentryButton on INSUFFICIENT_EVIDENCE ideas

## Spec Reference
- spec.md FR-7, FR-10
- Current memo page at docs/frontend/app/tournament/[id]/memo/page.tsx

## What to Build
### RealitySpikeCard (FR-7)
Polish the memo page RealitySpike section to be a prominent card:
- Visual card with border accent, icon, and provenance badge:
  Badge text: 'LLM_GENERATED_TACTICAL_COPY' in monospace with warning color
- Display all RealitySpike fields:
  - target_customer_profile
  - outreach_message
  - landing_page_headline + subhead
  - interview_questions (list of 5)
  - success_criteria + fail_criteria
  - weeks_to_run
- Only shown when memo.reality_spike exists (winner terminal_verdict == PURSUE_SPIKE)

### ReentryButton (FR-10)
Build a ReentryButton component:
- Shows on any idea with terminal_verdict == INSUFFICIENT_EVIDENCE
- Label: 'Seed narrower tournament'
- On click: POST /tournament with:
  - tournament_id: new UUID
  - player_id: same as parent
  - ideas: narrowed version of the idea (add 'narrower:' prefix to cohort)
  - gate_profile: same as parent
  - parent_tournament_id: current tournament ID
- Navigate to /tournament/[new_id] on success
- Disabled if reentry_depth >= max_reentry_rounds (show reason tooltip)
- Integrate into both: memo page and poker board idea cards

## API Endpoints
- GET /tournament/{id}/memo -> DecisionMemo
- POST /tournament -> creates new tournament

## Files to Edit/Create
- docs/frontend/app/tournament/[id]/memo/page.tsx (add RealitySpikeCard)
- docs/frontend/app/tournament/[id]/page.tsx (add ReentryButton to idea cards)
- Consider components/ReentryButton.tsx
- Consider components/RealitySpikeCard.tsx

## Acceptance
- [ ] RealitySpikeCard shows provenance badge: LLM_GENERATED_TACTICAL_COPY
- [ ] All reality spike fields displayed
- [ ] ReentryButton visible on INSUFFICIENT_EVIDENCE ideas
- [ ] Clicking creates new tournament with parent_idea_id
- [ ] Button disabled when reentry_depth >= max_reentry_rounds