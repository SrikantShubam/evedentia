# Evidentia Dashboard Cockpit — UI Design Spec

**Version:** 0.2  
**Date:** 2026  
**Theme:** Dark, startup-grade, evidence-first  
**Accent:** #e2ff5d (lime)  
**Stack:** Next.js App Router, React, motion/react (framer-motion), Tailwind or custom styles matching existing homepage

## 1. Design Tokens (Extend Existing Homepage)

Use the same tokens as `app/page.tsx`:

```ts
const T = {
  bg: "#0a0a0a",
  surface: "#111111",
  surfaceHover: "#161616",
  border: "#1f1f1f",
  accent: "#e2ff5d",
  accentDim: "rgba(226,255,93,0.08)",
  text: "#f0f0f0",
  muted: "#666666",
  mutedLight: "#888888",
  success: "#22c55e",   // PASS green
  danger: "#ef4444",    // FAIL red
  warning: "#f59e0b",   // HOLD / caution
};
```

**Typography**
- Headings / prose: system sans-serif (Inter or similar via `var(--font-sans)`)
- Data, IDs, code, metrics: `var(--font-mono)` (already used in homepage)
- Scale: 11px (labels), 13px (body data), 15-16px (primary), 24-36px (page titles), 40-72px (hero)

**Spacing Scale** (consistent 4px grid)
- 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80px

**Borders & Radius**
- Subtle: `1px solid ${T.border}`
- Cards: `border-radius: 8px` or `10px`
- Buttons / Pills: `6px`
- Focus: 2px outline with accent

**Shadows**
- Subtle lift: `0 4px 12px rgba(0,0,0,0.4)`
- Accent glow: `0 0 0 1px ${T.accent}30`

## 2. Core Components

### 2.1 IdeaCard (Poker Board + Memo + Evidence Trail)

**Purpose:** The atomic unit of the cockpit. Used in swimlanes, lists, and drill-downs.

**Props (TypeScript):**
```ts
interface IdeaCardProps {
  idea: {
    id: string;
    label: string;
    confidence?: number;      // 0-1
    kill_risk?: number;       // 0-1
    quote?: string;
    source_url?: string;
    cost_usd?: number;
    status?: 'PENDING' | 'PASS' | 'FAIL' | 'HOLD';
  };
  variant?: 'board' | 'memo' | 'trail' | 'compact';
  onPass?: () => void;
  onFail?: () => void;
  showActions?: boolean;
}
```

**Layout (Board variant - primary):**
- Card: 320-380px wide, min-height 140px
- Top row: `label` (bold, 15px) + status pill (right)
- Middle: Horizontal metrics row
  - Confidence: small bar + `87%` (monospace)
  - Kill Risk: red-tinted pill or bar
  - Cost: `$0.041` (monospace, right aligned)
- Quote block: 2-3 lines, italic or normal, with source link (monospace url, truncated)
- Bottom: subtle "Evidence: 7 signals" count if available

**Visual Treatment:**
- Background: T.surface
- Border: T.border (on hover or when selected: T.accent 40%)
- On PASS: border becomes success green, subtle green glow
- On FAIL: border danger, desaturate / opacity 0.6 + strike-through option
- Hover: translateY(-2px), box-shadow lift, border accent

**Animations (motion/react):**
- Mount: fade + slight y slide
- Status change: scale(0.98) → 1.0 + color transition 200ms
- Drag (future): use @hello-pangea/dnd or framer drag with spring

**Code Sketch (ready to drop in):**
(See full polished version generated via 21st Magic below in section 6)

### 2.2 BudgetMeter

**Location:** Top of Poker Board

**Layout:** Horizontal or 3-column grid on wide screens
- LLM Calls: `142 / 500` + progress bar (lime)
- Search Calls: `89 / 300` + bar
- Spend: `$18.42 / $75.00` + warning when >70%

**Design:**
- Compact cards or single bar with three segments
- Monospace numbers
- Color: accent for progress, warning when thresholds crossed
- Tooltip on hover explaining what counts toward budget

### 2.3 Swimlane (Gate Column)

**Poker Board only.**

- Header: Gate name + "PASS count / total"
- Body: vertical stack of IdeaCards (sortable or animated reorder)
- Drop zone visual when dragging
- Empty state: "No ideas reached this gate yet"

**Animation:** Cards "slide right" on PASS with a green flash trail (use AnimatePresence + layoutId for magic)

### 2.4 RealitySpikeCard (Decision Memo)

**Special provenance badge:**
```tsx
<Badge variant="spike">LLM_GENERATED_TACTICAL_COPY</Badge>
```
- Yellow/amber treatment or distinct border
- "This section was LLM-generated from the evidence trail. Human review required."

### 2.5 Other Atoms
- `GatePill`, `ConfidenceBar`, `CostTag`, `SourceLink`, `PrimaryButton` (lime fill on dark), `SecondaryButton` (outline)

## 3. Page-by-Page Layout Specs

### 3.1 Homepage (/) — Already excellent
- Keep the existing marketing + "Try It" section.
- Minor polish: Make the results "idea cards" use the new `IdeaCard` component (compact variant).
- Add subtle "View in Dashboard" links once a tournament is created.

### 3.2 Player Profile (/player)

**Layout:**
- Centered narrow container (max 720px)
- Header: "Player Profile" + "Load from API" button
- Large monospace JSON editor (textarea or better: use a lightweight JSON editor like `react-json-view` or CodeMirror if added)
- Two big CTAs side-by-side at bottom:
  - **Save Profile** (primary lime)
  - **Validate & Test Gates** (secondary)
- Right sidebar (or collapsible): "Gate Profiles" reference cards (consumer_app, b2b_workflow, etc.)

**Feel:** Minimal, functional, "power user" tool. High contrast for JSON readability.

### 3.3 Tournament New (/tournament/new)

**Primary CTA:** Big "Run Tournament" button (disabled until valid JSON + player)

**Layout (two-column on desktop, stacked mobile):**
- Left (60%): 
  - Anchor picker (nice dropdown or searchable select with current anchors)
  - Harvest Preview card: "47 signals harvested" + breakdown by source (small pills)
  - Large "Generate Ideas" button (calls backend to synthesize)
  - Editable JSON textarea (taller, with syntax highlight if possible)
- Right (40%):
  - Gate Profile Override: beautiful segmented control or dropdown with descriptions
  - "Inferred from ideas: consumer_app (0.82)"
  - Budget estimate preview (if API supports)
  - "What happens next" explainer box

**Polish touches:**
- Live JSON validation with red/green border
- "Seed with sample ideas" link
- Consistent use of SectionLabel from homepage

### 3.4 Poker Board (/tournament/[id]) — The Hero View

**Overall:**
- Full-bleed dark background
- Top sticky header: Tournament ID (monospace) + "Live" pulsing dot + BudgetMeter
- Main area: Horizontal swimlanes (4-7 gates depending on profile)
  - Use CSS Grid or horizontal scroll + snap for mobile
- Each lane has a header with gate name + pass/fail counters
- Cards animate rightward when they PASS a gate (smooth layout transition)
- Cards that FAIL get a red flash then fade to 40% opacity and move to a "Failed" collapsed section or stay in lane with FAIL styling

**Live Feel (SSE):**
- New gate events cause cards to highlight briefly
- Budget numbers update with count-up animation
- Connection status pill in header ("Connected" / "Reconnecting")

**Bottom Section:**
- "Zero-Winner Diagnosis" (collapsible, important)
  - List of ideas that died + the exact gate + reason
  - "Most common kill reason: data_feasibility"

**Interactions:**
- Click card → opens side drawer or navigates to `/ideas/[id]`
- Keyboard: `p` = PASS focused, `f` = FAIL, `esc` = clear

### 3.5 Decision Memo (/tournament/[id]/memo)

**Document feel (printable):**

- Centered content, max ~800px wide (like a Google Doc or Notion page)
- Top: "Decision Memo" + tournament ID + date + "Export PDF" button
- Winner section: Large IdeaCard (memo variant) + "Selected" badge
- Two columns below:
  - **Arguments For** (green tint)
  - **Arguments Against** (red tint)
- Missing Evidence Checklist (checkboxes, some pre-filled from backend)
- RealitySpikeCard(s) with clear "LLM_GENERATED..." provenance
- Footer: "Human sign-off required before build"

**Typography:** Slightly larger body text (15px), generous line-height for readability.

**Print CSS:** Hide nav, make it look like a formal memo when printed.

### 3.6 Evidence Trail (/ideas/[id])

**Drill-down view:**

- Breadcrumb: Tournament > Idea Label
- Header with the IdeaCard (large)
- Timeline / vertical list of every gate the idea passed or failed
  - For each gate: timestamp, outcome badge, confidence delta, quote(s) used, cost for that step
- Full quote provenance list (clickable sources)
- Posterior probability chart (simple SVG or Recharts bar if added)
- Cost breakdown table

**Feel:** Forensic, trustworthy, "every number has a source".

## 4. Animation & Micro-interaction Guidance

- Use `motion/react` everywhere (already dependency).
- Card movements in board: `layout` prop + `AnimatePresence`.
- Status changes: spring scale + color flash.
- Budget updates: count-up using `framer-motion` `useMotionValue`.
- Page transitions: subtle fade (not too long).
- Avoid heavy parallax on dashboard pages (keep focus on data).

## 5. Implementation Notes

- Keep all pages using the same `T` token object (move to `lib/tokens.ts`).
- Create `components/` folder: `IdeaCard.tsx`, `BudgetMeter.tsx`, `Swimlane.tsx`, `SectionLabel.tsx` (reuse from homepage).
- For the Poker Board, consider lightweight state management (Zustand or just React) for the live event stream.
- Add shadcn/ui only if needed for complex forms (the current homepage avoids heavy component libs — prefer custom for brand consistency).

## 6. Generated Components via 21st Magic (Recommended Starting Points)

After running the component builder for "kanban card dashboard", integrate the following high-quality snippet (example of what the tool returns — adapt colors):

```tsx
// components/IdeaCard.tsx (example polished output)
'use client';

import { motion } from 'motion/react';

export function IdeaCard({ idea, onPass, onFail, variant = 'board' }: IdeaCardProps) {
  const isBoard = variant === 'board';
  
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="rounded-xl border p-4 transition-all"
      style={{
        background: '#111111',
        borderColor: idea.status === 'PASS' ? '#22c55e' : idea.status === 'FAIL' ? '#ef4444' : '#1f1f1f',
      }}
    >
      {/* Full implementation with confidence bar, quote, cost, actions */}
      {/* ... */}
    </motion.div>
  );
}
```

**Next Steps for Engineer:**
1. Copy the tokens and components into `components/`
2. Replace the inline-style pages one by one starting with `/tournament/new` and the Poker Board.
3. Run the magic refiner tool on the new components once they are in the codebase for final polish.

---

**This spec turns the current functional dashboard into a world-class, investor-ready cockpit that matches the quality of the marketing homepage.**

**Priority order for implementation:**
1. IdeaCard (used everywhere)
2. BudgetMeter + Poker Board swimlanes
3. Tournament New page polish
4. Decision Memo document treatment
5. Evidence Trail timeline

*End of spec*
