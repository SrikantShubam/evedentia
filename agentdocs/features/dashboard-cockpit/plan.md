# Plan: Dashboard Cockpit

## Status
- [x] Draft
- [x] Review
- [x] Approved
- [ ] In Progress
- [ ] Complete

## Design System
Glassmorphism + bento boxes + modern startup UX
See notes/design.md for full design tokens and CSS snippets

## Agent Roster

| Role | Who | Responsibility |
|---|---|---|
| Orchestrator | Me | Coordinate phases, write spec/plan, spawn agents, review, merge |
| Designer | Grok + Stitch MCP | Generate glassmorphism+bento UI design via Google Stitch MCP |
| Subagent A | Grok | Repair homepage Try It section - wire to real API endpoints |
| Subagent B | Grok | Redesign /tournament/new with anchor picker, profile picker |
| Subagent C | Grok | Redesign /tournament/[id] poker board with swim lanes + IdeaCards |
| Subagent D | Grok | Build BudgetMeter + Diagnosis components |
| Subagent E | Grok | Build ReentryButton + polish memo page with RealitySpikeCard |
| Reviewer | Me | Review all commits after subagents, create PRs for issues |
| Fix Agent | Grok | Fix issues identified in review, PR -> fix -> re-review -> merge |

## Execution Phases

### Phase 0: Setup (Done)
- Feature directory: agentdocs/features/dashboard-cockpit/
- spec.md, plan.md, tasks/01-05, notes/design.md created
- API :8000 and frontend :3000 running

### Phase 1: Design (Next - Grok + Google Stitch MCP)
- Prompt Grok with Stitch MCP to generate glassmorphism startup UI
- Apply glassmorphism tokens (backdrop-filter, rgba borders, glow) to frontend
- Convert card layouts to bento box grids

### Phase 2: Implementation (Subagents A-E in parallel)

#### A: Homepage -> /harvest + /generate (FR-1)
#### B: Tournament seed form (FR-3)
#### C: Poker board swim lanes + IdeaCards (FR-4, FR-5)
#### D: BudgetMeter + Diagnosis (FR-6, FR-9)
#### E: ReentryButton + memo RealitySpikeCard (FR-7, FR-10)

### Phase 3: Review
- Review each commit against spec
- Issues -> PR -> Grok fixes -> re-review -> merge

### Phase 4: Verify
- Full pipeline smoke test: invoice reconciliation end-to-end

## Task Mapping

| Task | File | Agent | Reqs |
|---|---|---|---|
| Homepage | tasks/01-homepage-try-it.md | A | FR-1 |
| Seed Form | tasks/02-tournament-seed-form.md | B | FR-3 |
| Poker Board | tasks/03-poker-board.md | C | FR-4, FR-5 |
| BudgetMeter | tasks/04-budget-meter-diagnosis.md | D | FR-6, FR-9 |
| Reentry | tasks/05-reentry-memo.md | E | FR-7, FR-10 |
| Design | notes/design.md | Designer | All NFRs |