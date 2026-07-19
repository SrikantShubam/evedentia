# Evidentia — Scan Quality Work Orders
**Target**: Fix zero-PURSUE live scan for real queries like "expense tracking"
**Exit condition**: `pytest tests/validation/ -v` still 12 passed, plus new WO tests; manual scan of "expense tracking" produces ≥1 PURSUE.
**Model**: Codex 5.3xhigh
**Execution order**: WO-1 → WO-2 → WO-3 (sequential, each depends on prior); WO-4, WO-5 independent; WO-6 after WO-1.

---

## Guardrails

1. **Never break the existing 12 validation tests** — run `pytest tests/validation/ -v` after every WO and confirm 12 passed before committing.
2. **No new external dependencies** — use only stdlib (`html`, `re`, `urllib`) for HTML decoding.
3. **Do not change the hard gate logic in `scoring.py`** — gates must remain binary pass/fail.
4. **Do not remove any existing function signatures** — only add parameters or change internals.
5. **All new test functions go in `tests/validation/test_scan_quality.py`** (new file).

---

## Schema Reference (do not change these contracts)

```python
# classifier.py: classify_candidate(candidate) → dict
# Returns candidate dict merged with:
{
  "willingness_to_pay": "pass" | "fail",
  "distribution_channel": "pass" | "fail",
  "data_feasibility": "pass" | "fail",
  "competition_gap": float,   # 0.0–1.0
  "buildability": float,      # 0.0–1.0
  "reachability_strength": float,  # 0.0–1.0
}

# scoring.py: score_opportunity(opportunity) → dict
# If any gate != "pass": {"verdict": "HOLD", "gate_verdict": "HOLD", "score": 0.0, ...}
# Else:                  {"verdict": "PURSUE", "gate_verdict": "PURSUE", "score": float, ...}
```

---

## WO-1 — Fix classifier prompt: remove example values from numeric fields

**File**: `src/evidentia/classifier.py`
**Function**: `_classification_prompt`
**Problem (F1)**: The prompt shows literal numbers in the example output format:
```
{"willingness_to_pay": "pass", "distribution_channel": "pass", "data_feasibility": "pass",
"competition_gap": 0.8, "buildability": 0.7, "reachability_strength": 0.6}
```
LLMs anchor to example values and echo them instead of reasoning. Result: every item gets
0.80/0.70/0.60 regardless of content.

**Fix**: Replace the example line with placeholder tokens that make clear the values must be inferred.
Also add explicit classifier perspective: score from the POV of a BUYER expressing demand, not a builder announcing supply.

**Exact replacement in `_classification_prompt`**:

Replace this block:
```python
        "REQUIRED OUTPUT FORMAT (copy this structure):\n"
        '{"willingness_to_pay": "pass", "distribution_channel": "pass", "data_feasibility": "pass", '
        '"competition_gap": 0.8, "buildability": 0.7, "reachability_strength": 0.6}\n\n'
        "RULES:\n"
        "- willingness_to_pay, distribution_channel, data_feasibility: MUST be the string \"pass\" or the string \"fail\". No other values.\n"
        "- competition_gap, buildability, reachability_strength: MUST be a number between 0.0 and 1.0.\n"
        "- Do NOT add additional keys, nested objects, or reasoning fields.\n\n"
```

With this block:
```python
        "REQUIRED OUTPUT FORMAT — fill in your assessed values, do not copy these placeholders:\n"
        '{"willingness_to_pay": "<pass|fail>", "distribution_channel": "<pass|fail>", "data_feasibility": "<pass|fail>", '
        '"competition_gap": <0.0-1.0>, "buildability": <0.0-1.0>, "reachability_strength": <0.0-1.0>}\n\n'
        "RULES:\n"
        "- willingness_to_pay, distribution_channel, data_feasibility: MUST be the string \"pass\" or the string \"fail\". No other values.\n"
        "- competition_gap, buildability, reachability_strength: MUST be a number between 0.0 and 1.0. Assess from the signal text — do NOT use 0.8, 0.7, or 0.6 as defaults.\n"
        "- Do NOT add additional keys, nested objects, or reasoning fields.\n\n"
        "PERSPECTIVE: Classify from the viewpoint of a BUYER expressing unmet demand. "
        "A 'Show HN: I built X' post is a builder signal, not a buyer signal — mark willingness_to_pay=fail unless buyers respond with explicit spend intent in the text.\n\n"
```

**Definition of done**: The prompt string no longer contains literal `0.8`, `0.7`, or `0.6` as numeric values.

**New test** (add to `tests/validation/test_scan_quality.py`):
```python
from evidentia.classifier import _classification_prompt

def test_prompt_no_example_numeric_defaults():
    candidate = {"title": "test", "verbatim_quote": "test", "source_text": "test"}
    prompt = _classification_prompt(candidate)
    # The prompt must not contain the exact example values that cause LLM anchoring
    assert "0.8," not in prompt
    assert "0.7," not in prompt
    assert "0.6}" not in prompt
```

---

## WO-2 — Decode HTML entities in HN scanner output

**File**: `src/evidentia/scanners/hn.py`
**Function**: `scan_hn_live`
**Problem (F4)**: HN Algolia returns `story_text` as HTML. Entities like `&#x27;` (apostrophe) and
`&#x2F;` (slash) are stored as-is in `verbatim_quote` and `source_text`. The auditor's substring
match then fails against the decoded page body.

**Fix**: Import `html` from stdlib and decode entities after reading `story_text`.

Add at top of file (after existing imports):
```python
import html as _html
```

In `scan_hn_live`, change:
```python
source_text = str(item.get("story_text") or item.get("title") or "")
```
to:
```python
source_text = _html.unescape(str(item.get("story_text") or item.get("title") or ""))
```

**Definition of done**: `_html.unescape` is called on `source_text` in `scan_hn_live`. No entity
literals (`&#x27;`, `&#x2F;`, `&amp;`) appear in the `verbatim_quote` field of HN scan output.

**New test**:
```python
from evidentia.scanners.hn import scan_hn_live

def test_hn_html_entities_decoded():
    def _mock_fetch(url):
        return {
            "hits": [{
                "objectID": "12345",
                "title": "Test story",
                "story_text": "I&#x27;m building a tool &amp; it&#x27;s great",
                "created_at": "2025-01-01T00:00:00.000Z",
            }]
        }
    results = scan_hn_live("test", max_results=1, fetch_json=_mock_fetch)
    assert len(results) == 1
    assert "&#x27;" not in results[0]["verbatim_quote"]
    assert "I'm building a tool & it's great" == results[0]["source_text"]
```

---

## WO-3 — Filter GitHub scanner to demand-relevant signals only

**File**: `src/evidentia/scanners/github.py`
**Function**: `scan_github_live`
**Problem (F3)**: GitHub Issues search returns implementation tickets — developer feature specs and
school project tasks. These are supply artefacts. The query should target *user-facing* feedback:
issues tagged as feature requests, discussions, or issues with body length > 50 chars.

**Fix**: Change the GitHub search query to prefer user-facing repos and require non-trivial body content.

In `scan_github_live`, change:
```python
query_string = urlencode({"q": query, "per_page": max_results})
url = f"https://api.github.com/search/issues?{query_string}"
```
to:
```python
# Restrict to feature-request labelled issues or issues with "request" in body; exclude bots
github_query = f"{query} label:feature-request OR label:enhancement is:open"
query_string = urlencode({"q": github_query, "per_page": max_results * 3, "sort": "reactions", "order": "desc"})
url = f"https://api.github.com/search/issues?{query_string}"
```

And in the normalization loop, add a minimum body length filter:
```python
for item in items:
    html_url = item.get("html_url")
    if not html_url:
        continue
    source_text = str(item.get("body") or item.get("title") or "")
    # Skip issues with trivially short bodies (title-only, no real signal)
    if len(source_text.strip()) < 50:
        continue
    if len(normalized) >= max_results:
        break
    normalized.append({ ... })  # same as existing
```

**Definition of done**: The GitHub query string includes `label:feature-request OR label:enhancement`.
Issues with body length < 50 characters are filtered out before appending to normalized list.

**New test**:
```python
from evidentia.scanners.github import scan_github_live

def test_github_filters_short_body_issues():
    def _mock_fetch(url, headers=None):
        return {
            "items": [
                {"html_url": "https://github.com/a/b/issues/1", "title": "Expense Tracking", "body": "Expense Tracking", "id": 1, "updated_at": "2025-01-01T00:00:00Z"},
                {"html_url": "https://github.com/a/b/issues/2", "title": "Feature: expense tracking", "body": "We need expense tracking because we currently spend hours in spreadsheets and need a better solution for our 50-person team.", "id": 2, "updated_at": "2025-01-01T00:00:00Z"},
            ]
        }
    results = scan_github_live("expense tracking", max_results=3, fetch_json=_mock_fetch)
    assert len(results) == 1
    assert "github:2" == results[0]["cluster_id"]

def test_github_query_targets_feature_requests():
    captured = {}
    def _mock_fetch(url, headers=None):
        captured["url"] = url
        return {"items": []}
    scan_github_live("invoicing", max_results=3, fetch_json=_mock_fetch)
    assert "feature-request" in captured["url"] or "enhancement" in captured["url"]
```

---

## WO-4 — Content-based deduplication for cross-platform posts

**File**: `src/evidentia/scoring.py`
**Function**: Add `dedupe_by_content_hash` after existing `dedupe_by_cluster`
**Problem (F6)**: Same content posted to multiple subreddits (r/iosapps and r/iOSAppsMarketing)
has different permalinks → different `cluster_id` → passes through `dedupe_by_cluster`.

**Fix**: Add a content-hash dedup pass that runs AFTER cluster dedup. Use first 200 chars of
source_text as the fingerprint key.

Add this function to `src/evidentia/scoring.py`:
```python
def dedupe_by_content_fingerprint(items: list[dict]) -> list[dict]:
    """Remove duplicates where the first 200 chars of source_text are identical.
    Keeps the item with the higher score (or earlier in list on tie).
    """
    seen: dict[str, dict] = {}
    for item in items:
        fingerprint = str(item.get("source_text", ""))[:200].strip()
        if not fingerprint:
            continue  # no fingerprint — cannot deduplicate, keep
        current = seen.get(fingerprint)
        if current is None or _dedupe_key(item) > _dedupe_key(current):
            seen[fingerprint] = item
    # Preserve items with no fingerprint as-is
    no_fp = [item for item in items if not str(item.get("source_text", ""))[:200].strip()]
    return list(seen.values()) + no_fp
```

Also update `run_live_scan` in `src/evidentia/cli.py` to call it:
```python
from evidentia.scoring import dedupe_by_cluster, dedupe_by_content_fingerprint, rank_opportunities, score_opportunity
# ...
deduped = dedupe_by_cluster(scored)
deduped = dedupe_by_content_fingerprint(deduped)  # add this line
ranked = rank_opportunities(deduped)
```

**Definition of done**: `dedupe_by_content_fingerprint` exists in `scoring.py`. It is called in `run_live_scan` in `cli.py` after `dedupe_by_cluster`.

**New test**:
```python
from evidentia.scoring import dedupe_by_content_fingerprint

def test_content_dedup_removes_cross_platform_duplicates():
    body = "We need better expense tracking for our team. " * 5  # > 200 chars, same text
    item_a = {"cluster_id": "reddit:a", "source_text": body, "score": 0.5, "published_at": None, "opportunity_id": "opp_001"}
    item_b = {"cluster_id": "reddit:b", "source_text": body, "score": 0.4, "published_at": None, "opportunity_id": "opp_002"}
    result = dedupe_by_content_fingerprint([item_a, item_b])
    assert len(result) == 1
    assert result[0]["cluster_id"] == "reddit:a"  # higher score kept
```

---

## WO-5 — Expose gate failure reasons in API and UI

**File**: `src/evidentia/scoring.py` (add gate_failures field)
**File**: `docs/frontend/app/page.tsx` (update OpportunityCard display)
**Problem (F2, U3)**: HOLD items show heuristic scores (meaningless) but not which gate failed.
Users cannot understand or debug HOLD decisions.

### Part A — scoring.py: add `gate_failures` to HOLD return

In `score_opportunity`, replace the HOLD return:
```python
# OLD:
    if any(gate != "pass" for gate in gates):
        return {
            "verdict": "HOLD",
            "gate_verdict": "HOLD",
            "heuristic_score": 0.0,
            "freshness_factor": 0.0,
            "final_score": 0.0,
            "score": 0.0,
        }
```
With:
```python
# NEW:
    gate_values = {gate: opportunity[gate] for gate in HARD_GATES}
    if any(v != "pass" for v in gate_values.values()):
        return {
            "verdict": "HOLD",
            "gate_verdict": "HOLD",
            "gate_failures": [k for k, v in gate_values.items() if v != "pass"],
            "heuristic_score": 0.0,
            "freshness_factor": 0.0,
            "final_score": 0.0,
            "score": 0.0,
        }
```

### Part B — page.tsx: render gate failures for HOLD

In the `OpportunityCard` component in `docs/frontend/app/page.tsx`, find the section that
renders heuristic scores (competition_gap, buildability, reachability) and conditionally render
gate failures instead for HOLD items.

Find the block that renders score numbers (looks for `competition_gap`, `buildability`, `reachability_strength`).
Replace or wrap it so that:
- If `opp.verdict === "HOLD"` AND `opp.gate_failures?.length > 0`: render gate failures as red pills
  e.g. `willingness_to_pay ✗`, `distribution_channel ✗`
- If `opp.verdict === "PURSUE"`: render the heuristic scores as before

Example JSX for gate failures:
```tsx
{opp.verdict === "HOLD" && opp.gate_failures && opp.gate_failures.length > 0 && (
  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
    {opp.gate_failures.map((g: string) => (
      <span key={g} style={{
        background: "rgba(255,60,60,0.12)", color: "#ff6b6b",
        border: "1px solid rgba(255,60,60,0.3)",
        borderRadius: 4, padding: "2px 8px", fontSize: 11, fontFamily: "var(--font-geist-mono)"
      }}>
        {g.replace(/_/g, " ")} ✗
      </span>
    ))}
  </div>
)}
```

**Definition of done**:
- `score_opportunity` HOLD return includes `"gate_failures": list[str]`
- Existing 12 validation tests still pass (they check `verdict`, not internal fields — safe)
- `OpportunityCard` in page.tsx renders gate failure pills for HOLD, not heuristic scores

**New test**:
```python
from evidentia.scoring import score_opportunity

def test_hold_exposes_gate_failures():
    opp = {
        "willingness_to_pay": "fail",
        "distribution_channel": "pass",
        "data_feasibility": "pass",
        "competition_gap": 0.8,
        "buildability": 0.7,
        "reachability_strength": 0.6,
    }
    result = score_opportunity(opp)
    assert result["verdict"] == "HOLD"
    assert "gate_failures" in result
    assert result["gate_failures"] == ["willingness_to_pay"]

def test_pursue_has_no_gate_failures():
    opp = {
        "willingness_to_pay": "pass",
        "distribution_channel": "pass",
        "data_feasibility": "pass",
        "competition_gap": 0.8,
        "buildability": 0.7,
        "reachability_strength": 0.6,
    }
    result = score_opportunity(opp)
    assert result["verdict"] == "PURSUE"
    assert result.get("gate_failures") is None or result.get("gate_failures") == []
```

---

## WO-6 — Minimum engagement filter for Reddit scanner

**File**: `src/evidentia/scanners/reddit.py`
**Function**: `scan_reddit_live`
**Problem (F8, F10)**: Promotional posts from r/LooteraShopper with no engagement signal pass
through. Self-promotion and spam dilute results.

**Fix**: Filter out items with score < 2 (Reddit score = upvotes − downvotes) and items from
known promotional-only subreddits.

In the normalization loop in `scan_reddit_live`, add before `normalized.append(...)`:
```python
# Filter: require minimum engagement
reddit_score = item.get("score", 0) or 0
if int(reddit_score) < 2:
    continue
# Filter: skip known promotional-only subreddits
subreddit = str(item.get("subreddit") or "").lower()
_PROMO_SUBS = {"lootershopper", "deals", "freebies", "beermoney", "slavelabour"}
if subreddit in _PROMO_SUBS:
    continue
```

**Definition of done**: `scan_reddit_live` skips items with `score < 2` and skips items from
`_PROMO_SUBS`. The SaveSage post from r/LooteraShopper would be filtered by the subreddit check.

**New test**:
```python
from evidentia.scanners.reddit import scan_reddit_live

def test_reddit_filters_low_score_posts():
    def _mock_fetch(url, headers=None):
        return {
            "data": {"children": [
                {"data": {"permalink": "/r/test/comments/abc/", "title": "Good signal", "selftext": "We need expense tracking for our 20-person startup and would pay monthly.", "created_utc": 1700000000, "score": 50, "subreddit": "startups"}},
                {"data": {"permalink": "/r/deals/comments/xyz/", "title": "Promo", "selftext": "Buy now", "created_utc": 1700000000, "score": 1, "subreddit": "LooteraShopper"}},
            ]}
        }
    results = scan_reddit_live("expense tracking", max_results=5, fetch_json=_mock_fetch)
    assert len(results) == 1
    assert results[0]["title"] == "Good signal"
```

---

## Execution Order

```
WO-1 (classifier prompt fix)
  └─ WO-2 (HN HTML decode)
       └─ WO-3 (GitHub filter)
            └─ run pytest — confirm 12 original + new WO tests pass

WO-4 (content dedup)   ← independent, can run in parallel with WO-3
WO-5 (gate failures)   ← independent, can run in parallel
WO-6 (reddit filter)   ← independent, can run in parallel
```

Run `pytest tests/validation/ -v` after each work order. Final state must show ≥ 18 tests passing
(12 original + 6 new: 1 per WO-1, 1 per WO-2, 2 per WO-3, 1 per WO-4, 2 per WO-5, 1 per WO-6).

---

## Acceptance Contract

The work orders are complete when **all** of:

1. `pytest tests/validation/ -v` shows ≥ 18 passed, 0 failed
2. A manual `evidentia scan --live --domain "expense tracking" --sources hn,reddit,github --max-results 3 --output /tmp/scan.json` run produces ≥ 1 item with `"verdict": "PURSUE"` (requires a live LLM API key)
3. `score_opportunity` HOLD return includes `"gate_failures"` key
4. HN scanner `verbatim_quote` contains no `&#x` patterns
5. GitHub query string in `scan_github_live` includes `feature-request` or `enhancement`
6. `dedupe_by_content_fingerprint` is exported from `scoring.py` and called in `run_live_scan`
