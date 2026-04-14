# AGENTS.md

This file is the operating index for agentic work in this repo.

Read this first when starting Codex App or any other coding agent in `main/`.

---

## 1. Project Summary

Evidentia is an internal demand-to-product pipeline.

The intended workflow is:

```text
scan -> verify -> score -> spec -> build -> ship -> track
```

The project is **pre-implementation**. The current repo contains planning and operating documents, not a built system.

### Current truth

- The evidence-engine concepts are grounded in prior `codex/` and `kimi/` markdown.
- The corrected project direction is in `main/final_pivot.md`.
- The staged execution plan is in `main/IMPLEMENTATION_PLAN.md`.
- The corrected comparison of prior docs is in `main/COMPARATIVE_ANALYSIS.md`.

### Important boundary

Do not treat build/ship/track as proven capabilities. They are planned phases.

The only grounded foundation from the broader markdown corpus is the evidence-first core:

- signal collection patterns
- verification/auditing concepts
- deterministic gate-first scoring
- skeptical review / reality-spike mindset

---

## 2. Read Order

When starting work, read files in this order:

1. `AGENTS.md`
2. `final_pivot.md`
3. `IMPLEMENTATION_PLAN.md`
4. `COMPARATIVE_ANALYSIS.md`
5. `README.md`

If implementing code, treat `IMPLEMENTATION_PLAN.md` as the execution source of truth.

If judging product direction or scope, treat `final_pivot.md` as the source of truth.

---

## 3. Proof Levels

Keep these proof levels separate at all times:

1. **Fixture proof**
   - deterministic tests against saved inputs
2. **Dry-run proof**
   - provider wiring, orchestration, and query planning without claiming live retrieval proof
3. **Live proof**
   - real external retrieval and a real shipped product path

Never describe fixture proof as live proof.
Never describe dry-run proof as live proof.

---

## 4. Hard Gates vs Heuristics

### Hard gates

These inherited gates control whether an opportunity may reach `PURSUE`:

- `willingness_to_pay`
- `distribution_channel`
- `data_feasibility`

If any hard gate fails:

- verdict is `HOLD` or `SKIP`
- score is `0`
- no automated build should proceed

### Ranking heuristics

These may reorder valid opportunities but must not override hard gates:

- `competition_gap`
- `buildability`
- `reachability_strength`

---

## 5. Agent Roster

Use the smallest number of agents needed for the current phase.

### 5.1 Orchestrator

Purpose:
- controls phase order
- decides what to run next
- owns artifact boundaries
- enforces human approval gates

Responsibilities:
- read plan docs
- break work into tasks
- assign work to specialized agents
- verify that outputs move through the correct phase order
- stop agents from skipping gates

Write scope:
- may edit shared planning and coordination files
- should avoid editing implementation files that are already owned by a specialist in the same round

### 5.2 Scanner

Purpose:
- collect raw candidate signals from sources

Responsibilities:
- implement source-specific retrieval
- normalize raw results into a common candidate format
- preserve source URL, quote/snippet, timestamps, and source metadata

Write scope:
- `evidentia/scanners/`
- scanner tests
- fixture inputs for source retrieval

Must not:
- invent evidence
- score opportunities
- bypass verification

### 5.3 Verifier

Purpose:
- verify quotes, URLs, and source traceability

Responsibilities:
- fetch or load page/fixture text
- confirm quoted text exists
- normalize/canonicalize URLs
- assign discard reasons for failed verification

Write scope:
- `evidentia/auditor.py`
- verifier/fetch utilities
- verification tests
- discard-log related fixtures

Must not:
- fabricate verified status
- silently repair malformed evidence with prose

### 5.4 Scorer

Purpose:
- apply hard gates and ranking heuristics

Responsibilities:
- enforce deterministic hard gates
- deduplicate by source cluster
- apply freshness decay
- apply heuristic ranking only after hard gates pass

Write scope:
- `evidentia/scoring.py`
- models related to verdicts/coverage
- scoring tests

Must not:
- weaken hard gates for convenience
- let heuristics override gate failure

### 5.5 Spec Writer

Purpose:
- turn a chosen opportunity into a structured product spec

Responsibilities:
- synthesize a spec from verified evidence only
- output structured data
- preserve traceability to source-backed signals

Write scope:
- `evidentia/spec_writer.py`
- spec schema/tests
- spec fixtures

Must not:
- cite unverified claims
- trigger build or deploy automatically

### 5.6 Builder

Purpose:
- generate a wedge product from an approved spec

Responsibilities:
- scaffold app structure
- map approved spec features into code
- produce a locally runnable project

Write scope:
- `evidentia/builder.py`
- templates/
- builder tests
- generated-app validation helpers

Must not:
- change scoring semantics
- deploy without approval

### 5.7 Shipper

Purpose:
- handle deployment workflows

Responsibilities:
- wrap deploy tooling
- return deployment metadata
- keep deploy logic explicit and auditable

Write scope:
- `evidentia/deployer.py`
- deployment tests

Must not:
- auto-run without explicit approval
- claim production success without returned deployment data

### 5.8 Tracker

Purpose:
- collect post-deploy metrics

Responsibilities:
- pull visits, signups, and revenue-proxy signals from configured sources
- write structured tracking outputs

Write scope:
- `evidentia/tracker.py`
- tracker tests

Must not:
- fabricate metrics
- infer traction from missing data

---

## 6. Phase Ownership

### Phase 0-2

Primary agents:
- `orchestrator`
- `scanner`
- `verifier`
- `scorer`

This is the core MVP. Prefer not to start builder/deployer/tracker work until this core is stable.

### Phase 3

Primary agents:
- `orchestrator`
- `spec-writer`

Only begin once the evidence core is deterministic.

### Phase 4-5

Primary agents:
- `builder`
- `shipper`
- `tracker`

These are later-stage agents. They should not define product truth; they consume approved upstream artifacts.

---

## 7. Handoff Rules

All agents hand off through artifacts, not through loose prompt memory.

Required handoff pattern:

```text
scanner -> raw candidates
verifier -> verified signals + discard log
scorer -> ranked opportunities + verdicts
spec-writer -> structured product spec
builder -> runnable app artifact
shipper -> deployment metadata
tracker -> structured metrics
```

Each handoff must be:

- file-based or schema-based
- deterministic where possible
- traceable to the previous phase

---

## 8. Human Approval Gates

Human approval is required before:

- moving from scoring to build on a real opportunity
- deploying any generated app
- sending any outreach
- treating any result as live proof

Agents must not bypass these gates.

---

## 9. Repo Behavior Rules

1. Do not fabricate evidence.
2. Do not blur hard gates and heuristics.
3. Do not treat old completion claims as implementation proof.
4. Do not claim live capability without live verification.
5. Do not let builder/deployer/tracker rewrite evidence-core semantics.
6. Keep each agent within its file and phase ownership where possible.
7. Prefer tests before implementation changes.
8. Use fixtures for deterministic validation.

---

## 10. Suggested Startup Prompt For Codex App

Use this project with the following assumptions:

```text
Read AGENTS.md first.
Then read final_pivot.md and IMPLEMENTATION_PLAN.md.
Treat the repo as pre-implementation.
Prioritize the evidence-core phases before build/ship/track.
Keep hard gates strict: willingness_to_pay, distribution_channel, data_feasibility.
Treat competition_gap, buildability, and reachability_strength as ranking heuristics only.
Do not claim live proof unless real live verification has happened.
```

---

## 11. Current File Index

- `AGENTS.md`: operating contract for agentic work
- `final_pivot.md`: corrected product direction
- `IMPLEMENTATION_PLAN.md`: phased execution plan
- `COMPARATIVE_ANALYSIS.md`: evidence-based context and comparison
- `README.md`: lightweight repo index

