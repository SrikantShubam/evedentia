# Task: Old Content Migration (app/about/page.tsx)

## Agent
C

## Scope
Move the old marketing/education content from the current `app/page.tsx` to a new `app/about/page.tsx`.

## Sections to Migrate
From the current `app/page.tsx`, extract these sections:
1. Pipeline Stages (the expandable cards with step 01-07)
2. Proof Levels (L1/L2/L3 cards)
3. Scoring Model (Hard Gates table + Heuristic Weights bars)
4. CLI Reference (code blocks with copy buttons)
5. Old Try It section (scan → spec flow)

## Design
- Same glassmorphism styling as the dashboard
- Nav back to Home
- Sections use glass cards, same tokens

## Files
- CREATE: `app/about/page.tsx`
- Update layout/nav to include link to `/about`
