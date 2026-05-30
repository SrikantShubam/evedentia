# Evidentia — Next Pivot Work Orders (Week 1)

**For:** Codex 5.3xhigh
**Prepared from:** `NEXT_PIVOT.md` (2026-04-17)
**Scope:** Week 1 — reset. Delete drifted modules, fix critical bugs, add REFINE verdict. Does not implement anchors/clusterer (Week 2+, see `docs/next_pivot_v1_architecture.md`).
**Exit condition for each work order:** `pytest tests/validation/ -v` stays at `12 passed` (unless explicitly replaced in WO-7). Run after every work order.

---

## Guardrails (apply to every work order)

1. **Do not add new runtime dependencies.** Stdlib only: `urllib.request`, `json`, `os`, `pathlib`, `datetime`, `re`, `html`, `dataclasses`, `enum`.
2. **One work order at a time.** Do not speculatively fix issues not listed in the work order you are executing.
3. **Do not touch `tests/fixtures/` JSON.** Those are data contracts.
4. **Write a test for every new code path.** Place in the appropriate existing test file.
5. **Deletions are deliberate.** WO-1 deletes modules. Do not resurrect them — their contracts are dropped per `NEXT_PIVOT.md`.
6. **`tests/validation/test_validation_suite.py` is updated in WO-7 only.** Do not touch it in any other work order.
7. **Commit per work order** with message `[WO-N] <title>` so each step is reversible.

---

## Execution Order

```
WO-1 (delete drift) → WO-2 (registry fix) → WO-3 (auditor fetch)
    → WO-4 (classifier debug log) → WO-5 (structured JSON contract)
    → WO-6 (REFINE verdict in scoring) → WO-7 (validation suite update)
    → WO-8 (cli trim) → WO-9 (pyproject cleanup)
```

WO-1 must run first. Everything else depends on the reduced surface.

---

## WO-1 — Delete drifted modules

**Files to delete:**
- `src/evidentia/builder.py`
- `src/evidentia/deployer.py`
- `src/evidentia/tracker.py`
- `src/evidentia/spec_writer.py`
- `src/evidentia/server.py`

**Tests to delete:**
- `tests/unit/test_deployer.py`
- `tests/unit/test_spec_writer.py`
- Any test named `test_build_*`, `test_ship_*`, `test_track_*` inside `tests/acceptance/test_cli_artifacts.py` and `tests/acceptance/test_scan_pipeline.py` — delete those test functions only, not the files.

**Code to remove from `src/evidentia/cli.py`:**
- `build`, `ship`, `track`, `spec` subcommands and their helper functions.
- Any import from the deleted modules.
- Any CLI option group tied to the removed commands.

**Estimated effort:** 2h

### Definition of done
- `grep -r "from evidentia.builder" src/ tests/` returns no results.
- `grep -r "from evidentia.deployer" src/ tests/` returns no results.
- `grep -r "from evidentia.tracker" src/ tests/` returns no results.
- `grep -r "from evidentia.spec_writer" src/ tests/` returns no results.
- `grep -r "from evidentia.server" src/ tests/` returns no results.
- `python -m evidentia.cli --help` shows only: `scan`, `audit`, `classify`, `score`. No `spec/build/ship/track`.
- `pytest tests/ -v --ignore=tests/validation` runs without ImportError. Failures from removed tests are expected and acceptable; **validation suite is updated in WO-7**, so `pytest tests/validation/` is allowed to fail here and will be fixed in WO-7.

### New test to add
None in this WO. Tests are removed, not added.

---

## WO-2 — Fix `LIVE_SCANNERS["hn"] = None`

**File:** `src/evidentia/scanners/__init__.py`
**Estimated effort:** 5 min

### Problem
`LIVE_SCANNERS["hn"]` is `None`. See `REVIEW_REPORT.md` FP-03.

### Required change
```python
from evidentia.scanners.hn import scan_hn_fixture, scan_hn_live
from evidentia.scanners.reddit import scan_reddit_fixture, scan_reddit_live
from evidentia.scanners.github import scan_github_fixture, scan_github_live

LIVE_SCANNERS = {
    "hn": scan_hn_live,
    "reddit": scan_reddit_live,
    "github": scan_github_live,
}
```

### Definition of done
- `callable(LIVE_SCANNERS["hn"])` is True.
- `all(callable(fn) for fn in LIVE_SCANNERS.values())` is True.

### New test to add
In `tests/integration/test_multi_source_scan.py`:
```python
def test_live_scanners_registry_is_complete_and_callable():
    from evidentia.scanners import LIVE_SCANNERS
    assert set(LIVE_SCANNERS.keys()) == {"hn", "reddit", "github"}
    for source, fn in LIVE_SCANNERS.items():
        assert callable(fn), f"LIVE_SCANNERS['{source}'] not callable: {fn!r}"
```

---

## WO-3 — Real page fetch in auditor

**File:** `src/evidentia/auditor.py`
**Estimated effort:** 3h

### Problem
`verify_quote` is a substring check on scanner-returned text. When that text is the title, it verifies the title against itself. See `REVIEW_REPORT.md` FP-02.

### Required behavior
1. New function `_fetch_page_text(url: str, max_bytes: int = 51_200, timeout: float = 6.0) -> str | None`.
   - Uses `urllib.request` with a `User-Agent: evidentia/0.1` header.
   - Reads at most `max_bytes` bytes.
   - Returns decoded text (utf-8, errors='replace') or `None` on any exception.
   - Strips HTML tags with a stdlib-only helper (regex `<[^>]+>` replace → then `html.unescape`).
2. `verify_quote(candidate: dict) -> dict` must:
   - First try `_fetch_page_text(candidate["source_url"])`.
   - If fetch succeeds: check quote substring against fetched text (case-insensitive, whitespace-normalized). Tag `proof_level: "fetched"`.
   - If fetch fails: fall back to existing `source_text` check. Tag `proof_level: "in_memory"`.
   - If both fail: `verified: False`, `proof_level: "none"`, `discard_reason: "quote_not_verifiable"`.

### Definition of done
- `proof_level` key present on every auditor output.
- Existing validation tests VAL-04 and VAL-05 still pass (they use `source_text` path, which remains functional as `in_memory` fallback).
- New test covers the `fetched` path with a monkeypatched `_fetch_page_text`.

### New test to add
In `tests/unit/test_auditor.py`:
```python
def test_verify_quote_fetched_path(monkeypatch):
    from evidentia import auditor
    monkeypatch.setattr(auditor, "_fetch_page_text",
        lambda url, **kw: "some page with the verbatim quote inside")
    result = auditor.verify_quote({
        "source_url": "https://example.com/x",
        "verbatim_quote": "verbatim quote",
        "source_text": "unrelated"
    })
    assert result["verified"] is True
    assert result["proof_level"] == "fetched"

def test_verify_quote_in_memory_fallback(monkeypatch):
    from evidentia import auditor
    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url, **kw: None)
    result = auditor.verify_quote({
        "source_url": "https://example.com/x",
        "verbatim_quote": "present here",
        "source_text": "present here"
    })
    assert result["verified"] is True
    assert result["proof_level"] == "in_memory"

def test_verify_quote_unverifiable(monkeypatch):
    from evidentia import auditor
    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url, **kw: None)
    result = auditor.verify_quote({
        "source_url": "https://example.com/x",
        "verbatim_quote": "not anywhere",
        "source_text": "unrelated"
    })
    assert result["verified"] is False
    assert result["proof_level"] == "none"
    assert result["discard_reason"] == "quote_not_verifiable"
```

---

## WO-4 — Classifier raw-response debug log

**File:** `src/evidentia/classifier.py`
**Estimated effort:** 1h

### Problem
`REVIEW_REPORT.md` FP-01: 100% HOLD on live data. Cannot tune `_normalize_gate` without seeing what the LLM actually returns.

### Required behavior
1. Add optional parameter `debug_log_path: str | None = None` to `classify_candidate`.
2. When set, append one JSON line per call with:
   ```json
   {"timestamp": "...", "provider": "...", "model": "...",
    "prompt": "...", "raw_response": {...}, "normalized": {...}}
   ```
3. Add CLI flag `--debug-llm-log PATH` on `scan` that plumbs through to `classify_candidate`.
4. No behavior change when flag is absent.

### Definition of done
- `python -m evidentia.cli scan --domain X --debug-llm-log out.jsonl` produces `out.jsonl` with valid JSON per line.
- Unit test uses a fake provider, asserts log file has one line with expected keys.

### New test to add
In `tests/unit/test_classifier.py`:
```python
def test_classify_candidate_debug_log(tmp_path):
    from evidentia.classifier import classify_candidate
    class FakeProvider:
        def generate_json(self, prompt, model):
            return {"willingness_to_pay": "pass", "distribution_channel": "pass",
                    "data_feasibility": "pass", "competition_gap": 0.7,
                    "buildability": 0.8, "reachability_strength": 0.6}
    log_path = tmp_path / "log.jsonl"
    classify_candidate({"title": "x", "verbatim_quote": "y", "source_text": "z"},
                       provider=FakeProvider(), model="fake",
                       debug_log_path=str(log_path))
    import json
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert "raw_response" in entry and "normalized" in entry and "prompt" in entry
```

---

## WO-5 — Structured JSON schema contract in classifier

**File:** `src/evidentia/classifier.py`
**Estimated effort:** 2h
**Depends on:** WO-4

### Problem
Current prompt asks the LLM nicely. Real LLM outputs vary. Enforce shape with validation + one retry with a corrective prompt before falling through to the provider chain.

### Required behavior
1. Define constant `REQUIRED_KEYS = {"willingness_to_pay", "distribution_channel", "data_feasibility", "competition_gap", "buildability", "reachability_strength"}`.
2. New helper `_validate_classification_shape(raw: dict) -> list[str]` returns list of violation strings (missing keys, wrong types, out-of-range floats).
3. In `classify_candidate`, after `generate_json` returns: if violations exist, retry **once** with an amended prompt appending:
   `"Your previous response was invalid: <violations>. Return ONLY the JSON object with exact keys and types specified."`
4. If the retry still violates, log it (via WO-4 path) and **advance to the next provider in the chain** rather than returning mangled data.
5. If all providers exhausted, raise `ClassifierError(message, last_raw_response=...)`.

### Definition of done
- New `ClassifierError` class in `classifier.py`.
- `_validate_classification_shape` returns empty list for a good dict, non-empty list for bad ones.
- Retry logic exercised by a test with a stub provider that returns bad JSON first, good JSON second.

### New test to add
In `tests/unit/test_classifier.py`:
```python
def test_classifier_retries_on_bad_shape():
    from evidentia.classifier import classify_candidate
    calls = {"n": 0}
    class FlakeyProvider:
        def generate_json(self, prompt, model):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"willingness_to_pay": "yes"}  # missing keys
            return {"willingness_to_pay": "pass", "distribution_channel": "pass",
                    "data_feasibility": "pass", "competition_gap": 0.5,
                    "buildability": 0.5, "reachability_strength": 0.5}
    result = classify_candidate({"title": "t", "verbatim_quote": "q", "source_text": "s"},
                                provider=FlakeyProvider(), model="fake")
    assert calls["n"] == 2
    assert result["willingness_to_pay"] == "pass"

def test_classifier_raises_after_retries_exhausted():
    from evidentia.classifier import classify_candidate, ClassifierError
    class BadProvider:
        def generate_json(self, prompt, model):
            return {"nope": "bad"}
    import pytest
    with pytest.raises(ClassifierError):
        classify_candidate({"title": "t", "verbatim_quote": "q", "source_text": "s"},
                           provider_chain=[(BadProvider(), "m")])
```

---

## WO-6 — REFINE verdict in scoring

**File:** `src/evidentia/scoring.py`, `src/evidentia/models.py`
**Estimated effort:** 4h

### Problem
`NEXT_PIVOT.md` section 2 mandates three verdicts: `KILL`, `PURSUE`, `REFINE`. Current code returns `SKIP`/`HOLD`/`PURSUE` and has no REFINE.

### Required behavior
1. In `models.py`, add enum:
   ```python
   class Verdict(str, Enum):
       KILL = "KILL"
       REFINE = "REFINE"
       PURSUE = "PURSUE"
   ```
2. In `scoring.py`, `score_opportunity` must return one of those three values in `verdict` (and keep the old `gate_verdict` field for backcompat while other code transitions).
3. Mapping rule for Week 1 (single-signal scoring; slice-level comes in Week 2):
   - All three hard gates `pass` AND min of heuristic scores ≥ 0.4 → `PURSUE`
   - All three hard gates `pass` AND min of heuristic scores < 0.4 → `REFINE`
   - Any hard gate `fail` AND all heuristics = 0 (model gave up) → `KILL`
   - Any hard gate `fail` otherwise → `REFINE`
4. `score_opportunity` output must now include:
   - `verdict`: one of KILL/REFINE/PURSUE
   - `refine_reason`: str or null — which condition triggered REFINE
   - `next_test`: str or null — placeholder `"TODO: slice-level REFINE handler, see NEXT_PIVOT.md"` for now
5. No caller of `score_opportunity` in `cli.py` should depend on the literal string `HOLD`. Grep and replace where needed.

### Definition of done
- `grep -n '"HOLD"' src/` returns no hits.
- `score_opportunity` returns only KILL/REFINE/PURSUE.
- Unit tests for each of the four conditions.

### New test to add
In `tests/unit/test_scoring.py`:
```python
def _base_opp(**overrides):
    base = {
        "cluster_id": "c1", "source_url": "https://x/y", "timestamp": "2026-04-01T00:00:00Z",
        "willingness_to_pay": "pass", "distribution_channel": "pass", "data_feasibility": "pass",
        "competition_gap": 0.7, "buildability": 0.7, "reachability_strength": 0.7,
        "verified": True,
    }
    base.update(overrides)
    return base

def test_scoring_verdict_pursue():
    from evidentia.scoring import score_opportunity
    out = score_opportunity(_base_opp())
    assert out["verdict"] == "PURSUE"

def test_scoring_verdict_refine_weak_heuristics():
    from evidentia.scoring import score_opportunity
    out = score_opportunity(_base_opp(competition_gap=0.1, buildability=0.2, reachability_strength=0.3))
    assert out["verdict"] == "REFINE"
    assert out["refine_reason"] is not None

def test_scoring_verdict_refine_gate_fail_soft():
    from evidentia.scoring import score_opportunity
    out = score_opportunity(_base_opp(willingness_to_pay="fail"))
    assert out["verdict"] == "REFINE"

def test_scoring_verdict_kill_total_fail():
    from evidentia.scoring import score_opportunity
    out = score_opportunity(_base_opp(
        willingness_to_pay="fail", distribution_channel="fail", data_feasibility="fail",
        competition_gap=0.0, buildability=0.0, reachability_strength=0.0))
    assert out["verdict"] == "KILL"
```

---

## WO-7 — Update validation suite for new contract

**File:** `tests/validation/test_validation_suite.py`
**Estimated effort:** 2h
**Depends on:** WO-1 through WO-6

### Changes
1. Delete VAL-06 (spec writer), VAL-07 (build approval), VAL-08 (deploy approval), VAL-09 (e2e incl. build), VAL-10 (tracker). Those modules are gone.
2. VAL-02 (three parametrized cases): expected verdict changes from `HOLD` to `REFINE` for single-gate failures.
3. VAL-01: expected `verdict == "PURSUE"` remains.
4. Add VAL-11: auditor `proof_level` is always one of `{"fetched", "in_memory", "none"}`.
5. Add VAL-12: `score_opportunity` never returns `"HOLD"` or `"SKIP"` — enforce enum.

### Definition of done
- Renumbered validation suite passes: `pytest tests/validation/ -v` → 5+ green, 0 failing.
- New exit condition is documented at top of file.
- Header comment at top of file updated to list new 3-verdict contract.

---

## WO-8 — CLI trim

**File:** `src/evidentia/cli.py`
**Estimated effort:** 1h
**Depends on:** WO-1, WO-6

### Changes
1. Command surface is now: `scan`, `audit`, `classify`, `score`. Nothing else.
2. `scan` gains `--debug-llm-log PATH` (from WO-4).
3. Remove all HOLD references in logging; use the new verdict enum strings.
4. `--help` text updated: "Evidentia — harsh critic for demand-signal ideas. Verdicts: KILL / REFINE / PURSUE."

### Definition of done
- `python -m evidentia.cli --help` output matches description above.
- No reference to `build`, `ship`, `track`, `spec` in CLI help or code.

### No new test required.

---

## WO-9 — `pyproject.toml` cleanup

**File:** `pyproject.toml`
**Estimated effort:** 15 min

### Changes
1. Remove `rich` from `[project.dependencies]` (it was never imported; see FP-07).
2. Remove any dep that was only used by the deleted modules (check imports of deleted files: `vercel`, `flask`, anything web-serving).
3. Add a one-line comment at top referencing `NEXT_PIVOT.md` so future readers know the scope is intentional.

### Definition of done
- `pip install -e .` in a clean venv succeeds.
- `python -m evidentia.cli --help` runs.
- All tests pass.

---

## Post-Week-1 checkpoint

After WO-1 through WO-9 complete:
1. `pytest tests/ -v` all green.
2. Manual command: `python -m evidentia.cli scan --domain "expense tracking" --max-results 3 --debug-llm-log tmp/debug.jsonl`
3. Inspect `tmp/debug.jsonl`. If any classification returned malformed JSON, note the pattern — this is the data needed to tune `_normalize_gate` in a follow-up WO.
4. Merge to main. Tag `v0.2.0-niche-critic-reset`.
5. Week 2 starts: build `anchor.py`, `scanners/reviews.py`, `clusterer.py` per `docs/next_pivot_v1_architecture.md`.
