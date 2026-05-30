# Task: Repair Homepage Try It Section

## Agent
Subagent A

## Requirements
FR-1: Homepage Try It section wired to real API endpoints

## Spec Reference
- spec.md FR-1: Accept keyword -> POST /harvest -> POST /generate -> display idea cards
- Current homepage calls /scan which returns 404

## What to Do
1. In `app/page.tsx`, replace the runScan() function:
   - Call POST /harvest with {anchor_slug, limit, dry_run}
   - Then call POST /generate with {anchor_slug, count}
   - Display resulting ideas as cards with: label, cohort, pain_hypothesis, kill_condition
2. Handle loading spinner, empty state (no results), error state (API down)
3. Keep existing source selectors (HN/Reddit/GitHub) as UI, but they don't need to filter server-side (harvest is per-anchor)
4. Add a CTA button per idea card: Run Tournament -> navigates to /tournament/new with idea pre-filled

## API Endpoints
- POST /harvest: {anchor_slug, limit=20, dry_run=false}
- POST /generate: {anchor_slug, count=10}

## Files to Edit
- docs/frontend/app/page.tsx (TryItSection function, ~lines 1490-1699)

## Acceptance
- [ ] Enter keyword, click scan -> shows loading -> shows idea cards
- [ ] No calls to /scan endpoint
- [ ] Error state shows red banner with message
- [ ] Empty state shows message explaining no results
- [ ] Each idea card has a Run Tournament CTA