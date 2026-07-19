# Feature: Homepage Redesign — Dashboard Cockpit

## Status
- [x] Draft
- [x] Approved
- [ ] In Progress
- [ ] Complete

## Overview
Replace the old 70KB marketing/education homepage with a Stitch-inspired Dashboard Cockpit. The old content (pipeline stages, scoring model, proof levels, CLI reference) moves to `/about`.

## Design Reference
Two Stitch screens were generated in project `9504163294532841467`:
- **Evidentia Dashboard Home** (screen `67ce9b33`) — sidebar nav, scan section, results grid, validation engine
- **Evidentia Homepage** (screen `8fc5eacf`) — landing hero, try-it, how-it-works

The new `app/page.tsx` follows the **Dashboard Home** design.

## Layout
- **Left sidebar** (fixed 240px): glassmorphism card, logo, nav items with Material icons, "Create New Idea" button
- **Main area**: top bar (search, notifications, avatar, Get Started + Pro Plan), scrollable content sections

## Content Sections
1. **Hero banner**: "Evidentia — Find ideas worth building..." + "Get Started →"
2. **Try It / Scan**: keyword input + HN/Reddit/GitHub source pill toggles + "Scan →" button
3. **Active Tournament / Results**: bento grid of idea cards with label, cohort, pain hypothesis, kill condition badge, "Run Tournament ▶" button, optional traction score
4. **The Validation Engine**: 6 interactive stage cards (Scan, Verify, Score, Spec, Build, Ship) with icons + descriptions
5. **Footer**: Methodology, Pricing, Privacy, API links

## Old Content Migration
Move to `app/about/page.tsx`: pipeline details, scoring model, proof levels, CLI reference, old Try It section.

## API Wires
- Search + Scan button → `POST /harvest` + `POST /generate`
- Run Tournament → `POST /tournament` → navigate to `/tournament/[id]`
- Sidebar nav → links to existing routes

## Files
- `app/page.tsx` — Rewrite as Dashboard Home
- `app/about/page.tsx` — Create with old marketing content
