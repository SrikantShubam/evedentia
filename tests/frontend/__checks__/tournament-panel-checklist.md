# TournamentPanel — Component Test Checklist

Reviewer: check each item manually in the browser. Mark `[x]` when verified.

---

## Render States

- [ ] **IDLE**: Component mounts, shows nothing or empty glass container
- [ ] **LOADING**: POST /validate is called. Loading spinner visible inside glass card. Header shows "Creating tournament..."
- [ ] **LIVE**: SSE connected. SwimLanes visible with gate columns. "LIVE" badge in header.
- [ ] **LIVE**: Event count increments in header with each gate event
- [ ] **LIVE**: Spend counter ($X.XX) updates with each gate event
- [ ] **COMPLETE**: "done" SSE received. Status badge changes to "COMPLETE".
- [ ] **COMPLETE**: Final Snapshot grid visible with IdeaCards
- [ ] **COMPLETE**: Diagnosis visible when no PURSUE_SPIKE winner exists
- [ ] **COMPLETE**: No Diagnosis rendered when PURSUE_SPIKE winner exists
- [ ] **ERROR**: SSE onerror fires. Error card with message + retry button visible.
- [ ] **ERROR**: Retry button re-establishes SSE connection from scratch

## Reusability (use existing components, don't recreate)

- [ ] Uses `SwimLanes` component (not custom lane HTML)
- [ ] Uses `BudgetMeter` component
- [ ] Uses `Diagnosis` component
- [ ] Uses `IdeaCard` component for Final Snapshot
- [ ] Uses `ReentryButton` for INSUFFICIENT_EVIDENCE ideas
- [ ] Uses `T` from `@/lib/tokens` for ALL colors

## Style Audit

- [ ] Run: `grep -rn '#[0-9a-fA-F]\{6\}' docs/frontend/components/TournamentPanel.tsx` — ZERO results
- [ ] Every glass card has `backdropFilter: "blur(...)"`
- [ ] All labels/badges use `fontFamily: "var(--font-mono)"`
- [ ] Accent elements use `T.accent` (`#e2ff5d`)
- [ ] Background uses `T.bg` (`#0a0a0a`)
- [ ] PASS status uses `T.success` (green)
- [ ] FAIL status uses `T.danger` (red)
- [ ] PENDING/WARNING status uses `T.warning` (amber)

## Edge Cases

- [ ] 0 ideas in tournament → empty state message ("No ideas in this tournament")
- [ ] All ideas KILLED → Diagnosis component renders
- [ ] All ideas KILLED → No Final Snapshot (no survivors to show)
- [ ] Mixed verdicts → Final Snapshot shows only non-KILL ideas
- [ ] Rapid SSE events → no visual flickering or layout shift
- [ ] Click close button (X) → panel disappears, SSE connection closed
- [ ] Click close → state cleaned up (no memory leak from EventSource)
- [ ] Open same opportunity twice → different tournament IDs, fresh SSE
- [ ] Open different opportunity → old panel replaced, new tournament starts
- [ ] Very long opportunity title → truncated with ellipsis in header
- [ ] Opportunity with missing optional fields → defaults applied (no crash)
- [ ] Network error during POST /validate → error state shown
