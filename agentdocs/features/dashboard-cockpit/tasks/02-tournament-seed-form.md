# Task: Tournament Seed Form

## Agent
Subagent B

## Requirements
FR-3: /tournament/new with anchor picker, harvest preview, idea editor, profile override

## Spec Reference
- spec.md FR-3
- Current page at docs/frontend/app/tournament/new/page.tsx only has raw JSON paste

## What to Build
Replace the current /tournament/new page with:
1. Anchor picker dropdown - hardcode anchors from known list:
   ['onboarding-tools', 'invoice-reconciliation', 'dev-tooling', 'crm-for-agencies']
   (load_all_anchors() would be server-side; for now use a hardcoded list)
2. Harvest Preview toggle: when anchor selected, show a Preview button that calls POST /harvest and displays signal count + sample
3. Generate Ideas button: calls POST /generate with selected anchor, fills idea JSON editor with results
4. Idea JSON editor: editable textarea (keep existing pattern), with validation that JSON parses to valid Idea[]
5. Gate profile override: dropdown with consumer_app, b2b_workflow, browser_extension, agency_service
6. Player ID input (keep existing)
7. Submit button -> POST /tournament -> navigate to /tournament/[id] on success
8. Loading states for each async action

## API Endpoints
- POST /harvest: {anchor_slug, limit=20, dry_run=false} -> {candidates: [...], discard_log: [...]}
- POST /generate: {anchor_slug, count=10} -> {ideas: [...]}
- POST /tournament: {tournament_id, player_id, ideas, gate_profile} -> tournament result

## Files to Edit
- docs/frontend/app/tournament/new/page.tsx

## Acceptance
- [ ] Anchor picker lists available anchors
- [ ] Harvest preview shows signal count
- [ ] Generate fills the idea editor
- [ ] Profile override dropdown works
- [ ] Submit creates tournament and navigates to board