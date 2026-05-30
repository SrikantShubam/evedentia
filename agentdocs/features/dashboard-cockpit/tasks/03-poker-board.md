# Task: Poker Board

## Agent
Subagent C

## Requirements
FR-4: /tournament/[id] with swim lanes per gate, SSE streaming
FR-5: IdeaCard component

## Spec Reference
- spec.md FR-4, FR-5
- Current board at docs/frontend/app/tournament/[id]/page.tsx shows flat cards

## What to Build
Replace the current poker board with:
1. Swim lanes layout: columns per gate name (from the profile), cards sit in their current gate column
2. IdeaCard component per idea showing:
   - Idea label + cohort
   - Current gate name (the last gate with status=COMPLETED)
   - Confidence score so far (displayed as progress bar or badge)
   - Top kill risk (first FAIL gate, or lowest-confidence PASS gate)
   - Strongest verbatim quote (from evidence_ids)
   - Running LLM cost
3. Card states:
   - PASS: green border, moves to next column
   - FAIL: red border, fades out (stays in current column)
   - SKIPPED: yellow border, shimmer animation
   - PENDING: dimmed, waiting for SSE event
4. SSE stream: connect on mount, parse gate events, update card positions in real-time
5. Auto-reconnect on SSE connection drop
6. When tournament completes, show final snapshot (existing behavior)
7. Navigation links: View Memo, View Evidence Trail per idea
8. Empty/error state for invalid tournament ID

## API Endpoints
- GET /tournament/{id} -> tournament payload
- GET /tournament/{id}/sse -> SSE event stream

## Files to Edit
- docs/frontend/app/tournament/[id]/page.tsx
- Consider creating a components/ directory for IdeaCard

## Acceptance
- [ ] Swim lanes show gates as columns
- [ ] Cards move right on PASS, fade on FAIL
- [ ] SSE stream updates board live
- [ ] Auto-reconnect on drop
- [ ] Invalid tournament ID shows error message