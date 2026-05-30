# Dashboard Cockpit UI Design

## Design System

### Glassmorphism Tokens

- Glass card: background rgba(255,255,255,0.03), border 1px solid rgba(255,255,255,0.08), backdrop-filter: blur(16px)
- Glass hover: background rgba(255,255,255,0.06), border rgba(255,255,255,0.12)
- Glass accent: background rgba(226,255,93,0.06), border rgba(226,255,93,0.15)
- Surface: #0a0a0a bg with subtle radial gradient overlay
- Text: #f0f0f0 primary, #888 secondary via rgba(255,255,255,0.5)
- Glow: box-shadow 0 0 20px rgba(226,255,93,0.15) on CTA hover

### Bento Box Layout

- Page sections: asymmetric CSS grid with varied card sizes
- Homepage results: 2x2 bento with one featured card 2x1
- Poker board: gate columns as vertical bento slices
- Memo: document-style bento with for/against side by side
- Card size variants: full (2x1), half (1x1), double-height (1x2)

### Modern UI/UX Principles

- Large display headings (clamp 24-36px) with tight letter-spacing -0.025em
- Monospace 12px for data labels, sans-serif for body
- Clear CTA hierarchy: primary (glass+accent), secondary (ghost), tertiary (text only)
- Smooth transitions: 0.3s cubic-bezier(0.4, 0, 0.2, 1)
- Subtle micro-interactions: scale 1.02 on card hover, glow on CTA
- Whitespace: generous padding (24-32px), clear visual breathing room

## Page Designs (Updated)

### 1. Homepage Try It Section
- Bent search bar: glass card with input + CTA button side by side
- Source chips: pill-shaped glass toggles, accent border when active
- Results: bento grid (2 columns, featured idea gets 2x1 card)
- Each idea card: glass bg, left accent border colored by status
- CTA Run Tournament: glass-accent button at card bottom

### 2. Tournament New (Seed Form)
- Glass card form container with inner sections
- Anchor picker, harvest preview, generate: horizontal bento strip
- Idea JSON textarea: inset glass (bg rgba(0,0,0,0.3))
- Submit: full-width glass-accent CTA

### 3. Poker Board
- Header stats: bento row of glass badges (events, spend, memo link)
- BudgetMeter: 3 glass progress bars with glow fill
- Swim lanes: scrollable glass columns with frosted header
- IdeaCard: glass card, left 3px border color (green/red/yellow), glow shadow on PASS
- Diagnosis: 2x2 bento grid (kill histogram, what-would-flip, stats)

### 4. Decision Memo
- Document-style with glassmorphism cards
- Winner: glass-accent card with subtle glow
- RealitySpikeCard: glass-amber card with glowing provenance badge
- Provenance badge: glass pill with amber text, backdrop-filter

### 5. Evidence Trail
- Chronological bento: each gate as a glass card
- Status badges: glass pills (green/red/yellow)
- Quotes: glass inset blockquote style

## Component CSS Snippets

Glass card:
  background: rgba(255,255,255,0.03)
  border: 1px solid rgba(255,255,255,0.08)
  border-radius: 12px
  backdrop-filter: blur(16px)
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)

Glass accent (CTA):
  background: rgba(226,255,93,0.12)
  border: 1px solid rgba(226,255,93,0.25)
  color: #e2ff5d
  box-shadow: 0 0 20px rgba(226,255,93,0.1)

Glass pass (PASS card):
  border-left: 3px solid #4ade80
  box-shadow: 0 0 15px rgba(74,222,128,0.1)

Bento grid:
  display: grid
  grid-template-columns: 2fr 1fr
  gap: 16px
  .featured: grid-column: 1 / -1

## Animations (Updated)

- Card hover: transform scale(1.02), border-color brightens
- CTA hover: glow intensifies (box-shadow spread increase)
- PASS slide: translateX with glass blur transition
- FAIL fade: opacity + blur increase (glass shatter effect)
- SKIPPED shimmer: glass refraction animation (backdrop-filter shift)
- Page load: glass cards fade in with blur-to-clear transition (0.5s)