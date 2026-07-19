# Task: Dashboard Homepage (app/page.tsx)

## Agent
AB

## Scope
Rewrite `app/page.tsx` as the Stitch-inspired Dashboard Home with full glassmorphism.

## Sections to Build

### 1. Sidebar (fixed left, 240px)
- Glass card: bg T.glassBg, border, backdrop-filter blur
- Logo "evidentia" at top
- Nav items with Material Icons (use text fallbacks): Dashboard, Tournaments, Insights, Archive, Settings
- Active state: accent bg for current route
- Bottom: "Create New Idea" accent CTA button
- Sidebar sits outside scroll, fixed on page

### 2. Top Bar
- Search input (glass, left icon)
- Notifications bell icon, Account avatar circle
- "Get Started" accent CTA
- "Pro Plan" badge (glass pill with accent text)

### 3. Hero Banner
- "Evidentia" display heading
- "Find ideas worth building by scanning signals across the digital landscape with AI-driven validation."
- "Get Started →" CTA button (glass-accent, with glow shadow)

### 4. Scan Section
- Keyword text input (glass, full width within section)
- Source toggles: Hacker News (HN), Reddit, GitHub — as pill-shaped glass chips, accent border when active
- "Scan →" button (accent CTA)

### 5. Active Tournament / Results Grid
- Bento grid of idea cards (2 columns on desktop)
- Each card: label, cohort tag, pain hypothesis text, **kill condition** badge (amber glass, format "KILL IF: <desc>"), "Run Tournament ▶" button
- Last card: "More Signals Needed" — glass CTA card to expand search
- If no results yet, show the "More Signals Needed" placeholder

### 6. The Validation Engine
- 6 stage cards in a row/grid: Scan, Verify, Score, Spec, Build, Ship
- Each card: icon, stage name, short description
- Glass cards, accent border on hover

### 7. Footer
- "Evidentia" brand
- Links: Methodology, Pricing, Privacy, API
- "© 2024 Building Worthwhile Ideas."

## Wiring
- Scan button: `POST ${API}/harvest` with anchor_slug from input, then `POST ${API}/generate` → populate results grid
- Run Tournament: `POST ${API}/tournament` with generated idea → `window.location.href = /tournament/[id]`
- Sidebar links to existing routes

## Design Tokens
Use only from lib/tokens.ts: T.bg, T.surface, T.glassBg, T.glassBorder, T.accent, T.accentDim, T.text, T.muted, T.mutedLight, T.border

## Files
- MODIFY: `app/page.tsx` (full rewrite, ~500-700 lines)

## Existing Components to Reuse
- None from components/ — this is a distinct page layout
