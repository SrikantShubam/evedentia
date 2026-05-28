# Multi-Agent Architecture

## Team Structure

| # | Role | Agent | Responsibility |
|---|------|-------|----------------|
| 1 | **Orchestrator** | DeepSeek | Task DAG, assign coders, route PRs to reviewers, **merge**, maintain spec/plan |
| 2 | **Reviewer A** | DeepSeek | Review PRs (DeepSeek lens — catches different blind spots than Grok) |
| 3 | **Coder A** | Grok subagent | Implement tasks, push branches |
| 4 | **Coder B** | Grok subagent | Implement tasks, push branches |
| 5 | **Coder C** | Grok subagent | Implement tasks, push branches |
| 6 | **Reviewer B** | Grok subagent | Review PRs (Grok lens) |
| 7 | **Deep Critic** | Grok subagent (on-demand) | Spawned for high-risk merges only (engine, verdicts, re-entry) |
| 8 | **Tester** | Human | Manual testing, sign off |

**Count**: 5 steady Grok subagents + 1 floating + me (DeepSeek, dual-hat Orchestrator + Reviewer A) + human.

---

## Per-Cycle Pipeline

```
Orchestrator picks next task from plan (dependencies verified)
  → writes/updates task.md with precise scope
  → assigns to Coder

Coder implements in branch → runs tests → writes handoff-<task>.md
  → pushes branch + handoff

Orchestrator routes PR to Reviewers

Reviewer A (DeepSeek) approves with notes OR rejects
Reviewer B (Grok) approves with notes OR rejects

If EITHER rejects → sent back to Coder with notes
If BOTH approve → Orchestrator re-runs tests → merges

Tester manually verifies on main
```

**Deep Critic**: Orchestrator may spawn before merging any PR touching:
- `tournament/engine.py` — dispatch logic
- `tournament/verdict.py` — terminal verdict derivation
- `tournament/confidence.py` — scoring math
- `tournament/gates.py` — core gate functions
- `models.py` — data type changes

---

## Merge Rules

1. **Orchestrator is sole merger**. No one else pushes to main.
2. Required before merge:
   - Clean `handoff-<task>.md` from coder
   - Full test suite passes (Orchestrator re-runs)
   - Both reviewers approved
   - Deep critic sign-off (high-risk tasks only)
3. Merge method: `--ff-only` or squash with handoff summary in commit message.
4. Short-lived task branches only: `feat/<task-number>-<short-name>`.
5. Branch + worktree cleaned up after merge.

---

## How It Solves the 6 Problems

**1. Reviewer bottleneck**
Two reviewers (different models) handle 3 coders. Orchestrator routes, doesn't review (except as Reviewer A). No single point of delay — if one reviewer is busy, the other can pull.

**2. File collisions**
Coders work on branches + git worktrees. Orchestrator avoids assigning same-file tasks in parallel. Collisions impossible by construction.

**3. No CI**
Double test gate: coder runs before handoff, Orchestrator re-runs before merge. Deep Critic adds pre-merge check for high-risk changes.

**4. Grok amnesia**
Handoff packet on disk carries all context (files changed, test output, deviations). Each spawn reads spec + plan + prior handoffs from files, not memory.

**5. Task ordering**
Orchestrator only spawns a task when its dependencies are merged into main. Enforced by DAG in plan.md + manual gate.

**6. No branch protection**
Orchestrator is sole merger. Branch protection rules on GitHub enforced (require 1 review + passing status).

---

## Agent Coordination Rules

- Coders never review. Reviewers never code.
- Orchestrator never codes or reviews as primary — wears Reviewer A hat as second model perspective.
- Deep Critic is advisory only: flags issues, doesn't approve/reject.
- Tester has zero git rights. Reports via `test-report-*.md` artifacts.
- All handoffs go through files, not memory.
- If a PR sits unreviewed >30 min, Orchestrator rebalances reviewers.

---

## Related

- Product spec: `../spec.md`
- Implementation plan: `../plan.md`
- Tasks: `../tasks/`
