# Master Documentation Index — Evidentia

**Date**: 2026-05-28  
**Ground Rules Applied** (from main/AGENTS.md + main/docs/ACTIVE_PLAN.md):  
- Single active governing document: `main/docs/ACTIVE_PLAN.md`  
- All prior plans = historical records only (do not use as implementation guides)  
- main/ is canonical; codex/ and kimi/ are archived/untouched previous experiments  
- Canonical product: Generate → Validate (edge player → edge generate → edge validate → edge memo)  
- Proof levels: fixture > dry-run > live (never blur)  
- Quarantined until live proof: api.py, db.py, entire docs/frontend/  
- Hard gates: willingness_to_pay, distribution_channel, data_feasibility (verdict HOLD/SKIP on failure)  
- 4-way TerminalVerdict (KILL / INSUFFICIENT_EVIDENCE / SHORTLIST / PURSUE_SPIKE), mechanical memo, file/schema handoffs only

**Total .md files analyzed**: 52 (via 5 parallel read-only subagents)

---

## Active-Governing / Current Canonical (Treat as Current Truth)

| Path                              | Classification      | 1-Line Gist                                                                 | Notes |
|-----------------------------------|---------------------|-----------------------------------------------------------------------------|-------|
| main/AGENTS.md                    | active-governing    | Operating index for all agentic work; defines product, proof levels, quarantines, repo behavior rules | Mandatory first read for any agent |
| main/docs/ACTIVE_PLAN.md          | active-governing    | Concise declaration of generate→validate system, test contract (5 validator + generator acceptance tests), quarantines | The single source of truth |
| main/README.md                    | product-spec        | CLI quickstart and overview for edge player/generate/validate/memo workflow | Aligned with ACTIVE_PLAN |
| ultimate plan.md                  | product-spec        | Detailed master spec: data shapes, deterministic 4-way TerminalVerdict, gate profiles (structural/evidence), mechanical memo, phases 0-7, anti-hallucination contract | Only root-level document fully consistent with current direction |
| main/HANDFOR_REVIEW.md            | implementation-detail | Post-reset (May 2026) status: quarantine table, CLI cleanup to edge-only, generator/validator handoff questions, 84 tests passing at time of writing | Useful bridge explaining how current state was reached |
| main/outputs/memo_dry.md          | implementation-detail | Real mechanical Decision Memo artifact (zero-winner case, 3FV failure diagnosis) from dry-run | Direct example of current validator output |
| main/outputs/memo_live.md         | implementation-detail | Real mechanical Decision Memo artifact from live tournament (zero-winner on 3FV) | Demonstrates live proof-level output format |

---

## Quarantined-Design (Do Not Treat as Active Guidance)

| Path                                           | Classification      | 1-Line Gist                                                                 | Notes |
|------------------------------------------------|---------------------|-----------------------------------------------------------------------------|-------|
| main/docs/frontend/README.md                   | quarantined-design  | Self-declaration that the directory holds UI prototypes for the old product framing and is quarantined | Correctly self-enforces the rule |
| main/docs/frontend/GUI_INPUT_TESTS.md          | quarantined-design  | Manual input validation tests for old live Vercel scan→cluster→hypotheses UI (pre-reset semantics) | Direct violation of quarantine |
| main/docs/frontend/MANUAL_VALIDATION_SET.md    | quarantined-design  | Detailed regression test plan + "personally verified" baselines for old Next.js cockpit (semantic clustering, spec handoff) | Dated April 2026; strong violation |

---

## Historical-Archive (Superseded — Record of Past Pivots and Drift Only)

**main/docs/archive/ (17 files)** — All explicitly superseded per ARCHIVE_INDEX.md. Chronology of repeated plan drift.

**Most Important Cautionary Files**:
- `reviewer.md` (May 25, 2026): 21 findings — plan proliferation (7+ docs), Phase 5-7 built before Phase 3-4 engine gate on real markets, surviving dead code (scoring.py, critic.py, loop.py), three competing CLIs, zero test-first commits. Directly documents the violations the current rules were written to prevent.
- `phase7_dogfood_retro.md` + `worklog_2026-04-24.md`: Contemporaneous records of premature Phase 5 (API) + Phase 6 (cockpit) + Phase 7 tuning implementation.
- `final_pivot.md`, `IMPLEMENTATION_PLAN.md`: Original "Scan → Score → Spec → Build → Ship → Track" AI Venture Factory vision.
- `NEXT_PIVOT*.md` + related work orders: Niche-hunter pivot (KILL/REFINE/PURSUE) that was itself superseded.
- `ARCHIVE_INDEX.md`: Self-authoritative declaration that only ACTIVE_PLAN.md governs.

**Root-Level Historical**:
- `COMPARATIVE_ANALYSIS.md`: 2026-04-14 Codex vs Kimi forensic engine comparison (Kimi declared "production-ready", Codex at 41%).
- `final_pivot.md`: The demand-to-shippable-product factory pipeline (build/ship as core MVP).

**codex/ (8 files)** — Entire prior "forensic_engine" experiment:
- Hunter/Auditor/Prosecutor pipeline, golden cases + mutation prompts, KILL/REJECT/SURVIVE verdicts, "MVP complete" + live pipeline claims.
- All files (plan.md, journey.md, README.md, GIVEMEKEYS.md, golden_prompts/*, fixtures/golden_cases/README.md) classified historical-archive.
- No instruction in ACTIVE_PLAN or AGENTS to revive or consult these artifacts.

**kimi/ (16 files)** — Parallel "Forensic Validation Engine" track:
- 5 specialized hunters + Verification Auditor + Gap Prosecutor + Reality Spike Outreach.
- Repeated maximal claims across multiple files: "🎉 COMPLETE - Production Ready", "100% of roadmap items", "LIVE and READY for production use", end-to-end simulations with 100% accuracy.
- plan.md (detailed spec with patched hard gates), journey*.md, PROJECT_COMPLETION_SUMMARY.md, ROADMAP_COMPLETION.md, README.md, TESTING_LOG.md (runnable traces with live search), GIVEMEKEYS.md, etc.
- Explicitly the "parallel implementation track (hunters/auditors/prosecutors, live integration)" labeled archived/untouched in ground rules.

**Other Historical in main/**:
- `main/outputs/README.md`: Describes superseded anchor-hunt / best_ideas.jsonl pipeline and `evidentia best` CLI.

---

**Summary Statistics** (52 files)
- Active-governing / Product-spec: 7
- Quarantined-design: 3
- Historical-archive: 42

**Usage Rule**: When in doubt, re-read only `main/AGENTS.md` and `main/docs/ACTIVE_PLAN.md` before consulting any other .md file. All historical documents exist to illustrate the exact failure modes (plan drift, early Phase 5-7 work, over-claiming completion, parallel pipelines) that the current ruthless player-aware Generate→Validate engine + mechanical memo + strict proof levels were designed to eliminate.

**Generated by**: 5 parallel read-only subagents (dispatching-parallel-agents skill) using embedded ground rules for consistent classification.

---

## Open Questions & Recommended Follow-ups

Use these questions whenever you encounter any .md file in this repository. They are derived from the ground rules and the patterns visible across the 52 documents.

### Standing Questions (Apply to Every Historical or Quarantined Document)
- Does this document claim any form of "completion", "production ready", "MVP done", or "100% roadmap" without referencing fixture-backed acceptance tests that match the current 5 validator + generator contract in ACTIVE_PLAN.md?
- Does it blur proof levels (treating dry-run or old live runs as evidence of current capability)?
- Does it describe build/ship/API/cockpit work as part of the active MVP while ignoring the quarantine rule for api.py / db.py / docs/frontend/?
- Does it present parallel pipelines (hunt/loop/scan, hunter/auditor, niche critic) as still viable or referenceable?
- Would a reader of this document be likely to violate the "one plan only" and "retire dead code" rules?
- What specific claims in this document would need to be true for it to be moved out of historical-archive into active use — and are those claims currently testable?

### Specific High-Value Files — Targeted Questions

**reviewer.md (archive)**
- Which of the 21 findings have been fully closed by the current tournament engine + mechanical memo work, and which remain open?
- Does the existence of this document itself constitute a violation of the rules it describes (plan proliferation)?
- What is the current status of the "surviving dead code" (scoring.py, critic.py, loop.py imports) flagged here?
- Has the "engine gate on real markets before Phase 5" rule been enforced since this review?

**ultimate plan.md (root)**
- Are there any sections of this detailed spec that have been silently deprioritized or contradicted by later changes in ACTIVE_PLAN.md or HANDFOR_REVIEW.md?
- Does the confidence threshold tuning and SHORTLIST vs PURSUE_SPIKE distinction still match current implementation in tournament/verdict.py and confidence.py?
- The plan says "Do not start Phase 5 until Phase 4 engine gate met on real markets." Has this gate been formally declared met, and where is the evidence?
- Are the exact data shapes defined here still the source of truth, or have they drifted in models.py?

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

**main/docs/frontend/* files**
- Given that the frontend/README.md correctly quarantines the directory, why do the two long test plan files still exist and contain dated "verified by me" baselines?
- What is the plan to either delete or clearly mark these files so future agents do not accidentally treat them as active design?
- Do any current components in main/src/evidentia/ still assume UI behavior described in these files?

**codex/plan.md and kimi/plan.md**
- Both documents contain very similar "hard gate" language to the current system. Are there any specific gate definitions or claim-type distinctions here that are *stricter* than what the current three_first_person_voices + qualify_evidence logic enforces?
- If we ever wanted to mine these for test cases, what would be the safe extraction process that does not violate the "archived/untouched" rule?

**ACTIVE_PLAN.md (current)**
- The test contract claims all 5 validator acceptance tests + generator roundtrips are present and passing. Is this still true after the latest 3FV semantic changes?
- The document says "Generator acceptance tests (present and passing)". Where are the explicit generator acceptance tests, and do they cover evidence_provenance + QualifiedEvidence roundtrips?
- Has the "engine is the only execution path" assumption been violated anywhere in the current codebase (direct calls to evaluate_gate outside run_tournament, etc.)?

**Any file claiming "verified" evidence or live results**
- Does the evidence carry explicit `verified: true` + `first_person: true` + usable `voice_key`, or is it only non-synthetic?
- Would the current qualify_evidence() + three_first_person_voices logic (with the None fallback removed) accept this evidence?

**General Anti-Drift Questions**
- If an agent read only this document (and nothing else), what incorrect actions would they be likely to take?
- What would need to change in this document for it to become dangerous rather than merely historical?

**Next Actions This Index Suggests**
- Run a targeted review of all direct calls to `evaluate_gate` (especially for three_first_person_voices) outside of `run_tournament`.
- Decide the fate of the two long frontend test files (delete vs. move to archive with heavy warnings).
- Produce a one-page "Current vs Historical Gate Semantics" comparison that can be shown to anyone referencing old codex/kimi material.
- Consider adding a linter or test that fails if any new code imports or references modules/files that this index classifies as historical.