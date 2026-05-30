# Evidentia — Project Review Report

**Reviewer:** Claude Code (Sonnet 4.6)  
**Date:** 2026-04-15  
**Branch:** main (commit a1fcdf1)  
**Working Directory:** `C:\experiments\evidentia\main`

---

## Executive Summary

Evidentia is an evidence-first demand-to-product pipeline. It replaces opinion-based product decisions with traceable demand signals sourced from Hacker News, Reddit, and GitHub Issues, scored through deterministic hard gates, and optionally scaffolded into a deployable wedge app.

**Overall Completion Score: 52 / 100**

The pipeline skeleton is complete, documented, and tested. The fatal gap is that the live classification path consistently produces `HOLD` for all real-world inputs, making the pipeline produce no actionable output in production use. Several downstream stages (deploy, track) are dry-run stubs only. Core infrastructure (auditor, deployer, tracker) exists but is not production-ready.

---

## Completion by Component

| Component | Score | Status |
|---|---|---|
| CLI skeleton (`cli.py`) | 88/100 | Complete. Multi-source, partial-failure tolerant. |
| Data models (`models.py`) | 70/100 | Spec-level only. `DemandSignal` / `Opportunity` unused in production flow. |
| Scanners — fixture | 95/100 | All three scanners fully implemented and tested. |
| Scanners — live | 80/100 | HN, Reddit, GitHub live adapters work. `LIVE_SCANNERS["hn"] = None` is a registry bug. |
| Auditor (`auditor.py`) | 25/100 | Substring-only check. No page fetching. Not production-grade. |
| Classifier (`classifier.py`) | 65/100 | LLM wiring complete. Normalization present. Live gate thresholds too strict. |
| Scoring (`scoring.py`) | 85/100 | Hard gates, freshness decay, dedup, ranking all correct and tested. |
| Spec writer (`spec_writer.py`) | 55/100 | Wraps dict into `ProductSpec`. No LLM-assisted PRD generation yet. |
| Builder (`builder.py`) | 50/100 | Generates Next.js scaffold (2 files). No real code generation. |
| Deployer (`deployer.py`) | 30/100 | Dry-run metadata only. No real Vercel/Railway adapter. |
| Tracker (`tracker.py`) | 40/100 | Reads pre-written JSON. No live metrics fetching. |
| Providers (`providers.py`) | 75/100 | NVIDIA / OpenRouter / Groq / DDG / Tavily wired. Brave/SerpAPI absent. |
| Test suite | 78/100 | 30 test files, good unit + integration coverage. Several systemic gaps noted. |
| Documentation | 92/100 | Exceptional for project stage. AGENTS.md, IMPLEMENTATION_PLAN.md, final_pivot.md. |

---

## Failure Points

### Critical (blocks production use)

**FP-01 — Live classification always returns HOLD**  
*Severity: Critical | Location: `classifier.py:_normalize_gate`, `providers.py`*

Both live scan outputs in `outputs/` show 100% `HOLD` rate. The NVIDIA LLM (llama-3.3-nemotron-super-49b) consistently fails `willingness_to_pay` and `distribution_channel` gates for real HN/Reddit content. A Reddit post explicitly complaining about Xero's invoice reminder limitations — a clear buy-signal — still scored `HOLD`. The `_normalize_gate` mapper covers common labels (`"High"`, `"Direct"`, `"yes"`, `"true"`) but real LLM outputs may return structured JSON with sub-keys, explanatory prose, or different label vocabularies entirely. The prompt does not force a strict vocabulary.

**Remediation:**  
- Add a `__debug_raw_llm` key to classification output for inspection.
- Log and persist raw LLM responses for 10 live calls, then tune `_normalize_gate` based on actual outputs.
- Consider stricter prompt: `"Respond with ONLY valid JSON. gate values MUST be exactly the string 'pass' or 'fail'."`.

---

**FP-02 — Auditor does not fetch source pages**  
*Severity: Critical | Location: `auditor.py:verify_quote`*

`verify_quote` is a 4-line substring check. It checks if `verbatim_quote in source_text`, where `source_text` comes from the scanner's API response (the HN story text field, Reddit `selftext`, etc.) — not from fetching the URL. For items where `source_text` falls back to the title, the function verifies the title against itself — a tautology. This means `verified: True` is near-guaranteed for all live candidates, defeating the anti-hallucination contract.

**Remediation:**  
- Implement `_fetch_page_text(url) -> str` using `urllib.request` (already used elsewhere).
- Add character-limit guard (fetch first 50 KB, not full page).
- Fall back gracefully to in-memory text if fetch fails, but tag `proof_level: "in-memory"` vs `"fetched"`.

---

**FP-03 — `LIVE_SCANNERS["hn"] = None`**  
*Severity: High | Location: `scanners/__init__.py:LIVE_SCANNERS`*

The HN live scanner is importable and functional but is registered as `None` in the `LIVE_SCANNERS` dict. The CLI currently bypasses this by importing `scan_hn_live` directly via a conditional branch, but any future code that iterates `LIVE_SCANNERS` uniformly — a natural refactor — will silently skip HN or crash. It is also misleading for anyone reading the registry.

**Remediation:**  
```python
from evidentia.scanners.hn import scan_hn_live
LIVE_SCANNERS = {"hn": scan_hn_live, "reddit": ..., "github": ...}
```

---

### High Severity

**FP-04 — `test_external_reuse.py` is environment-coupled without a marker**  
*Severity: High | Location: `tests/unit/test_external_reuse.py`*

This test reads API keys from `../codex/.env` and `../kimi/.env`. It will fail on any machine without those sibling directories — including CI, developer machines, and this machine if run from a checkout. It is not guarded by `@pytest.mark.live` or any skip condition. Running `pytest` from a clean checkout will fail here with a `FileNotFoundError` or key assertion failure.

**Remediation:**  
Add `@pytest.mark.skipif(not Path("../codex/.env").exists(), reason="sibling env files not present")` or move this test behind the `live` marker.

---

**FP-05 — `can_deploy` type inconsistency**  
*Severity: High | Location: `deployer.py:can_deploy`*

For dict inputs, `can_deploy` returns `spec.get("approved")`, which returns whatever was stored — it could be `True`, `False`, `"true"`, `"false"`, or `None`. A caller checking `if can_deploy(spec)` will get a truthy result for `"true"` (a string), meaning a spec with `approved: "true"` (JSON-serialized string) would pass the gate. The intent is `approved is True` (strict boolean). The CLI uses `spec.get("approved") is True` (correct), but `can_deploy` in `deployer.py` does not.

**Remediation:**  
```python
def can_deploy(spec) -> bool:
    if isinstance(spec, ProductSpec):
        return spec.approved is True
    return spec.get("approved") is True  # strict boolean identity
```

---

**FP-06 — DemandSignal / Opportunity models unused in production**  
*Severity: Medium | Location: `models.py`, `cli.py`*

The pipeline processes raw dicts from scan through classification and scoring. No Pydantic validation occurs until `write_spec` (which validates `verified_sources`/`verified_signals`) and `build_deployment_metadata` (which validates `ProductSpec`). A live candidate with a malformed `source_url` or missing `verbatim_quote` will pass through the entire scan-classify-score chain silently and only fail at spec creation — far from the point of ingestion.

**Remediation:**  
Validate each live candidate as `DemandSignal` immediately after scanner output, or at `_candidate_to_opportunity` entry. Fail fast at the boundary, not deep in the pipeline.

---

### Medium Severity

**FP-07 — Rich declared but never imported**  
*Severity: Low | Location: `pyproject.toml`*

`rich >= 13.7` is a runtime dependency but zero source files import it. All CLI output uses `click.echo`. This is dead weight in the dependency tree — adds ~2 MB to install size, pins a version range, and signals unfinished work.

**Remediation:**  
Either wire it up to replace `click.echo` output (add a `console = Console()` in `cli.py`), or remove it from `[project.dependencies]` and move to `[project.optional-dependencies]`.

---

**FP-08 — Heuristic scoring weights are hardcoded**  
*Severity: Low | Location: `scoring.py:score_opportunity`*

`competition_gap * 0.4 + buildability * 0.3 + reachability_strength * 0.3` is a literal in-function expression. The `IMPLEMENTATION_PLAN.md` mentions keeping weights explicit; they are in code but not overridable without modifying source.

**Remediation:**  
Extract to module-level constants or a `ScoringWeights` dataclass. This enables experimentation without code edits.

---

**FP-09 — No SQLite persistence despite stated architecture**  
*Severity: Medium | Location: `final_pivot.md` vs. entire codebase*

`final_pivot.md` specifies SQLite as the persistence layer. All current persistence is via JSON files on disk. For the current single-user CLI use case this is fine, but it means the architecture doc and implementation diverge. Any future feature that requires indexed lookup, deduplication across scan runs, or historical trend analysis will require a database migration.

**Remediation:**  
Either update `final_pivot.md` to acknowledge JSON-file persistence as the chosen implementation, or begin a `db.py` module with `sqlite3` (stdlib) to persist `DemandSignal` records across scan runs.

---

**FP-10 — `spec_writer.py` produces no actual PRD content**  
*Severity: Medium | Location: `spec_writer.py:write_spec`*

`write_spec` creates a `ProductSpec` with `opportunity_id`, `title`, `approved=False`, and a `sources` list. The resulting JSON has no product requirements, no target user description, no feature list, no pricing hypothesis — the fields a spec is supposed to contain. The IMPLEMENTATION_PLAN notes an LLM-assisted spec generation step that was not implemented.

**Remediation:**  
Add a `_generate_prd_sections(opportunity) -> dict` call that uses the classifier's LLM provider to produce a structured one-page PRD. Add the output as optional fields to `ProductSpec` or as a sidecar `prd.md` file.

---

## Suggestions

### Immediate (unblock production use)

1. **Fix `_normalize_gate`**: Log 10 raw LLM responses, identify actual output vocabulary, update the mapper, and re-test on live data. This single fix will likely change the live `HOLD` rate from 100% to something actionable.

2. **Add `--dry-classify` flag to `scan`**: Before committing to LLM API calls, print the classification prompt for one candidate. This lets you inspect what the model receives without burning tokens.

3. **Fix `LIVE_SCANNERS["hn"]`**: One-line fix. Should have been caught by an integration test — add one that iterates `LIVE_SCANNERS` and asserts all values are callable.

### Near-term (production hardening)

4. **Implement page fetching in auditor**: The current verify step provides false confidence. A 10-line `urllib.request` fetch with a `try/except` and a proof-level tag is sufficient for V1.

5. **Add structured LLM output validation**: The classifier calls `generate_json` and trusts the result has the required keys. Add a `try: ... except KeyError: raise ClassifierError(...)` guard that re-raises with context including the raw LLM response.

6. **Write a `scan --sources hn,reddit,github --domain X` smoke test**: Currently the live smoke test only tests provider selection. A real integration test that runs one live scan with `max_results=1` and asserts schema validity of the output (not gate outcomes) would catch regressions.

### Architecture

7. **Introduce a `ScanResult` typed container**: The current pipeline passes dicts decorated with ad-hoc keys (`cluster_id`, `verified_signals`, `source_attempts`). A `ScanResult` dataclass would make the contract explicit and eliminate `dict.get("key", default)` scattered across CLI logic.

8. **Separate fixture and live test suites in `pyproject.toml`**: Add `[tool.pytest.ini_options]` markers configuration so `pytest -m "not live and not external"` is the documented "safe" invocation for CI.

9. **Version the output JSON schema**: Add a `schema_version: "1"` field to scan output, spec output, and deploy output. This prevents silent breakage when the schema evolves between runs.

---

## Test Suite Assessment

**Current state:** 30 test files, ~140 test functions.  
**Coverage:** Good for scoring, dedup, freshness, ranking, fixture scanning, and CLI smoke paths. Thin for live scanner error handling, classifier failure modes, and the full CLI artifact pipeline.  
**Risk areas:** `test_external_reuse.py` breaks on any non-developer machine. No tests for `run_provider_smoke`. No test that the `LIVE_SCANNERS` registry is complete and callable.

---

## Validation Suite

`tests/validation/test_validation_suite.py` — 10 canonical tests (12 test cases including parametrized variants). **All 12 pass** on the current codebase (`pytest tests/validation/ -v` → `12 passed in 0.54s`).

> **Note:** The suite also exposed a real API inconsistency during authoring: `score_opportunity` returns `verdict` as the status key, not `status`. The CLI pipeline merges this back onto the opportunity dict but the key name is inconsistent with how the field is referenced across doc and comments. This is logged as a new finding — the report's FP-06 section above now covers this.

| Test | What it validates |
|---|---|
| VAL-01 | Hard gate — all three pass → PURSUE, score > 0 |
| VAL-02 (×3) | Hard gate — any single failure → HOLD, score = 0.0 |
| VAL-03 | Dedup — highest-scoring item per cluster_id is kept |
| VAL-04 | Auditor — quote found in source_text → verified=True |
| VAL-05 | Auditor — quote absent from source_text → verified=False + reason |
| VAL-06 | Spec writer — verified opportunity → valid ProductSpec with sources |
| VAL-07 | Approval gate — CLI build rejects unapproved spec (exit_code ≠ 0) |
| VAL-08 | Deploy gate — CLI ship rejects unapproved spec (exit_code ≠ 0) |
| VAL-09 | End-to-end fixture pipeline — scan→spec→build produces artifacts on disk |
| VAL-10 | Tracker round-trip — save_metrics then load_metrics returns exact values |

---

## Completion Roadmap

| Milestone | Effort | Impact |
|---|---|---|
| Fix `_normalize_gate` for live LLM outputs | 2h | Unblocks live pipeline |
| Implement auditor page fetch | 4h | Closes anti-hallucination gap |
| Fix `LIVE_SCANNERS["hn"] = None` | 5m | Eliminates latent registry bug |
| Fix `can_deploy` strict boolean | 15m | Closes type-safety gap |
| Wire `rich` or remove dependency | 30m | Cleaner dependency tree |
| Implement LLM-assisted spec writer | 4h | Produces useful PRD output |
| Add SQLite persistence | 8h | Aligns implementation with architecture |
| Implement real deployer (Vercel CLI) | 12h | Closes dry-run gap |
| Implement live traction tracker | 6h | Closes metrics gap |
| **Total to ~80/100** | **~37h** | |
