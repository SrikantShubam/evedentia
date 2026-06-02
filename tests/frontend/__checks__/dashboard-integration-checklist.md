# Dashboard Integration — Test Checklist

Reviewer: check each item manually. Mark `[x]` when verified.

---

## Scan Results

- [ ] "Web" source toggle pill visible alongside HN, Reddit, GitHub
- [ ] "Web" toggle starts as active (blue/accent color)
- [ ] Clicking "Web" toggles it on/off
- [ ] Only "Web" selected → `activeSources` = `["web_search"]`
- [ ] All sources off → warning "Select at least one source" shown
- [ ] Scan with "Web" source → POST /scan called with `sources: ["web_search"]`
- [ ] Results appear as scored opportunity cards
- [ ] Verdict badge visible (PURSUE green / REFINE amber / KILL red)
- [ ] Score percentage visible on verdict badge
- [ ] Gate failure tags visible as red/amber chips

## Tournament Buttons

- [ ] "Validate ▼" button on each opportunity card (NOT "Run Tournament ▶")
- [ ] "Run Tournament ▶" text does NOT appear anywhere on the dashboard
- [ ] Clicking "Validate ▼" opens TournamentPanel below the results grid
- [ ] Scan results remain visible while TournamentPanel is open
- [ ] Clicking "Validate ▼" on a different opportunity replaces the active panel

## Layout Integrity

- [ ] Sidebar (logo, nav, "Create New Idea") unaffected
- [ ] Top bar (search, notifications, avatar) unaffected
- [ ] Scan section unaffected
- [ ] Results grid unaffected
- [ ] Validation Engine section unaffected
- [ ] Footer unaffected
- [ ] TournamentPanel appears AFTER results grid, BEFORE Validation Engine

## Build Check

- [ ] `npx next build` compiles clean (0 errors, 0 warnings)
- [ ] No `useRouter` import in `app/page.tsx`
- [ ] No `handleRunTournament` function in `app/page.tsx`
- [ ] No `window.location.href` for tournament navigation
- [ ] `TournamentPanel` imported from `@/components/TournamentPanel`
- [ ] All component props match their TypeScript interfaces

## Browser Console

- [ ] No red errors on page load
- [ ] No `EventSource` connection errors (handled gracefully)
- [ ] No `unhandled rejection` in console
