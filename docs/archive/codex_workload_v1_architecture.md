# Codex Workload v1 Architecture

**Document:** `codex_workload_v1_architecture.md`
**Scope:** In-depth architecture change overview for a Codex-centered workload that produces decision-grade opportunity artifacts instead of noisy ranked hits.
**Domain posture:** explicitly domain-agnostic; invoice, expense, accounting, finance, and similar examples may appear in fixtures or illustrations, but they must never become routing keywords or hidden defaults.
**Audience:** product, engineering, and agent orchestration owners
**Status:** proposed architecture baseline
**Date:** 2026-04-15

---

## Executive Summary

`codex_workload_v1` is a redesign of how Codex participates in the Evidentia pipeline.

The central change is simple:

Codex stops acting like an all-purpose market oracle and starts acting like a constrained artifact transformer inside explicit phase boundaries.

The workload moves from:

- scan everything
- infer opportunity quality
- score it
- suggest spec generation

into:

- admit or reject raw evidence
- normalize surviving evidence into structured demand artifacts
- separate observed facts from inferred judgments
- qualify opportunities through explicit gate rationale
- rank only comparable survivors
- expose spec readiness only when the record is complete enough

This redesign is required to make the output usable by a senior PM, not just interesting to read.

---

## Design Goals

`codex_workload_v1` must:

1. reduce junk in the operator review queue
2. prevent false-positive `PURSUE` decisions
3. preserve evidence provenance across every stage
4. make uncertainty explicit instead of implicit
5. make spec generation an earned transition, not a convenience button
6. keep hard gates deterministic and upstream of ranking
7. give Codex narrow, testable, schema-bounded tasks

It must not:

- let heuristics imply proof
- let one weak signal masquerade as demand certainty
- let builder/spec phases reinterpret upstream evidence
- hide missing data behind polished summaries
- rely on fixed topic keywords such as `invoice` or `expense` as the primary route into the queue
- assume any specific vertical, function, or workflow family as the default opportunity shape

---

## Domain-Agnostic Search Contract

Search, admissibility, clustering, and qualification must be driven by workflow pain, replacement intent, repeated friction, and reachable ICPs. They must not depend on fixed topic keywords, domain-specific whitelists, or a presupposed market category.

A candidate can be relevant in any domain if the text shows a repeated operational problem, a clear reason to replace the current workflow, and a plausible buyer or user that can be reached.

## Problem With the Current Shape

The current shape appears to behave roughly like this:

```text
scan -> verify -> classify -> score -> maybe spec
```

That is too compressed.

It causes three structural mistakes:

1. weak raw content gets promoted before admissibility is checked
2. hard-gate outcomes are inferred before evidence is organized by claim type
3. ranking and spec suggestion happen before the record is decision-grade

---

## Proposed Shape

`codex_workload_v1` should use this pipeline:

```text
scan
  -> admissibility filter
  -> evidence normalization
  -> signal typing
  -> opportunity assembly
  -> hypothesis generation
  -> prosecutor / validation loop
  -> gate evaluation
  -> qualification state assignment
  -> survivor ranking
  -> spec readiness check
  -> spec generation
```

This adds three missing stages and one missing boundary:

- a hard rejection layer before scoring
- a hypothesis-generation layer that turns repeated pain into candidate wedges
- a prosecutor or validation loop that tries to kill weak hypotheses before ranking
- a qualification layer before `PURSUE`
- a spec-readiness layer before spec generation

---

## Core Principle

Every stage should answer one question only.

Every stage must also remain domain-agnostic. The workload is not looking for invoice, expense, accounting, or any other preselected topic family. It is looking for repeated workflow pain, replacement intent, repeated friction, and reachable ICPs regardless of domain.

### Stage responsibilities

- `scan`: what raw source material might matter?
- `admissibility`: is this even a product-relevant signal?
- `normalization`: what was actually said and by whom?
- `signal typing`: what kind of evidence is this?
- `opportunity assembly`: which signals belong to the same problem cluster?
- `gate evaluation`: do we have enough evidence for hard-gate claims?
- `qualification`: what state is this opportunity in right now?
- `ranking`: among qualified survivors, which should be reviewed first?
- `spec readiness`: is there enough clarity to define a wedge?
- `spec generation`: produce a traceable product artifact

That is the workload split Codex needs.

---

## Generator-Validator Loop

The workload should not rely on scanning alone to produce good opportunities.

Pure scan-and-rank mostly returns:

- noisy complaints
- generic feature requests
- category SEO content
- competitor launches
- implementation tickets

The missing capability is controlled synthesis.

After signals are normalized and clustered, the system should generate explicit wedge hypotheses such as:

- a simpler replacement for a repeated incumbent failure
- a narrow workflow tool for a specific operator type
- a visibility or analytics layer where incumbents stop at vanity metrics
- an automation layer for a recurring manual process

Each hypothesis must then go through a validator loop before it can become an `OpportunityRecord` candidate for ranking.

### Loop shape

```text
clustered signals
  -> hypothesis generation
  -> prosecutor review
  -> reality-spike / missing-evidence check
  -> keep, revise, or kill
```

### Generator role

The generator may:

- propose 1-3 wedge hypotheses from a cluster of verified signals
- name the likely ICP
- define the broken workflow
- state the incumbent or workaround being replaced

The generator must not:

- pass hard gates
- imply buyer intent that is not evidenced
- skip the prosecutor pass

### Validator role

The validator should attack each hypothesis by asking:

- is this actually a product opportunity or just a complaint?
- is this a wedge or just a broad category?
- is there replacement intent or just discussion?
- is the ICP reachable?
- what evidence is still missing?

Only surviving hypotheses should proceed into gate evaluation and qualification.

---

## Codex Workload Definition

In `codex_workload_v1`, Codex is responsible for constrained transformations only.

### Allowed Codex tasks

- extract verbatim evidence into structured records
- classify evidence into strict enums
- generate wedge hypotheses from clustered verified signals
- generate prosecutor-style missing-evidence lists
- produce traceable rationale objects
- draft product specs from approved upstream artifacts

### Disallowed Codex tasks

- invent missing buyer intent
- pass hard gates from weak context clues
- convert generic chatter into market certainty
- rank opportunities that are not in the same evidence state
- recommend building when qualification is incomplete

---

## New Artifact Model

The architecture should introduce four artifact layers.

### 1. RawCandidate

Purpose:

- preserve scanner output before interpretation

Required fields:

- `candidate_id`
- `source`
- `source_url`
- `title`
- `raw_text`
- `author_handle` if available
- `timestamp`
- `metadata`

This artifact is not an opportunity.

### 2. DemandSignal

Purpose:

- normalize a verified piece of evidence into a typed signal

Required fields:

- `signal_id`
- `candidate_id`
- `source_url`
- `verbatim_quote`
- `signal_type`
- `actor_type`
- `problem_area`
- `evidence_strength`
- `proof_level`
- `observed_fields`
- `inferred_fields`

Key rule:

Observed and inferred data must not be merged.

### 3. OpportunityRecord

Purpose:

- aggregate multiple signals into one problem cluster

Required fields:

- `opportunity_id`
- `cluster_key`
- `problem_summary`
- `candidate_icp`
- `supporting_signals`
- `contradicting_signals`
- `freshness_summary`
- `duplicate_count`
- `qualification_state`
- `missing_evidence`

This is the main review artifact.

### 4. SpecReadinessRecord

Purpose:

- establish whether an opportunity can become a spec

Required fields:

- `opportunity_id`
- `ready_for_spec`
- `wedge_definition`
- `buyer_definition`
- `workflow_definition`
- `distribution_path`
- `build_scope`
- `blocked_by`
- `source_trace`

Only this artifact may unlock spec generation.

---

## State Machine

The architecture needs a stricter state machine.

### Proposed states

- `REJECT`
- `DISCOVER`
- `QUALIFY`
- `PURSUE`
- `DEFER`

### State semantics

`REJECT`
- not a product opportunity
- spam, noise, non-market discussion, vague chatter, or irrelevant content

`DISCOVER`
- product-relevant pain/request signal exists
- no decision-grade hard-gate evidence yet

`QUALIFY`
- enough evidence exists to justify further structured review
- missing evidence is explicit
- not yet ready for build/spec commitment

`PURSUE`
- all hard gates passed with rationale
- wedge is clear enough for spec generation

`DEFER`
- admissible but lower-priority due to timing, duplication, or portfolio constraints

If external UI needs `SKIP/HOLD/PURSUE`, map internally as:

- `REJECT` -> `SKIP`
- `DISCOVER` or `QUALIFY` or `DEFER` -> `HOLD`
- `PURSUE` -> `PURSUE`

But the internal workload must preserve the richer state model.

---

## Gate Evaluation Redesign

Hard gates must no longer be bare labels.

### Current problem

A simple `pass/fail` label hides:

- what evidence was used
- whether the judgment was observed or inferred
- how confident the judgment is
- what is missing

### New structure

Each hard gate should produce a rationale object:

```json
{
  "status": "pass|fail|unknown",
  "basis": "observed|inferred|mixed",
  "reason": "short explanation",
  "supporting_signal_ids": ["sig_1", "sig_2"],
  "missing_for_pass": ["explicit budget owner", "reachable acquisition path"]
}
```

### Hard gate rules

`willingness_to_pay`
- pass only on explicit spend, replacement intent, repeated painful workaround cost, or strong buyer urgency tied to business outcome

`distribution_channel`
- pass only when the acquisition path is concrete enough to name, not just imaginable

`data_feasibility`
- pass only when the input data and minimal workflow appear obtainable for a wedge

If any hard gate is `fail` or `unknown`, the record cannot become `PURSUE`.

---

## Admissibility Filter

This is the most important new stage.

It should reject before scoring when any of the following are true:

- pure speculation with no product action signal
- personal advice threads without externalizable product pattern
- generic feature labels with no workflow context
- obvious spam, engagement farming, or tester-swap noise
- non-buyer discussion disconnected from a repeated operational pain

### Why this matters

Right now too much garbage survives because the system tries to classify everything. That is the wrong optimization.

The first optimization should be ruthless exclusion, and that exclusion must be driven by product signal quality rather than topic keywords.

---

## Opportunity Assembly

Single posts should rarely become full opportunities alone.

The system should cluster signals by:

- problem area
- actor type
- workflow phrase
- incumbent mention
- repeated friction pattern

The output should show:

- how many distinct supporting signals exist
- whether they come from one source or multiple sources
- whether they represent the same complaint pattern

That prevents one post from masquerading as market truth.

---

## Ranking Redesign

Ranking should only operate on admissible survivors.

### Ranking inputs

- hard gates already passed or qualification state fixed
- deduplicated opportunity clusters
- freshness decay
- heuristic dimensions

### Ranking outputs

- queue order
- not truth claims

### Heuristic constraints

`competition_gap`, `buildability`, and `reachability_strength` remain useful, but only after gate evaluation is settled.

No heuristic score should be displayed for a `REJECT` record.
No composite score should imply build-readiness for `DISCOVER` records.

---

## Spec Readiness Layer

This is the second major missing boundary.

An opportunity is not spec-ready just because it is interesting.

Spec readiness must be inferred from domain-agnostic evidence of workflow pain, replacement intent, repeated friction, and a reachable ICP. It must not depend on invoice, expense, accounting, or any other fixed topic category being present.

### Spec-ready checklist

A record is spec-ready only if it can answer:

- who the user or buyer is
- what recurring workflow is broken
- what current workaround exists
- what minimum wedge can be built
- why this wedge is reachable
- what evidence supports each claim

### Architecture rule

`generate spec` must only appear when `ready_for_spec = true` on the `SpecReadinessRecord`.

If the record is not ready, the system should show `blocked_by` fields instead.

---

## Output Contract Redesign

The operator-facing output should stop pretending every item is equally mature.

The output contract must also stop implying that certain domains are preferred discovery targets. Any domain may produce a valid opportunity if the evidence shows pain, intent, repetition, and reachability.

### Proposed output sections per record

- `state`
- `cluster summary`
- `synthesized hypothesis`
- `problem summary`
- `who has the problem`
- `why this is in queue`
- `observed evidence`
- `inferred judgments`
- `hard gate rationale`
- `missing evidence`
- `spec readiness`
- `next action`

The operator should see cluster-level output first, not raw hit-level spam. Raw source rows are supporting evidence for a synthesized hypothesis, not the main artifact.

### Hypothesis output contract

Each surfaced record should read as:

- one semantic cluster
- one synthesized hypothesis
- one validation posture
- one explicit next action

That means the UI and downstream docs should prefer:

- cluster identifier or cluster summary
- synthesized wedge statement
- supporting evidence list
- prosecutor / validator verdict
- readiness state for spec handoff

And they should avoid presenting:

- isolated raw hits without synthesis
- fake certainty from a single source row
- raw scores with no cluster context
- opportunity cards that do not explain what was synthesized

### Example `next_action`

- `discard`
- `monitor`
- `qualify manually`
- `request follow-up evidence`
- `generate spec`

This is more useful than showing a naked score.

---

## Agent Boundary Changes

The repo already defines scanner, verifier, scorer, and spec-writer roles. `codex_workload_v1` should sharpen them.

### Scanner

Owns:

- raw candidate collection
- metadata preservation

Must not:

- imply opportunity quality

### Verifier

Owns:

- quote validation
- URL normalization
- proof-level tagging

Must not:

- classify market significance

### Signal Classifier

Owns:

- typed demand signal extraction
- observed vs inferred separation
- admissibility recommendation

Must not:

- assign `PURSUE`

### Opportunity Assembler

Owns:

- clustering
- duplicate collapse
- supporting and contradicting signal aggregation

### Gate Evaluator

Owns:

- hard-gate rationale objects
- qualification state assignment

### Spec Writer

Owns:

- spec generation from `SpecReadinessRecord`

Must not:

- repair missing upstream evidence with prose

---

## Why This Works Better With Codex 5.3xhigh

A strong coding model performs best when:

- tasks are narrow
- schemas are explicit
- uncertainty is first-class
- transitions are deterministic
- each artifact has one job

That is exactly what `codex_workload_v1` provides.

The model should be used for disciplined structured reasoning, not omniscient business inference.

---

## Migration Guidance

### Phase 1

Introduce new internal states and rationale objects without changing the outer CLI yet. Also remove any hidden dependency on invoice/expense/accounting keywords in search, clustering, admissibility, and qualification paths.

### Phase 2

Add admissibility filtering and hide heuristic scores for rejected items.

### Phase 3

Add `OpportunityRecord` and `SpecReadinessRecord` artifacts.

### Phase 4

Move spec generation behind readiness gating.

### Validation artifact rule

Manual validation docs should mirror the same contract:

- review cluster-level outputs, not raw rows
- check that a hypothesis is synthesized from multiple signals where available
- check that the validation posture is visible
- check that spec handoff fields trace back to the cluster evidence

### Phase 5

Update CLI and review UI to expose `next_action`, `missing_evidence`, and richer states.

---

## Success Criteria

`codex_workload_v1` is successful when:

1. obviously irrelevant posts are rejected before scoring
2. weak demand signals land in `DISCOVER`, not `PURSUE`
3. every hard-gate outcome includes rationale and source traceability
4. only clustered, admissible opportunities are ranked together
5. `generate spec` appears only on spec-ready records
6. operator review time decreases because the queue contains fewer junk records
7. downstream builder/spec phases can trust upstream artifact maturity

---

## Bottom Line

The architecture change is not about making Codex “smarter.”
It is about giving Codex the right workload.

`codex_workload_v1` makes the system credible by enforcing:

- stricter admissibility
- richer intermediate artifacts
- explicit qualification states
- hard-gate rationale objects
- a real spec-readiness boundary

That is the architecture Evidentia needs if it is going to produce decision-grade opportunity outputs instead of noisy internet summaries.

