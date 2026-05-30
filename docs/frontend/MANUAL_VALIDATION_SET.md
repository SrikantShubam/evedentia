# Evidentia Frontend Manual Validation Set

Last updated: 2026-04-15  
Scope: `docs/frontend` Next.js app  
Purpose: manual regression and release validation for the Evidentia frontend

## Environment

- App directory: `docs/frontend`
- Run locally with:

```powershell
npm --prefix docs/frontend install
npm --prefix docs/frontend run dev
```

- Open: `http://localhost:3000`
- Recommended browsers:
  - Chrome latest
  - Edge latest
- Recommended viewports:
  - Desktop: `1440 x 900`
  - Mobile: `390 x 844`

## Personally Verified Baseline

The cases marked `Verified by me` were executed or directly inspected in this repo on 2026-04-15.

## Test Cases

| ID | Area | Verified by me |
|---|---|---|
| FE-001 | Build and boot | Yes |
| FE-002 | Global Roboto typography | Yes |
| FE-003 | Navigation to Try section | Yes |
| FE-004 | Source labels and HN expansion | Yes |
| FE-005 | Shortcut tooltip behavior | Yes |
| FE-006 | Source selection state | No |
| FE-007 | Domain input behavior | No |
| FE-008 | Semantic clustering and result rendering | No |
| FE-009 | Empty/error state handling | No |
| FE-010 | Hard-gate matrix overflow on mobile | No |
| FE-011 | No mojibake or corrupted copy | Yes |
| FE-012 | Keyboard and focus behavior | No |
| FE-013 | Synthesized hypothesis output contract | No |

## Detailed Cases

### FE-001: Build and boot

Precondition: dependencies installed

Steps:
1. Run `npm --prefix docs/frontend run build`
2. Run `npm --prefix docs/frontend run dev`
3. Open `http://localhost:3000`

Expected:
- Build completes without Next.js compile errors
- Local app loads without blank screen or hydration error

Evidence:
- Personally verified on 2026-04-15

### FE-002: Global Roboto typography

Precondition: app is running locally

Steps:
1. Open the homepage
2. Inspect hero heading, body copy, nav, buttons, form fields, and result cards
3. Inspect computed styles in DevTools for representative text and inputs

Expected:
- Primary UI text uses Roboto
- Inputs, buttons, and textareas inherit the same Roboto family
- No section falls back to a visibly different mono family

Evidence:
- Personally verified in source and build output on 2026-04-15

### FE-003: Navigation to Try section

Precondition: app is running locally

Steps:
1. Click the `try` navigation item

Expected:
- Page scrolls to the interactive input section
- The section is visible and ready for input

Evidence:
- Personally verified in source on 2026-04-15

### FE-004: Source labels and HN expansion

Precondition: app is running locally

Steps:
1. Locate the pipeline overview section
2. Locate the source selector in the Try section

Expected:
- `hn` is not shown as unexplained shorthand
- Users see `Hacker News (HN)` anywhere the source label is presented in full

Evidence:
- Personally verified in source on 2026-04-15

### FE-005: Shortcut tooltip behavior

Precondition: desktop browser

Steps:
1. Hover the `hn` source chip or any UI badge that shows a source shortcut
2. Repeat for any other source shortcut shown in results

Expected:
- Tooltip or native title explains the shortcut
- For HN, tooltip reads `hn = Hacker News (HN)`

Evidence:
- Personally verified in source on 2026-04-15

### FE-006: Source selection state

Precondition: app is running locally

Steps:
1. Toggle `Hacker News (HN)`, `Reddit`, and `GitHub`
2. Select one source only
3. Select multiple sources
4. Deselect a source

Expected:
- Selected state is visually distinct
- Multi-select works consistently
- Selection updates without UI breakage

### FE-007: Domain input behavior

Precondition: app is running locally

Steps:
1. Enter a domain keyword such as `invoicing`
2. Clear the field
3. Enter a long phrase

Expected:
- Input accepts text without layout shift
- Placeholder and helper copy remain readable
- Empty state is handled cleanly

### FE-008: Semantic clustering and result rendering

Precondition: frontend is connected to the expected backend or mock response path

Steps:
1. Enter a domain
2. Select one or more sources
3. Trigger the scan action

Expected:
- Loading state is visible while request is in flight
- Returned results are grouped into semantic clusters
- Each visible card reflects a synthesized hypothesis rather than a raw hit list
- Keep / revise / kill language is visible somewhere in the validation path
- No duplicate or broken cards appear

### FE-009: Empty/error state handling

Precondition: app is running locally

Steps:
1. Trigger a scan with invalid or unavailable backend conditions
2. Trigger a scan that returns no results

Expected:
- Error state is readable and non-destructive
- Empty state explains that no results were found
- Existing layout remains stable

### FE-010: Hard-gate matrix overflow on mobile

Precondition: mobile viewport `390 x 844`

Steps:
1. Open the scoring and hard-gate section
2. Scroll horizontally if needed

Expected:
- Table remains readable on mobile
- Content is not clipped off-screen
- Horizontal overflow is contained within its panel

### FE-013: Synthesized hypothesis output contract

Precondition: frontend is running locally with a result that reaches the opportunity display path

Steps:
1. Trigger a scan that returns at least one cluster
2. Open the first visible result card
3. Trigger spec generation or inspect the result summary panel

Expected:
- The output names a cluster or cluster summary, not just a raw source row
- The result body presents a synthesized hypothesis
- The validation posture is explicit through keep / revise / kill language or equivalent state text
- The spec handoff is traceable back to the cluster evidence

### FE-011: No mojibake or corrupted copy

Precondition: app is running locally

Steps:
1. Review hero, pipeline, scoring, Try section, result cards, and footer copy
2. Check chevrons, separators, and badges

Expected:
- No corrupted glyphs or replacement characters appear
- UI copy is readable and consistent

Evidence:
- Personally verified in source on 2026-04-15

### FE-012: Keyboard and focus behavior

Precondition: desktop browser

Steps:
1. Use `Tab` to move through nav, inputs, source chips, and action buttons
2. Use `Enter` and `Space` where applicable

Expected:
- Focus order is logical
- Interactive controls are reachable by keyboard
- Focus remains visible during interaction

## Personally Verified Commands

```powershell
npm --prefix docs/frontend run build
```

```powershell
Select-String -Path 'docs/frontend/app/layout.tsx' -Pattern 'Roboto|--font-roboto|className'
Select-String -Path 'docs/frontend/app/globals.css' -Pattern '--font-sans: var\(--font-roboto\)|--font-mono: var\(--font-roboto\)|button,|input,|textarea,|select'
Select-String -Path 'docs/frontend/app/page.tsx' -Pattern 'Hacker News \(HN\)|sourceShortcutTitle|\["pipeline", "scoring", "try", "cli"\]|function TryItSection\(|<TryItSection \/>|title=\{sourceShortcutTitle'
```
