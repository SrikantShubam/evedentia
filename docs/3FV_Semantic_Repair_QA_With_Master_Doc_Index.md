# 3FV Semantic Repair QA + Master Documentation Index

**Date**: 2026-05-28  
**Context**: Full QA of the Verified-Voice Semantics Repair for the `three_first_person_voices` gate, followed by the complete one-page Master Documentation Index (with open questions) derived from parallel analysis of all 52 .md files.

---

# Part 1: QA Report — Verified-Voice Semantics Repair (three_first_person_voices gate)

**Test execution (independent run)**:  
Full suite under `main/tests/`: **98 passed, 1 skipped, 0 failures** (29s). Matches the claim exactly.

## Implementation Fidelity to the Proposed Plan

**Phase 1 (QualifiedEvidence)**: Implemented (`models.py:143-149`).

**Phase 2 (qualification step)**: Implemented. New `tournament/qualify.py` + wired into `engine.py:51` and `engine.py:104`.

**Phase 3 (rewrite of 3FV)**: Partially implemented.  
The strict logic exists in `gates.py:58-76` when `qualified_evidence` is passed.  
**Critical gap**: `gates.py:51-57` still contains the old "non-synthetic >= 3" fallback when `qualified_evidence is None`. This is a silent bypass.

**Phase 4/5**: Partial. Good diagnosis update in `diagnosis.py`. No live verification path yet (documented limitation).

**Fixtures & tests**: Good. Key fixtures updated with `"verified"` provenance. 5 new semantic tests in `test_gates.py` cover the exact matrix.

## Reviewer Questions — Answers from Actual Code

1. Can any unverified evidence still pass 3FV? **Yes** — via the None fallback branch.
2. Can multiple items from one speaker pass as distinct voices? **Yes** (default voice_key = evidence_id).
3. Did we treat provenance as truth again? **Partially** (qualify.py trusts the string "verified").
4. Is verification step isolated? **Mostly yes**.
5. Are failure reasons useful? **Yes** (5 distinct rationales).
6. Did backward compat create a silent bypass? **Yes** — the legacy path in the gate itself.

## Findings by Severity

**High**: Legacy fallback in gates.py:51-57 remains a material violation of the plan's intent.

**Medium**: Generous `first_person=True` default for non-verified items; weak voice distinctness; some integration tests still hit old path.

**Low**: Parallel data structures expected during transition.

## Strengths
- Engine path now enforces stricter semantics.
- Excellent explicit rationales.
- Fixture-backed tests and acceptance updates are disciplined.
- Full suite remains green.

## Readiness Verdict
**Ready for controlled CLI testing** on fixture data **with explicit caveat**: the improvement is real for normal `run_tournament` flows but not hermetic due to the fallback. Do not remove the None branch until all call sites are updated and a policy decision is made on direct `evaluate_gate` usage.

**Recommendation**: Add follow-up task to eliminate the legacy 3FV fallback and consider making qualified_evidence mandatory for that gate.

---

# Appendix A: Master Documentation Index (One-Page)

**Date**: 2026-05-28  
**Ground Rules Applied** (from main/AGENTS.md + main/docs/ACTIVE_PLAN.md):  
- Single active governing document: `main/docs/ACTIVE_PLAN.md`  
- All prior plans = historical records only  
- main/ canonical; codex/ and kimi/ archived/untouched  
- Canonical product: Generate → Validate (edge player → generate → validate → memo)  
- Proof levels: fixture > dry-run > live (never blur)  
- Quarantined: api.py, db.py, docs/frontend/  
- Hard gates + 4-way TerminalVerdict + mechanical memo

**Total files analyzed**: 52

## Active-Governing / Current Canonical

| Path | Classification | 1-Line Gist | Notes |
|------|----------------|-------------|-------|
| main/AGENTS.md | active-governing | Operating index; product, proof levels, quarantines, rules | Mandatory first read |
| main/docs/ACTIVE_PLAN.md | active-governing | The single active plan + test contract | Source of truth |
| main/README.md | product-spec | CLI quickstart for current workflow | Aligned |
| ultimate plan.md | product-spec | Full detailed spec (data shapes, TerminalVerdict, phases, memo) | Only root doc that matches current direction |
| main/HANDFOR_REVIEW.md | implementation-detail | Post-reset status and quarantine table | Useful history |
| main/outputs/memo_dry.md + memo_live.md | implementation-detail | Real mechanical memo + zero-winner diagnosis examples | Current validator output |

## Quarantined-Design (Do Not Treat as Active)

| Path | Classification | 1-Line Gist | Notes |
|------|----------------|-------------|-------|
| main/docs/frontend/* (3 files) | quarantined-design | Old scan/clustering/spec UI test plans | One file self-quarantines; the other two violate it |

## Historical-Archive (Superseded — Record of Drift Only)

**main/docs/archive/ (17 files)**: All superseded. Key cautionary documents:
- `reviewer.md`: 21 findings on plan drift, early Phase 5-7 work, dead code, multiple CLIs.
- `phase7_dogfood_retro.md` + `worklog_2026-04-24.md`: Records of premature API/cockpit work.
- `final_pivot.md`, `IMPLEMENTATION_PLAN.md`, `NEXT_PIVOT*`: Old factory and niche-hunter pipelines.
- `ARCHIVE_INDEX.md`: Self-authoritative "historical only".

**Root historical**: `COMPARATIVE_ANALYSIS.md`, `final_pivot.md` (old Codex/Kimi + build/ship factory).

**codex/ (8 files)**: Full prior forensic_engine (Hunter/Auditor/Prosecutor, golden cases, KILL/REJECT/SURVIVE, "MVP complete" claims). Explicitly archived/untouched.

**kimi/ (16 files)**: Parallel "Forensic Validation Engine" with 5 hunters + auditor + prosecutor + reality spike. Repeated "Production Ready", "100% complete", live integration claims. The exact parallel track labeled historical in the ground rules.

**Other**: `main/outputs/README.md` (dead hunt pipeline).

**Summary**: 7 active-governing/product-spec, 3 quarantined-design, 42 historical-archive.

**Usage Rule**: When in doubt, re-read only main/AGENTS.md and main/docs/ACTIVE_PLAN.md. Everything else exists to document the failure modes the current rules were written to stop.

**Generated by**: 5 parallel read-only subagents.

---

## Open Questions & Recommended Follow-ups

### Standing Questions (Apply to Every Historical or Quarantined Document)
- Does this document claim any form of "completion", "production ready", "MVP done", or "100% roadmap" without referencing fixture-backed acceptance tests that match the current 5 validator + generator contract in ACTIVE_PLAN.md?
- Does it blur proof levels (treating dry-run or old live runs as evidence of current capability)?
- Does it describe build/ship/API/cockpit work as part of the active MVP while ignoring the quarantine rule?
- Does it present parallel pipelines (hunt/loop/scan, hunter/auditor, niche critic) as still viable?
- Would a reader of this document be likely to violate the "one plan only" and "retire dead code" rules?
- What specific claims would need to be true for this document to be moved out of historical-archive?

### Specific High-Value Files — Targeted Questions

**reviewer.md (archive)**
- Which of the 21 findings have been fully closed by the current tournament engine work?
- What is the current status of the "surviving dead code" (scoring.py, critic.py, loop.py) it flagged?
- Has the "engine gate on real markets before Phase 5" rule been formally declared met since this review?

**ultimate plan.md (root)**
- Are any sections of this detailed spec silently deprioritized or contradicted by later changes in ACTIVE_PLAN.md?
- Has the explicit restriction "Do not start Phase 5 until Phase 4 engine gate met on real markets" been satisfied, and where is the evidence recorded?
- Do the exact data shapes and TerminalVerdict rules defined here still match current models.py + tournament/verdict.py?

**main/docs/frontend/* files**
- Why do the two long test plan files still exist and contain dated "verified by me" baselines when the directory's own README quarantines them?
- What is the concrete plan to delete or heavily mark these files?

**codex/plan.md and kimi/plan.md**
- Are there any specific gate definitions or claim-type distinctions here that are *stricter* than the current three_first_person_voices + qualify_evidence logic?
- If we ever wanted to mine these for test cases, what safe extraction process respects the "archived/untouched" rule?

**ACTIVE_PLAN.md (current)**
- The test contract claims all generator acceptance tests are present and passing. Do they cover evidence_provenance + QualifiedEvidence roundtrips after the 3FV semantic changes?
- Has the "engine is the only execution path" assumption been violated by direct calls to evaluate_gate outside run_tournament?

**Any file claiming "verified" evidence**
- Does the evidence carry explicit `verified: true` + `first_person: true` + usable `voice_key`, or is it only non-synthetic?
- Would the current qualify_evidence() + three_first_person_voices logic (with the None fallback removed) accept it?

**General Anti-Drift Questions**
- If an agent read only this document, what incorrect actions would they be likely to take?
- What would need to change in this document for it to become dangerous rather than merely historical?

**Suggested Next Actions**
- Audit all direct calls to `evaluate_gate` (especially 3FV) outside `run_tournament`.
- Decide fate of the two long frontend test files (delete or move to archive with warnings).
- Produce a one-page "Current vs Historical Gate Semantics" comparison.
- Consider a lint rule that fails on references to modules/files this index classifies as historical.

---

## QA Reviewer Questions (Grok 4.3 — 2026-05-28)

Acting as QA on the 3FV semantic repair + the full documentation corpus analysis, these are my open questions. They are not rhetorical — they need answers before I would sign off on "the semantic fix is solid and the documentation discipline is holding."

### On the 3FV Semantic Repair Itself
1. The legacy `if qualified_evidence is None` path in `gates.py:51-57` still performs the exact weak "non-synthetic >= 3" logic the plan was written to kill. Is this an intentional temporary shim with a removal ticket, or did it slip through review?
2. In `qualify.py`, non-"verified" items (seed, reentry, etc.) are defaulted to `first_person=True`. What is the actual evidence or policy justification for assuming a bare seed/reentry signal is first-person? This seems like the same class of over-assumption the old pipeline was criticized for.
3. The 5 new semantic tests all explicitly pass `qualified_evidence`. Have we run the full acceptance + integration suite with the None fallback temporarily removed (or made to hard-fail) to see what actually breaks in real fixtures and generated ideas?
4. Several integration tests (notably in `test_generator_roundtrip.py`) still call `evaluate_gate("three_first_person_voices", ...)` directly without qualification. Are these considered acceptable technical debt, or do they represent a hole in the "engine is the only execution path" rule stated in ACTIVE_PLAN.md?
5. The current implementation trusts the string `"verified"` in `evidence_provenance` to set both `verified=True` and `first_person=True`. What prevents a generator or manual artifact from incorrectly labeling something as "verified" and thereby bypassing the intent of the semantic repair?

### On the Broader Documentation & Drift Discipline
6. `reviewer.md` (May 25, 2026) is only a few days old relative to this work and lists 21 specific failures, including building Phase 5-7 before the engine gate on real markets. Which of those 21 findings are verifiably closed by the current tournament + 3FV changes versus still open or only directionally addressed?
7. The two long frontend test files (`GUI_INPUT_TESTS.md` and `MANUAL_VALIDATION_SET.md`) remain in the tree with dated "personally verified" baselines for pre-tournament UI behavior. Why have they not yet been moved to archive or deleted, given that even their own directory's README quarantines the entire frontend/ area?
8. `ultimate plan.md` contains an explicit non-negotiable restriction (#12): "Do not start Phase 5 until Phase 4's engine gate is met on real markets." Has this gate been formally declared met with evidence, and if so, where is that declaration and supporting data recorded so it can be audited?
9. `codex/plan.md` and `kimi/plan.md` contain hard-gate language and claim-type distinctions that are in some cases more specific than the current `three_first_person_voices` + `qualify_evidence` implementation. Is there a deliberate decision that the current version is intentionally looser, or is this an area of accidental regression in strictness?
10. The Master Index and this combined QA document I just helped produce — what is the mechanism to prevent them from becoming the next set of "helpful but eventually stale" analysis documents that future agents will have to wade through (exactly the problem `reviewer.md` documented)?

### Cross-Cutting / Process Questions
11. The full test suite (98 passed) is green. However, the new semantic tests for 3FV are all unit-level and explicitly supply `qualified_evidence`. What coverage exists for the *end-to-end path* where ideas come from the generator (or reentry) with only `evidence_provenance` set, flow through `run_tournament`, get qualified, and are then evaluated?
12. Given the project's extremely strong historical pattern of over-claiming completion (visible across codex/, kimi/, and multiple archived pivots), what is the current, written definition of "done" for the 3FV semantic repair that would prevent us from repeating that pattern?

These questions are now part of the permanent record in this file. Answers (or explicit decisions to defer) should be captured before treating the 3FV semantic work or the documentation hygiene as settled.

---

# Appendix A: Master Documentation Index (One-Page)

**Date**: 2026-05-28  
**Ground Rules Applied** (from main/AGENTS.md + main/docs/ACTIVE_PLAN.md):  
- Single active governing document: `main/docs/ACTIVE_PLAN.md`  
- All prior plans = historical records only  
- main/ canonical; codex/ and kimi/ archived/untouched  
- Canonical product: Generate → Validate (edge player → generate → validate → memo)  
- Proof levels: fixture > dry-run > live (never blur)  
- Quarantined: api.py, db.py, docs/frontend/  
- Hard gates + 4-way TerminalVerdict + mechanical memo

**Total files analyzed**: 52

## Active-Governing / Current Canonical

| Path | Classification | 1-Line Gist | Notes |
|------|----------------|-------------|-------|
| main/AGENTS.md | active-governing | Operating index; product, proof levels, quarantines, rules | Mandatory first read |
| main/docs/ACTIVE_PLAN.md | active-governing | The single active plan + test contract | Source of truth |
| main/README.md | product-spec | CLI quickstart for current workflow | Aligned |
| ultimate plan.md | product-spec | Full detailed spec (data shapes, TerminalVerdict, phases, memo) | Only root doc that matches current direction |
| main/HANDFOR_REVIEW.md | implementation-detail | Post-reset status and quarantine table | Useful history |
| main/outputs/memo_dry.md + memo_live.md | implementation-detail | Real mechanical memo + zero-winner diagnosis examples | Current validator output |

## Quarantined-Design (Do Not Treat as Active)

| Path | Classification | 1-Line Gist | Notes |
|------|----------------|-------------|-------|
| main/docs/frontend/* (3 files) | quarantined-design | Old scan/clustering/spec UI test plans | One file self-quarantines; the other two violate it |

## Historical-Archive (Superseded — Record of Drift Only)

**main/docs/archive/ (17 files)**: All superseded. Key cautionary documents:
- `reviewer.md`: 21 findings on plan drift, early Phase 5-7 work, dead code, multiple CLIs.
- `phase7_dogfood_retro.md` + `worklog_2026-04-24.md`: Records of premature API/cockpit work.
- `final_pivot.md`, `IMPLEMENTATION_PLAN.md`, `NEXT_PIVOT*`: Old factory and niche-hunter pipelines.
- `ARCHIVE_INDEX.md`: Self-authoritative "historical only".

**Root historical**: `COMPARATIVE_ANALYSIS.md`, `final_pivot.md` (old Codex/Kimi + build/ship factory).

**codex/ (8 files)**: Full prior forensic_engine (Hunter/Auditor/Prosecutor, golden cases, KILL/REJECT/SURVIVE, "MVP complete" claims). Explicitly archived/untouched.

**kimi/ (16 files)**: Parallel "Forensic Validation Engine" with 5 hunters + auditor + prosecutor + reality spike. Repeated "Production Ready", "100% complete", live integration claims. The exact parallel track labeled historical in the ground rules.

**Other**: `main/outputs/README.md` (dead hunt pipeline).

**Summary**: 7 active-governing/product-spec, 3 quarantined-design, 42 historical-archive.

**Usage Rule**: When in doubt, re-read only main/AGENTS.md and main/docs/ACTIVE_PLAN.md. Everything else exists to document the failure modes the current rules were written to stop.

**Generated by**: 5 parallel read-only subagents.

---

## Open Questions & Recommended Follow-ups

### Standing Questions (Apply to Every Historical or Quarantined Document)
- Does this document claim any form of "completion", "production ready", "MVP done", or "100% roadmap" without referencing fixture-backed acceptance tests that match the current 5 validator + generator contract in ACTIVE_PLAN.md?
- Does it blur proof levels (treating dry-run or old live runs as evidence of current capability)?
- Does it describe build/ship/API/cockpit work as part of the active MVP while ignoring the quarantine rule?
- Does it present parallel pipelines (hunt/loop/scan, hunter/auditor, niche critic) as still viable?
- Would a reader of this document be likely to violate the "one plan only" and "retire dead code" rules?
- What specific claims would need to be true for this document to be moved out of historical-archive?

### Specific High-Value Files — Targeted Questions

**reviewer.md (archive)**
- Which of the 21 findings have been fully closed by the current tournament engine work?
- What is the current status of the "surviving dead code" (scoring.py, critic.py, loop.py) it flagged?
- Has the "engine gate on real markets before Phase 5" rule been formally declared met since this review?

**ultimate plan.md (root)**
- Are any sections of this detailed spec silently deprioritized or contradicted by later changes in ACTIVE_PLAN.md?
- Has the explicit restriction "Do not start Phase 5 until Phase 4 engine gate met on real markets" been satisfied, and where is the evidence recorded?
- Do the exact data shapes and TerminalVerdict rules defined here still match current models.py + tournament/verdict.py?

**main/docs/frontend/* files**
- Why do the two long test plan files still exist and contain dated "verified by me" baselines when the directory's own README quarantines them?
- What is the concrete plan to delete or heavily mark these files?

**codex/plan.md and kimi/plan.md**
- Are there any specific gate definitions or claim-type distinctions here that are *stricter* than the current three_first_person_voices + qualify_evidence logic?
- If we ever wanted to mine these for test cases, what safe extraction process respects the "archived/untouched" rule?

**ACTIVE_PLAN.md (current)**
- The test contract claims all generator acceptance tests are present and passing. Do they cover evidence_provenance + QualifiedEvidence roundtrips after the 3FV semantic changes?
- Has the "engine is the only execution path" assumption been violated by direct calls to evaluate_gate outside run_tournament?

**Any file claiming "verified" evidence**
- Does the evidence carry explicit `verified: true` + `first_person: true` + usable `voice_key`, or is it only non-synthetic?
- Would the current qualify_evidence() + three_first_person_voices logic (with the None fallback removed) accept it?

**General Anti-Drift Questions**
- If an agent read only this document, what incorrect actions would they be likely to take?
- What would need to change in this document for it to become dangerous rather than merely historical?

**Suggested Next Actions**
- Audit all direct calls to `evaluate_gate` (especially 3FV) outside `run_tournament`.
- Decide fate of the two long frontend test files (delete or move to archive with warnings).
- Produce a one-page "Current vs Historical Gate Semantics" comparison.
- Consider a lint rule that fails on references to modules/files this index classifies as historical.

---

## QA Reviewer Questions (Grok 4.3 — 2026-05-28)

Acting as QA on the 3FV semantic repair + the full documentation corpus analysis, these are my open questions. They are not rhetorical — they need answers before I would sign off on "the semantic fix is solid and the documentation discipline is holding."

### On the 3FV Semantic Repair Itself
1. The legacy `if qualified_evidence is None` path in `gates.py:51-57` still performs the exact weak "non-synthetic >= 3" logic the plan was written to kill. Is this an intentional temporary shim with a removal ticket, or did it slip through review?
2. In `qualify.py`, non-"verified" items (seed, reentry, etc.) are defaulted to `first_person=True`. What is the actual evidence or policy justification for assuming a bare seed/reentry signal is first-person? This seems like the same class of over-assumption the old pipeline was criticized for.
3. The 5 new semantic tests all explicitly pass `qualified_evidence`. Have we run the full acceptance + integration suite with the None fallback temporarily removed (or made to hard-fail) to see what actually breaks in real fixtures and generated ideas?
4. Several integration tests (notably in `test_generator_roundtrip.py`) still call `evaluate_gate("three_first_person_voices", ...)` directly without qualification. Are these considered acceptable technical debt, or do they represent a hole in the "engine is the only execution path" rule stated in ACTIVE_PLAN.md?
5. The current implementation trusts the string `"verified"` in `evidence_provenance` to set both `verified=True` and `first_person=True`. What prevents a generator or manual artifact from incorrectly labeling something as "verified" and thereby bypassing the intent of the semantic repair?

### On the Broader Documentation & Drift Discipline
6. `reviewer.md` (May 25, 2026) is only a few days old relative to this work and lists 21 specific failures, including building Phase 5-7 before the engine gate on real markets. Which of those 21 findings are verifiably closed by the current tournament + 3FV changes versus still open or only directionally addressed?
7. The two long frontend test files (`GUI_INPUT_TESTS.md` and `MANUAL_VALIDATION_SET.md`) remain in the tree with dated "personally verified" baselines for pre-tournament UI behavior. Why have they not yet been moved to archive or deleted, given that even their own directory's README quarantines the entire frontend/ area?
8. `ultimate plan.md` contains an explicit non-negotiable restriction (#12): "Do not start Phase 5 until Phase 4's engine gate is met on real markets." Has this gate been formally declared met with evidence, and if so, where is that declaration and supporting data recorded so it can be audited?
9. `codex/plan.md` and `kimi/plan.md` contain hard-gate language and claim-type distinctions that are in some cases more specific than the current `three_first_person_voices` + `qualify_evidence` implementation. Is there a deliberate decision that the current version is intentionally looser, or is this an area of accidental regression in strictness?
10. The Master Index and this combined QA document I just helped produce — what is the mechanism to prevent them from becoming the next set of "helpful but eventually stale" analysis documents that future agents will have to wade through (exactly the problem `reviewer.md` documented)?

### Cross-Cutting / Process Questions
11. The full test suite (98 passed) is green. However, the new semantic tests for 3FV are all unit-level and explicitly supply `qualified_evidence`. What coverage exists for the *end-to-end path* where ideas come from the generator (or reentry) with only `evidence_provenance` set, flow through `run_tournament`, get qualified, and are then evaluated?
12. Given the project's extremely strong historical pattern of over-claiming completion (visible across codex/, kimi/, and multiple archived pivots), what is the current, written definition of "done" for the 3FV semantic repair that would prevent us from repeating that pattern?

These questions are now part of the permanent record in this file. Answers (or explicit decisions to defer) should be captured before treating the 3FV semantic work or the documentation hygiene as settled.