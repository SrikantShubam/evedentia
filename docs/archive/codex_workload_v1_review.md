# Codex Workload v1 Review

**Document:** `codex_workload_v1_review.md`
**Scope:** Review of why the current Evidentia opportunity output is low-signal, misleading, and operationally unfit for spec generation.
**Audience:** product, architecture, and Codex implementation owners
**Status:** authoritative failure review for workload redesign
**Date:** 2026-04-15

---

## Executive Summary

The current workload is not failing because the coding model is weak. It is failing because the system hands the model an incoherent job definition.

The pipeline currently asks one pass of logic to do four different things at once:

1. detect raw discussion noise
2. infer whether it is a real market opportunity
3. assign hard-gate outcomes without enough evidence
4. imply spec readiness from minimal text fragments

That design guarantees bad output.

The result is exactly what the current samples show:

- irrelevant or weak Reddit posts enter the opportunity set
- generic GitHub issues are treated as market evidence
- heuristic scores are shown even when hard-gate proof is absent
- `PURSUE` can appear on records that do not support a build decision
- `generate spec` becomes attached to evidence that does not define a wedge, buyer, or distribution path

This is not a ranking bug in isolation. It is a workload-boundary failure.

---

## What We Fucked Up

### 1. We collapsed discovery, validation, and commitment into one stage

The current output treats these as interchangeable:

- someone mentioned a problem
- someone requested a feature
- someone will pay for a solution
- we can reach the buyer
- we have enough evidence to write a product spec

Those are different states.

The pipeline currently jumps from weak discovery evidence to decision language. That is the central error.

### 2. We allowed the model to infer hard-gate passes from vague text

The repo contract is explicit:

- `willingness_to_pay`
- `distribution_channel`
- `data_feasibility`

must gate `PURSUE`.

The sample output strongly suggests those gates are being inferred from weak proxies such as:

- complaint intensity
- feature specificity
- apparent buildability
- generic audience size

That is wrong. A good coding model cannot rescue a bad gate contract.

### 3. We promoted scanner noise into scored opportunities too early

Items such as:

- app tester swap posts
- family budgeting advice threads
- speculative science/philosophy posts
- one-line GitHub issue titles

should never survive into the same presentation layer as viable opportunities.

This indicates missing rejection logic before scoring.

### 4. We used heuristics as if they were partial substitutes for proof

Showing:

- `competition_gap`
- `buildability`
- `reachability`

on records that have not passed gate evidence creates false confidence.

Those heuristics only make sense after the opportunity is already admissible.

Right now they are decorating bad candidates.

### 5. We made spec generation look cheaper than it is

A spec-worthy opportunity needs at minimum:

- a defined actor or ICP
- a concrete repeated workflow or pain loop
- evidence that the pain matters enough to act on
- a plausible route to reach the buyer
- enough source detail to define a wedge

The current output attaches `generate spec` to fragments that do not meet that bar.

### 6. We optimized for “interesting hits” instead of decision-grade artifacts

The scanner seems to be producing content that is discussable, not content that is operationally useful.

That usually happens when the implicit objective becomes:

- find posts about pain

instead of:

- find evidence that survives a deterministic opportunity decision pipeline

### 7. We did not preserve provenance of uncertainty

The output does not clearly tell the operator:

- what was directly observed
- what was inferred
- what is still missing
- why a result is blocked from advancing

That makes review expensive and creates an illusion of confidence.

---

## Root Cause Statement

The current architecture defines the Codex workload too broadly and too ambiguously.

Instead of giving Codex a narrow, phase-bounded task, the system gives it a blended task:

- classify content
- deduce market truth
- compress uncertainty
- produce decision language
- hint at product direction

without a hard separation between evidence states.

This is the wrong workload for a coding model.

Codex should not be used as a magical market decider. It should be used to execute constrained evidence transformations with explicit output contracts.

---

## Failure Modes in the Sample Output

### Failure Mode A: False-positive `PURSUE`

Example pattern:

- Reddit beta-tester exchange post
- generic category pitch with no replacement intent
- no buyer segment proof
- no spend proof
- no distribution advantage
- still elevated to `PURSUE`

Interpretation:

- scanner admissibility is too weak
- gates are not being enforced deterministically enough
- score presentation is outrunning evidence quality

### Failure Mode B: Low-value `HOLD` clutter

Example pattern:

- quantum simulation speculation
- personal household budgeting thread
- random feature requests with no buyer or workflow context

Interpretation:

- the system is not filtering out non-opportunities early
- `HOLD` is carrying multiple meanings: irrelevant, uncertain, under-evidenced, and potentially good later
- operator triage cost is too high

### Failure Mode C: Evidence does not imply wedge

Example pattern:

- generic “add this feature” GitHub issue
- solution-category content marketing disguised as demand
- HN thread with interesting technical commentary

Interpretation:

- evidence may describe a problem area, but not a decision-ready product wedge
- spec generation is being suggested before wedge extraction is complete

### Failure Mode D: Presentation confuses discovery with recommendation

Showing a numeric score next to weak evidence implies:

- the system has enough confidence to compare opportunities

In many examples, it does not.

---

## Product Consequences

If left unchanged, the system will:

- waste PM time on junk review
- encourage building against weak demand signals
- overfit to public chatter instead of buyer evidence
- train operators to distrust the output
- make “spec generation” look unserious
- create regressions later when builder/shipper consume bad upstream artifacts

This is especially dangerous in this repo because downstream phases must not rewrite evidence-core truth.

---

## What the System Actually Needs to Do

The workload must be reframed around artifact quality, not hit volume.

The right sequence is:

1. detect candidate evidence
2. reject obvious non-opportunities immediately
3. normalize surviving evidence into typed demand signals
4. cluster repeated pain into problem patterns
5. generate explicit wedge hypotheses from those patterns
6. run a prosecutor or validation pass that tries to kill weak hypotheses
7. evaluate hard gates only on surviving hypotheses
8. assign a phase state that reflects what is known
9. only then rank comparable opportunities
10. only then permit spec readiness review

---

## Missing Loop

The current system is acting like a search engine with opinions.

What it is missing is the generator-validator loop that existed in the stronger prior design patterns:

- one pass generates candidate wedges from clustered evidence
- a second pass prosecutes those wedges and tries to kill them
- only survivors enter ranking and qualification

That matters because good opportunities are often not present as a single perfect post. They emerge from multiple weak-but-related signals that need synthesis first and skepticism second.

Without that loop, the system does one of two bad things:

- promotes raw junk directly into ranking
- misses synthesizable wedges because no single post looks complete enough

The fix is not just better filtering. It is adding explicit hypothesis generation followed by explicit validation.

---

## Required Output States

The current `PURSUE/HOLD/SKIP` set is not enough for operator clarity.

At minimum, the workload needs these practical states:

- `REJECT`: irrelevant, spam, chatter, or not a product opportunity
- `DISCOVER`: interesting pain/request signal but insufficient commitment proof
- `QUALIFY`: enough evidence to investigate wedge/ICP/channel manually or with follow-up logic
- `PURSUE`: all hard gates passed and evidence is strong enough for spec creation
- `DEFER`: maybe relevant, but blocked by freshness, duplication, or low current priority

If the repo wants to preserve `SKIP/HOLD/PURSUE`, then map them internally, but do not expose one overloaded `HOLD` bucket to the user.

---

## Review of Codex Usage

### What Codex should do well here

- schema-constrained extraction
- evidence normalization
- typed classification with strict labels
- wedge summarization from verified inputs
- structured missing-evidence reporting
- disciplined spec drafting from approved upstream artifacts

### What Codex should not be asked to do

- infer willingness to pay from generic emotional language
- guess distribution viability from broad internet familiarity
- manufacture a product wedge from one weak post
- convert partial evidence into confidence language
- hide uncertainty behind numeric scores

---

## Decision Standard Going Forward

No item should reach spec generation unless the record can answer, from verified evidence or explicit review annotations:

- who has the problem
- what repeated workflow is broken
- what action they currently take
- why existing alternatives are insufficient
- why this is reachable
- what minimum wedge can be built
- which hard-gate evidence supports advancement

If those fields are absent, the artifact is not spec-ready.

---

## Non-Negotiable Changes

1. Introduce a pre-score rejection stage.
2. Split discovery state from pursue state.
3. Separate observed evidence from inferred judgments.
4. Require gate rationale objects, not bare pass/fail labels.
5. Stop showing heuristic scores for inadmissible opportunities.
6. Gate `generate spec` behind explicit spec-readiness criteria.
7. Make missing evidence visible in the output.
8. Deduplicate by problem cluster before operator review.
9. Treat generic GitHub issues as weak product evidence unless coupled to buyer or workflow context.
10. Prevent a single public post from looking like market truth.

---

## Bottom Line

The current system is not producing nonsense because Codex 5.3xhigh is incapable.
It is producing nonsense because the workload definition is wrong.

The fix is architectural:

- narrower Codex tasks
- stricter state transitions
- harder admissibility filters
- explicit uncertainty surfaces
- spec generation only after real qualification

That is the basis for `codex_workload_v1`.


