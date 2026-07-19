# Evidentia — Codex Work Orders

**For:** Codex 5.3xhigh  
**Prepared by:** Review pass on commit a1fcdf1  
**Validation suite:** `tests/validation/test_validation_suite.py` (12 cases, all green)  
**Exit condition for each work order:** `pytest tests/validation/ -v` must stay at `12 passed`. Run after every work order.

---

## Guardrails (apply to every work order)

1. **Do not change public function signatures.** The pipeline is wired through the CLI and 30 test files. Adding a parameter is allowed only if it has a default that preserves existing call sites. Removing or reordering parameters is forbidden.
2. **Do not modify `tests/validation/test_validation_suite.py`.** That file is the acceptance contract. If a work order makes a test fail, the implementation is wrong, not the test.
3. **Do not add new runtime dependencies** without updating `pyproject.toml` and checking that the dep is available on PyPI. The only stdlib modules are `urllib.request`, `json`, `os`, `pathlib`, `datetime`. All of these are already used — they are safe to import.
4. **One work order at a time.** Do not speculatively fix issues not listed in the work order you are executing.
5. **Do not touch `outputs/` or any fixture JSON files** in `tests/fixtures/`. Those are test data contracts.
6. **Write tests for every new code path** you add. Place them in the appropriate existing test file (unit/integration/acceptance). Do not create new test files unless instructed.

---

## Execution Order

Execute work orders in this sequence. Each one either unblocks the next or is independent.

```
WO-1 → WO-2 → WO-3  (must run in order: registry fix enables live scan; auditor fetch uses WO-3's urllib pattern)
WO-4                  (independent: test guard, no production code change)
WO-5 → WO-6          (classifier prompt fix first, then normalization expansion)
WO-7                  (independent: spec writer enrichment)
WO-8                  (independent: scoring weights extraction)
WO-9                  (independent: dependency cleanup)
```

---

## WO-1 — Fix `LIVE_SCANNERS["hn"] = None`

**File:** `src/evidentia/scanners/__init__.py`  
**Lines to change:** 14  
**Estimated effort:** 5 minutes

### Problem
`LIVE_SCANNERS["hn"]` is `None`. The CLI bypasses this with a direct import, but any code iterating the registry will silently fail or crash.

### Current code (`src/evidentia/scanners/__init__.py`)
```python
from evidentia.scanners.hn import scan_hn_fixture
...
LIVE_SCANNERS = {
    "github": scan_github_live,
    "hn": None,          # ← bug
    "reddit": scan_reddit_live,
}
```

### Required change
```python
from evidentia.scanners.hn import scan_hn_fixture, scan_hn_live   # add scan_hn_live
...
LIVE_SCANNERS = {
    "github": scan_github_live,
    "hn": scan_hn_live,   # ← fix
    "reddit": scan_reddit_live,
}
```

### Definition of done
- `LIVE_SCANNERS["hn"]` is callable (`callable(LIVE_SCANNERS["hn"]) is True`).
- All values in `LIVE_SCANNERS` are callable.
- `pytest tests/validation/ -v` → 12 passed.

### New test to add
In `tests/integration/test_multi_source_scan.py`, add:
```python
def test_live_scanners_registry_is_complete_and_callable():
    from evidentia.scanners import LIVE_SCANNERS
    for source, fn in LIVE_SCANNERS.items():
        assert callable(fn), f"LIVE_SCANNERS['{source}'] is not callable — got {fn!r}"
```

---

## WO-2 — Fix `can_deploy` strict boolean check

**File:** `src/evidentia/deployer.py`  
**Lines to change:** 7–8  
**Estimated effort:** 10 minutes

### Problem
`can_deploy(spec: dict)` calls `spec.get("approved")` and returns whatever is stored. A spec with `approved: "true"` (string) would return the string, which is truthy, bypassing the gate.

### Current code (`src/evidentia/deployer.py:6-8`)
```python
def can_deploy(spec: ProductSpec | dict) -> bool:
    approved = spec.approved if isinstance(spec, ProductSpec) else spec.get("approved")
    return approved is True
```

Wait — the current code already ends with `return approved is True`, which IS the correct strict check. **Re-read before touching.** 

**Verify first:** Run `python -c "from evidentia.deployer import can_deploy; print(can_deploy({'approved': 'true'}))"` — if it prints `False`, this work order is already resolved and should be skipped.

If the output is `True`, apply this fix:
```python
def can_deploy(spec: ProductSpec | dict) -> bool:
    if isinstance(spec, ProductSpec):
        return spec.approved is True
    return spec.get("approved") is True
```

### Definition of done
- `can_deploy({"approved": "true"})` returns `False`.
- `can_deploy({"approved": True})` returns `True`.
- `can_deploy(ProductSpec(..., approved=True, ...))` returns `True`.
- `pytest tests/validation/ -v` → 12 passed.

### New test to add
In `tests/unit/test_deployer.py`, add:
```python
def test_can_deploy_rejects_string_true():
    assert can_deploy({"approved": "true"}) is False

def test_can_deploy_rejects_integer_one():
    assert can_deploy({"approved": 1}) is False
```

---

## WO-3 — Implement page fetching in auditor

**File:** `src/evidentia/auditor.py`  
**Estimated effort:** 2–3 hours

### Problem
`verify_quote` checks `verbatim_quote in source_text` where `source_text` comes from the scanner's API payload (often the HN title or Reddit selftext) — not the actual page at `source_url`. For items where `source_text` falls back to the title, the function verifies the title against itself. This gives false `verified: True` confidence.

### Required behaviour
1. Attempt to fetch `source_url` with `urllib.request` (already used in `providers.py` — reuse the same pattern).
2. If fetch succeeds, check `verbatim_quote` against the fetched page text (first 50 KB only — truncate to avoid memory issues on large pages).
3. If fetch fails (network error, timeout, non-200 status), fall back to checking against the provided `source_text` and tag the result with `proof_level: "in-memory"`.
4. If fetch succeeds, tag the result with `proof_level: "fetched"`.
5. The function signature must not change: `verify_quote(source_text, source_url, verbatim_quote) -> dict`.

### Required return shape
```python
# Success via fetched page
{"verified": True, "source_url": "...", "proof_level": "fetched"}

# Success via in-memory fallback
{"verified": True, "source_url": "...", "proof_level": "in-memory"}

# Failure — quote not found anywhere
{"verified": False, "source_url": "...", "reason": "quote_not_found", "proof_level": "fetched" | "in-memory"}
```

### Implementation skeleton
```python
import urllib.request
import urllib.error

_FETCH_TIMEOUT = 10       # seconds
_MAX_BYTES = 50_000       # 50 KB


def _fetch_page_text(url: str) -> tuple[str, str]:
    """Returns (text, proof_level). proof_level is 'fetched' or 'in-memory'."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "evidentia-auditor/0.1"})
        with urllib.request.urlopen(req, timeout=_FETCH_TIMEOUT) as resp:
            if resp.status != 200:
                raise ValueError(f"non-200 status: {resp.status}")
            raw = resp.read(_MAX_BYTES)
            return raw.decode("utf-8", errors="replace"), "fetched"
    except Exception:
        return "", "in-memory"   # caller must fall back to source_text


def verify_quote(source_text: str, source_url: str, verbatim_quote: str) -> dict:
    page_text, proof_level = _fetch_page_text(source_url)
    text_to_check = page_text if page_text else source_text
    if verbatim_quote in text_to_check:
        return {"verified": True, "source_url": source_url, "proof_level": proof_level}
    return {"verified": False, "source_url": source_url, "reason": "quote_not_found", "proof_level": proof_level}
```

### Definition of done
- `verify_quote` still passes VAL-04 and VAL-05 (they use in-memory `source_text`, no URL fetch — ensure fallback works).
- A new unit test verifies that if `_fetch_page_text` is monkeypatched to return `("", "in-memory")`, the function falls back to `source_text` correctly.
- A new unit test verifies that if `_fetch_page_text` returns fetched text containing the quote, `proof_level` is `"fetched"`.
- `pytest tests/validation/ -v` → 12 passed.

### New tests to add
In `tests/unit/test_auditor.py`, add:
```python
def test_verify_quote_fetched_proof_level(monkeypatch):
    from evidentia import auditor
    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url: ("the real page text with the quote here", "fetched"))
    result = auditor.verify_quote("fallback text", "https://example.com", "the real page text")
    assert result["verified"] is True
    assert result["proof_level"] == "fetched"

def test_verify_quote_falls_back_to_source_text_on_fetch_failure(monkeypatch):
    from evidentia import auditor
    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url: ("", "in-memory"))
    result = auditor.verify_quote("the source text has the quote", "https://example.com", "has the quote")
    assert result["verified"] is True
    assert result["proof_level"] == "in-memory"
```

---

## WO-4 — Guard `test_external_reuse.py` against missing env files

**File:** `tests/unit/test_external_reuse.py`  
**Estimated effort:** 15 minutes

### Problem
All four tests in this file read API keys from `../codex/.env` and `../kimi/.env`. They fail with `FileNotFoundError` or key assertion errors on any machine without those sibling directories. The file has no `pytest.mark.skip` or `pytest.mark.live` guard.

### Required change
Add a module-level skip condition at the top of the file, after the imports:

```python
from pathlib import Path
import pytest

_CODEX_ENV = Path(__file__).parent.parent.parent.parent / "codex" / ".env"
_KIMI_ENV  = Path(__file__).parent.parent.parent.parent / "kimi"  / ".env"

pytestmark = pytest.mark.skipif(
    not (_CODEX_ENV.exists() and _KIMI_ENV.exists()),
    reason="sibling codex/.env and kimi/.env not present — skipping external reuse tests",
)
```

**Do not change any of the four existing test functions in this file.**

### Definition of done
- `pytest tests/unit/test_external_reuse.py -v` on a machine without `../codex/.env` prints `4 skipped` (not `4 errors`).
- On a machine that has both env files, the tests continue to run and pass.
- `pytest tests/validation/ -v` → 12 passed.

---

## WO-5 — Harden classifier prompt for strict gate vocabulary

**File:** `src/evidentia/classifier.py`  
**Function:** `_classification_prompt`  
**Estimated effort:** 30 minutes

### Problem
The prompt instructs: `"For gates, use only 'pass' or 'fail'."` but this sentence is buried in a paragraph with other instructions. Real LLM outputs from NVIDIA llama-3.3-nemotron-super-49b return elaborated JSON like:

```json
{"willingness_to_pay": {"verdict": "fail", "reasoning": "..."}}
```

or label variants not covered by `_normalize_gate` (e.g. `"insufficient evidence"`, `"unclear"`, `"n/a"`). The current `_normalize_gate` defaults anything unknown to `"fail"`, so ambiguous outputs become hard gate failures.

### Required change to `_classification_prompt`

Replace the current prompt body with one that:
1. Leads with the output contract before any context (models attend more to early tokens).
2. States the gate vocabulary as the **only** acceptable values using explicit enumeration.
3. Forbids nested JSON, prose keys, or explanation fields.
4. Provides a concrete example of the expected output.

```python
def _classification_prompt(candidate: dict) -> str:
    return (
        "You are a demand-signal classifier. Return ONLY a JSON object. No markdown, no explanation, no extra keys.\n\n"
        "REQUIRED OUTPUT FORMAT (copy this structure exactly):\n"
        '{"willingness_to_pay": "pass", "distribution_channel": "pass", "data_feasibility": "pass", '
        '"competition_gap": 0.8, "buildability": 0.7, "reachability_strength": 0.6}\n\n'
        "RULES:\n"
        "- willingness_to_pay, distribution_channel, data_feasibility: MUST be the string \"pass\" or the string \"fail\". No other values.\n"
        "- competition_gap, buildability, reachability_strength: MUST be a number between 0.0 and 1.0.\n"
        "- Do NOT add extra keys, nested objects, or explanation fields.\n\n"
        "CLASSIFY THIS SIGNAL:\n"
        f"Title: {candidate['title']}\n"
        f"Quote: {candidate['verbatim_quote']}\n"
        f"Source text: {candidate.get('source_text', '')[:1000]}\n\n"
        "willingness_to_pay = pass if the signal contains explicit spend intent, pricing discussion, "
        "budget mention, or stated willingness to pay. fail if absent.\n"
        "distribution_channel = pass if there is a clear reachable audience (community, platform, job title, mailing list). fail if absent.\n"
        "data_feasibility = pass if the required data is public or accessible via API. fail if proprietary or unavailable.\n"
    )
```

### Definition of done
- The prompt string contains `"MUST be the string"` and `"No other values"`.
- The source text passed to the prompt is capped at 1000 characters (prevents token overflow on long Reddit posts).
- Existing `test_classifier.py` tests still pass.
- `pytest tests/validation/ -v` → 12 passed.

### New test to add
In `tests/unit/test_classifier.py`, add:
```python
def test_classification_prompt_caps_source_text():
    from evidentia.classifier import _classification_prompt
    long_candidate = {
        "title": "test",
        "verbatim_quote": "quote",
        "source_text": "x" * 5000,
    }
    prompt = _classification_prompt(long_candidate)
    # source_text must be truncated to 1000 chars in the prompt
    assert prompt.count("x") <= 1000
```

---

## WO-6 — Expand `_normalize_gate` to cover ambiguous LLM labels

**File:** `src/evidentia/classifier.py`  
**Function:** `_normalize_gate`  
**Estimated effort:** 30 minutes  
**Prerequisite:** WO-5 must be merged first.

### Problem
`_normalize_gate` currently maps: `{"pass", "true", "yes", "high", "medium", "moderate", "direct"}` → `"pass"`. Labels observed in live LLM output that should map to `"pass"` but currently fall to `"fail"`:

- `"strong"`, `"clear"`, `"evident"`, `"present"`, `"confirmed"`, `"1"`, `"1.0"`, `"explicit"`

Labels that correctly default to `"fail"` but are not tested:
- `"insufficient evidence"`, `"unclear"`, `"n/a"`, `"none"`, `"low"`, `"no"`

### Required change
```python
def _normalize_gate(value) -> str:
    normalized = str(value).strip().lower()
    _PASS_LABELS = {
        "pass", "true", "yes", "1", "1.0",
        "high", "medium", "moderate", "direct",
        "strong", "clear", "evident", "present", "confirmed", "explicit",
    }
    if normalized in _PASS_LABELS:
        return "pass"
    # numeric strings: "0.7" and above → pass
    try:
        if float(normalized) >= 0.5:
            return "pass"
    except ValueError:
        pass
    return "fail"
```

### Definition of done
- `_normalize_gate("strong")` → `"pass"`
- `_normalize_gate("confirmed")` → `"pass"`
- `_normalize_gate("0.7")` → `"pass"`
- `_normalize_gate("0.3")` → `"fail"`
- `_normalize_gate("insufficient evidence")` → `"fail"`
- All existing `test_classifier.py` tests still pass.
- `pytest tests/validation/ -v` → 12 passed.

### New tests to add
In `tests/unit/test_classifier.py`, add:
```python
@pytest.mark.parametrize("label,expected", [
    ("strong", "pass"),
    ("confirmed", "pass"),
    ("explicit", "pass"),
    ("0.7", "pass"),
    ("0.3", "fail"),
    ("insufficient evidence", "fail"),
    ("n/a", "fail"),
    ("none", "fail"),
])
def test_normalize_gate_extended_labels(label, expected):
    from evidentia.classifier import _normalize_gate
    assert _normalize_gate(label) == expected
```

---

## WO-7 — Enrich spec writer with LLM-assisted PRD sections

**File:** `src/evidentia/spec_writer.py`  
**Estimated effort:** 3–4 hours

### Problem
`write_spec` produces a `ProductSpec` with only `opportunity_id`, `title`, `approved=False`, and `sources`. It generates no product requirements, target user description, or feature list. A human reviewer gets no PRD — they must write it from scratch.

### Required behaviour
1. Add an optional `provider` parameter to `write_spec`. If `None`, select via `choose_llm_provider(load_external_provider_env())` — the same pattern used in `classifier.py`.
2. Call the provider to generate a JSON block with these three fields:
   - `target_user`: one sentence describing the user persona.
   - `core_problem`: one sentence describing the pain.
   - `wedge_feature`: one sentence describing the smallest useful feature to build.
3. Attach this block as optional fields on a new `prd: dict | None` key in the JSON output. **Do NOT add `prd` to the `ProductSpec` Pydantic model** — serialize it separately in the output dict.
4. If the LLM call fails for any reason, proceed without PRD sections (`prd: null`) — do not raise.

### Updated function signature
```python
def write_spec(opportunity: dict, provider=None, model: str | None = None) -> ProductSpec:
```

The returned `ProductSpec` is unchanged. The CLI `spec` command must also write the `prd` sidecar into the JSON output file. Update `cli.py:spec` command:

```python
# in cli.py, spec command:
spec_payload = write_spec(opportunity)
output_dict = spec_payload.model_dump(mode="json")
prd_sections = _generate_prd(opportunity)   # new helper, may return None
output_dict["prd"] = prd_sections
_write_json(output_path, output_dict)
```

`_generate_prd` is a private function in `cli.py` (not in `spec_writer.py`) that wraps the LLM call with a try/except returning `None` on failure.

### PRD prompt
```python
def _prd_prompt(opportunity: dict) -> str:
    signals = opportunity.get("verified_signals", [])
    quotes = "\n".join(f"- {s.get('verbatim_quote', '')}" for s in signals[:3])
    return (
        "You are a product strategist. Based on the demand signals below, return ONLY a JSON object.\n"
        "REQUIRED OUTPUT:\n"
        '{"target_user": "...", "core_problem": "...", "wedge_feature": "..."}\n\n'
        f"Opportunity: {opportunity.get('title', '')}\n"
        f"Demand signals:\n{quotes}\n"
        "Each value must be exactly one sentence. No extra keys."
    )
```

### Definition of done
- `write_spec(opportunity)` still returns a valid `ProductSpec` (VAL-06 still passes).
- When a mock provider is injected, the CLI `spec` command writes `prd` as a top-level key in the output JSON alongside the spec fields.
- When no provider is available (LLM raises), `prd` key is present but `null`.
- `pytest tests/validation/ -v` → 12 passed.

### New tests to add
In `tests/acceptance/test_cli_artifacts.py`, add a test that:
1. Invokes the `spec` CLI command with a mock LLM provider injected (via monkeypatching `cli._generate_prd`).
2. Asserts the output JSON has a `prd` key.
3. Invokes again with `_generate_prd` raising — asserts `prd` is `null` (not missing).

---

## WO-8 — Extract scoring weights to named constants

**File:** `src/evidentia/scoring.py`  
**Estimated effort:** 20 minutes

### Problem
The scoring formula `competition_gap * 0.4 + buildability * 0.3 + reachability_strength * 0.3` is a literal expression. The weights cannot be overridden without editing source, and the formula is not self-documenting.

### Required change
Add module-level constants before `score_opportunity`:

```python
WEIGHT_COMPETITION_GAP     = 0.4
WEIGHT_BUILDABILITY        = 0.3
WEIGHT_REACHABILITY        = 0.3

assert abs(WEIGHT_COMPETITION_GAP + WEIGHT_BUILDABILITY + WEIGHT_REACHABILITY - 1.0) < 1e-9, \
    "scoring weights must sum to 1.0"
```

Replace the literal in `score_opportunity`:

```python
score = (
    opportunity.get("competition_gap", 0) * WEIGHT_COMPETITION_GAP
    + opportunity.get("buildability", 0) * WEIGHT_BUILDABILITY
    + opportunity.get("reachability_strength", 0) * WEIGHT_REACHABILITY
)
```

### Definition of done
- `from evidentia.scoring import WEIGHT_COMPETITION_GAP` works without error.
- The assert fires if weights are edited to not sum to 1.0.
- `pytest tests/validation/ -v` → 12 passed.

---

## WO-9 — Wire or remove `rich` dependency

**File:** `pyproject.toml`, `src/evidentia/cli.py`  
**Estimated effort:** 30 minutes

### Problem
`rich >= 13.7, < 14` is a runtime dependency but no source file imports it. It is dead weight in the install.

### Decision: wire it up (do not remove)
Replace all `click.echo(...)` calls in `cli.py` that print the output path confirmation with `rich` Console output. This gives users visual feedback and justifies the dependency.

### Required change in `cli.py`
```python
from rich.console import Console

_console = Console()
```

Replace these four `click.echo(output_path)` / `click.echo(output_dir)` calls at the end of each command with:
```python
_console.print(f"[green]✓[/green] {output_path}")
```

**Do NOT replace `click.echo(json.dumps(payload))` in the `track` command** — that output is machine-readable and must remain plain stdout.

### Definition of done
- `from rich.console import Console` in `cli.py` does not raise on import.
- `rich` is still in `[project.dependencies]` in `pyproject.toml`.
- `click.echo(output_path)` is removed from scan/spec/build/ship commands.
- The `track` command still emits plain JSON to stdout (no Rich markup).
- `pytest tests/validation/ -v` → 12 passed.

---

## Completion Gate

After all work orders are applied, run the full suite:

```bash
pytest tests/ -v --ignore=tests/unit/test_external_reuse.py -q
```

Expected outcome: all tests pass. If `test_external_reuse.py` is skipped via the WO-4 guard, that is correct — 0 failures, not 4 errors.

Then run the validation suite one final time as the release gate:

```bash
pytest tests/validation/ -v
```

**Required:** `12 passed, 0 failed, 0 errors`.

---

## Schema Reference

### `score_opportunity(opportunity: dict) -> dict` — return keys
| Key | Type | Values |
|---|---|---|
| `verdict` | str | `"PURSUE"` or `"HOLD"` |
| `gate_verdict` | str | same as `verdict` (alias) |
| `heuristic_score` | float | `[0.0, 1.0]` |
| `freshness_factor` | float | `[0.0, 1.0]` |
| `final_score` | float | `[0.0, 1.0]` |
| `score` | float | same as `final_score` |

**Note:** `score_opportunity` does NOT preserve input fields. The caller must merge: `{**opportunity, **score_opportunity(opportunity)}`. This is how `cli._candidate_to_opportunity` works at line 78.

### `load_metrics(path: str) -> dict` — return shape
```json
{
  "status": "ok",
  "proof_level": "unspecified",
  "metrics": {"visits": 0, "signups": 0, "revenue_proxy": 0},
  "missing_fields": []
}
```
Metrics are nested under `"metrics"` — not at the top level.

### `verify_quote(...) -> dict` — return shape (after WO-3)
```json
{"verified": true,  "source_url": "...", "proof_level": "fetched" | "in-memory"}
{"verified": false, "source_url": "...", "reason": "quote_not_found", "proof_level": "fetched" | "in-memory"}
```
