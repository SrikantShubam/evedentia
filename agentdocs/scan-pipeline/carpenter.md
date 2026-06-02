# Agent Task: CARPENTER — TournamentPanel + Dashboard Integration

## Role
You build the frame from blueprints. You reuse existing components. You don't recreate. You match the contract exactly.

## Pre-Read Contract (MUST read these files before touching any code)

Read these files IN ORDER:

1. `docs/frontend/app/tournament/[id]/page.tsx` — existing tournament board (what you're embedding inline)
2. `docs/frontend/components/SwimLanes.tsx` — component interface
3. `docs/frontend/components/IdeaCard.tsx` — component interface
4. `docs/frontend/components/BudgetMeter.tsx` — component interface
5. `docs/frontend/components/Diagnosis.tsx` — component interface
6. `docs/frontend/components/ReentryButton.tsx` — component interface
7. `docs/frontend/lib/tokens.ts` — T.* token values
8. `docs/frontend/app/page.tsx` — current dashboard (what you're modifying)

## What to Build

### 1. Create `docs/frontend/components/TournamentPanel.tsx`

**Props contract — must match EXACTLY:**

```typescript
interface TournamentPanelProps {
  opportunity: ScanOpportunity;
  keyword: string;
  onClose: () => void;
}

interface ScanOpportunity {
  opportunity_id?: string;
  title?: string;
  label?: string;
  hypothesis?: {
    headline?: string;
    wedge_statement?: string;
    hypothesis_type?: string;
  };
  verified_signals?: Array<{ source_url?: string }>;
  verdict?: "PURSUE" | "REFINE" | "KILL";
  final_score?: number;
  score?: number;
  gate_failures?: string[];
  cohort?: string;
  pain_hypothesis?: string;
  [key: string]: unknown;
}
```

**State machine:**

```
IDLE → LOADING → LIVE → COMPLETE
                 └→ ERROR (→ retry → LOADING)
```

**API calls:**
- `POST /validate` with `{ keyword, opportunity, player_id: "default" }` — on mount
- `EventSource /tournament/{id}/sse` — after receiving tournament_id

**Component structure (order):**
1. Header: ID badge, status, spend, close button
2. BudgetMeter (reuse from `@/components/BudgetMeter`)
3. SwimLanes (reuse from `@/components/SwimLanes`) with live gate data
4. Final Snapshot (only when COMPLETE): grid of IdeaCards
5. Diagnosis (reuse from `@/components/Diagnosis`, only when no PURSUE_SPIKE winner)

**Style rules (ZERO EXCEPTIONS):**
- NO hardcoded hex colors. Period.
- All cards: T.glassBg + T.glassBorder + backdropFilter: "blur(14px)"
- Labels: fontFamily: "var(--font-mono)"
- Accent: color: T.accent
- Background: T.bg

### 2. Modify `docs/frontend/app/page.tsx`

**Changes:**
1. Import `TournamentPanel` from `@/components/TournamentPanel`
2. Add state: `const [activeValidation, setActiveValidation] = useState<{opp, keyword} | null>(null)`
3. Results grid: replace "Run Tournament ▶" button with "Validate ▼" that calls `setActiveValidation`
4. Below results grid: conditionally render `<TournamentPanel ... />`
5. REMOVE: `useRouter` import
6. REMOVE: `handleRunTournament` function
7. REMOVE: any `router.push` or `window.location.href` for tournament navigation

## Tests to Pass

Checklist file: `tests/frontend/__checks__/tournament-panel-checklist.md` (39 items)
Checklist file: `tests/frontend/__checks__/dashboard-integration-checklist.md` (28 items)

Run before every commit:
```bash
cd C:\experiments\evidentia\main\docs\frontend; npx next build
```

## Commit

```bash
git add -A
git commit -m "feat: add inline TournamentPanel, integrate into dashboard, remove page navigation"
```

## PR

```bash
gh pr create --base feat/edge-tournament-phase0 --head feat/edge-tournament-phase0 --title "feat: inline TournamentPanel + dashboard integration" --body "Replaces separate /tournament/id page with inline TournamentPanel component. See tests/frontend/__checks__/ for verification checklists."
```

## Exit Gate (you're done when)

- [ ] `npx next build` compiles clean with zero errors
- [ ] TournamentPanel component exports with correct Props interface
- [ ] Dashboard imports TournamentPanel without errors
- [ ] "Validate ▼" button visible on opportunity cards
- [ ] "Run Tournament ▶" does NOT appear anywhere
- [ ] No `useRouter` or `window.location.href` for tournament nav
- [ ] Grep for `#[0-9a-fA-F]{6}` in TournamentPanel.tsx returns ZERO results
