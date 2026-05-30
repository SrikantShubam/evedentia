# Evidentia — Next Pivot Work Orders (Part 2: Niche Hunter Loop)

**For:** Codex 5.3xhigh
**Prepared from:** `NEXT_PIVOT.md` + `docs/next_pivot_v1_architecture.md`
**Precondition:** Part 1 (`NEXT_PIVOT_WORKORDERS.md` WO-1..9) complete and merged. Repo at 92+ passing tests, CLI = `scan/audit/classify/score`, verdicts = KILL/REFINE/PURSUE.
**Scope:** The generate↔validate loop — idea generator, anchors, review-based listening, slice clustering, real critic with `next_test`, persistent "best ideas" repo, and the orchestrator that loops until stopped.

**Exit condition for each WO:** `pytest tests/ -q` stays green. `pytest tests/validation/ -v` stays green. New tests added per WO.

---

## Guardrails (apply to every work order)

1. **Stdlib + existing deps only.** No new PyPI deps without explicit approval in the WO.
2. **Deterministic logic wherever possible.** LLMs label/classify narrow decisions. They do not decide control flow.
3. **Every LLM call returns structured JSON** via `providers.generate_json`, validated by shape-checker (same pattern as `classifier._validate_classification_shape`).
4. **No new artifact without a schema_version.** All JSON artifacts get `"schema_version": 1`.
5. **Verified evidence or discard.** Every `DemandSignal` must pass `auditor.verify_quote` with `proof_level in {"fetched", "in_memory"}`. `"none"` → `discard_log`.
6. **REFINE always has `next_test`.** Invariant enforced in tests.
7. **Commits per work order**, message `[WO-N] <title>`.

---

## Execution Order

```
WO-10 (models) → WO-11 (anchor.py + anchors/) → WO-12 (reviews scanner)
  → WO-13 (clusterer) → WO-14 (critic + next_test) → WO-15 (outputs + best_ideas index)
  → WO-16 (generator) → WO-17 (CLI: hunt, generate, loop)
  → WO-18 (loop orchestrator) → WO-19 (end-to-end tests + live smoke)
```

WO-10 through WO-15 form the **validator side**. WO-16 is the **generator side**. WO-17/18 wire the loop. WO-19 proves it.

---

## WO-10 — Extend `models.py` for slice-level reasoning

**File:** `src/evidentia/models.py`
**Estimated effort:** 1h

### Additions

```python
from dataclasses import dataclass, field
from enum import Enum

@dataclass
class DemandSignal:
    signal_id: str                       # sha1 of source_url + verbatim_quote
    source_url: str
    verbatim_quote: str
    timestamp: str                       # ISO-8601
    title: str | None = None
    source_text: str | None = None
    source_kind: str = "unknown"         # "ios_review" | "reddit" | "product_hunt" | "hn" | "github"
    signal_subtype: str = "unknown"      # missing_feature | usability_complaint | cohort_exclusion | pricing_complaint | switching_intent
    author: str | None = None            # for distinct-author counting
    verified: bool = False
    proof_level: str = "none"            # none | in_memory | fetched

@dataclass
class Anchor:
    slug: str
    market_name: str
    incumbents: list[str]
    proof_of_market: DemandSignal
    cohort_hints: list[str] = field(default_factory=list)
    primary_channel_queries: list[str] = field(default_factory=list)

@dataclass
class Slice:
    slice_id: str                        # sha1 of anchor.slug + sorted signal_ids
    anchor_slug: str
    label: str                           # LLM-generated, short
    signal_ids: list[str]
    author_count: int
    dominant_subtype: str

@dataclass
class SliceVerdict:
    slice_id: str
    anchor_slug: str
    verdict: str                         # KILL | REFINE | PURSUE (use Verdict enum)
    gates: dict[str, bool]               # market_exists, slice_has_voices, slice_underserved, reachable, buildable
    heuristics: dict[str, float]
    refine_reason: str | None
    next_test: str | None
    evidence_ids: list[str]              # DemandSignal.signal_id list
    schema_version: int = 1
```

Keep the existing `Verdict` enum and `ProductSpec`, `Opportunity` (if still used) untouched.

### Definition of done
- All dataclasses import and instantiate.
- `to_dict()` helper via `dataclasses.asdict` works for JSON serialization.
- Unit test in `tests/unit/test_models.py` constructs each model.

---

## WO-11 — `anchor.py` + hand-curated anchors

**Files created:**
- `src/evidentia/anchor.py`
- `anchors/bible-study-apps.yaml`
- `anchors/meditation-apps.yaml`
- `anchors/home-workout-apps.yaml`
- `anchors/resume-builders.yaml`
- `anchors/smb-invoicing.yaml`

**New dep:** `pyyaml` (add to `pyproject.toml`).
**Estimated effort:** 3h

### `anchor.py` API

```python
def load_anchor(path: Path) -> Anchor: ...
def load_all_anchors(root: Path = Path("anchors")) -> list[Anchor]: ...
def verify_anchor(anchor: Anchor) -> Anchor: ...  # re-runs auditor.verify_quote on proof_of_market
def anchors_root() -> Path: ...  # Path("anchors") resolved relative to repo root
```

### Anchor YAML schema

```yaml
slug: bible-study-apps
market_name: Bible study apps
incumbents: [YouVersion, Bible.is, Blue Letter Bible]
proof_of_market:
  verbatim_quote: "YouVersion has surpassed 500 million installs"
  source_url: https://youversion.com/press
  timestamp: 2024-11-01T00:00:00Z
cohort_hints: [women, post-evangelical, youth, seniors]
primary_channel_queries:
  - "site:reddit.com/r/Christianity YouVersion missing"
  - "site:reddit.com/r/exvangelical"
  - "site:producthunt.com YouVersion"
```

### Rules
- `verify_anchor` calls `auditor.verify_quote({source_url, verbatim_quote, source_text: ""})`. If `proof_level == "none"`, raise `AnchorVerificationError` with the URL.
- `load_all_anchors` skips files that fail verification but logs a warning and continues.

### Hand-curated anchors (content)
Each of the 5 anchors below must be committed with a **real, fetchable proof_of_market URL** and a real verbatim quote. Codex should search the web to find and verify each one before committing the YAML. If a quote cannot be verified, substitute a different one from the same market and document the substitution in the commit message.

Starter seed (verify + replace as needed):

1. **bible-study-apps** — YouVersion install count
2. **meditation-apps** — Calm or Headspace subscriber/revenue count
3. **home-workout-apps** — Nike Training Club or Peloton digital user count
4. **resume-builders** — Resume.io or Zety user count
5. **smb-invoicing** — FreshBooks or Wave user count

### Definition of done
- `from evidentia.anchor import load_all_anchors; load_all_anchors()` returns 5 verified anchors.
- `pytest tests/unit/test_anchor.py` passes (see below).

### New test — `tests/unit/test_anchor.py`
```python
def test_load_and_verify_fixture_anchor(tmp_path, monkeypatch):
    from evidentia import anchor, auditor
    monkeypatch.setattr(auditor, "_fetch_page_text",
        lambda url, **kw: "YouVersion has surpassed 500 million installs today")
    yaml_text = """
slug: test-anchor
market_name: Test Market
incumbents: [IncumbentA]
proof_of_market:
  verbatim_quote: "YouVersion has surpassed 500 million installs"
  source_url: https://example.com/press
  timestamp: 2024-11-01T00:00:00Z
cohort_hints: []
primary_channel_queries: []
"""
    p = tmp_path / "a.yaml"
    p.write_text(yaml_text)
    a = anchor.load_anchor(p)
    a = anchor.verify_anchor(a)
    assert a.proof_of_market.verified is True
    assert a.proof_of_market.proof_level == "fetched"

def test_unverifiable_anchor_raises(tmp_path, monkeypatch):
    from evidentia import anchor, auditor
    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url, **kw: None)
    # ... construct yaml with unmatchable quote
    # assert raises AnchorVerificationError
```

---

## WO-12 — `scanners/reviews.py` (iOS RSS + reddit-per-product)

**File created:** `src/evidentia/scanners/reviews.py`
**Estimated effort:** 5h

### Public API

```python
def listen(anchor: Anchor, limit: int = 50, env: dict[str, str] | None = None) -> list[DemandSignal]: ...
```

### Behavior
1. For each `incumbent` in `anchor.incumbents`:
   a. **iOS RSS reviews** — `https://itunes.apple.com/us/rss/customerreviews/page=1/id=<APPID>/sortBy=mostRecent/json`. The app id lookup uses `https://itunes.apple.com/search?term=<incumbent>&entity=software&limit=1`. Parse reviews; skip 4-5 star reviews (we want pain, not praise).
   b. **Reddit subreddit-per-product** — query Reddit API for `r/<slugified_incumbent>` and a search for `"<incumbent>" missing OR broken OR hate OR switch`.
2. For each `primary_channel_query` in the anchor, call `providers.search` with the existing chain and convert top results to candidates.
3. For each candidate: run `auditor.verify_quote`. Discard `proof_level == "none"`.
4. Tag `signal_subtype` deterministically via `_classify_subtype(text: str) -> str` helper using keyword regex:
   - `missing_feature` — "missing", "wish it had", "should add", "needs"
   - `usability_complaint` — "confusing", "hard to use", "clunky", "UI"
   - `cohort_exclusion` — "for men only", "not for women", "excluded", "no option for"
   - `pricing_complaint` — "too expensive", "overpriced", "free tier", "paywall"
   - `switching_intent` — "switching to", "looking for alternative", "replaced X with"
   - fallback: `unknown`
5. Compute `signal_id = sha1(source_url + verbatim_quote)[:16]`.
6. Return at most `limit` signals, sorted by (verified desc, timestamp desc).

### Rate-limiting / resilience
- Per-source try/except — one source failing never kills the anchor.
- 2s sleep between iOS RSS requests.
- Respect existing `providers` fallback chain; do not hardcode Tavily.

### Definition of done
- Fixture test in `tests/unit/test_reviews_scanner.py` with a stubbed iOS RSS response, stubbed Reddit response, monkeypatched auditor → returns expected signals.
- Live smoke test `tests/live/test_reviews_live.py` marked `@pytest.mark.live` — fetches one real anchor's iOS reviews and asserts schema.
- `listen()` never raises on a single-source failure.

---

## WO-13 — `clusterer.py`

**File created:** `src/evidentia/clusterer.py`
**Estimated effort:** 3h

### Public API

```python
def cluster_signals(anchor: Anchor, signals: list[DemandSignal],
                    jaccard_threshold: float = 0.35,
                    llm_labeler: callable | None = None) -> list[Slice]: ...
```

### Deterministic clustering algorithm

1. **Normalize** each signal: `text = (quote + " " + title).lower()`, strip punctuation via `re.sub(r"[^\w\s]", " ", text)`, collapse whitespace. Remove incumbent names (from anchor) as stopwords.
2. **Tokenize** to set of tokens ≥ 3 chars, excluding an English stopword list (committed as a module-level constant — ~50 words max, stdlib-only).
3. **Pairwise Jaccard**: `|A ∩ B| / |A ∪ B|`. O(n²) is fine — n ≤ 200 per anchor.
4. **Subtype gate**: edges only form between signals with matching `signal_subtype` (or one side = `unknown`).
5. **Cohort boost**: if `anchor.cohort_hints` intersect either signal's normalized text, boost the pair's similarity by `+0.15` before thresholding.
6. **Single-link clustering** (union-find): edge exists when boosted_similarity ≥ `jaccard_threshold`.
7. **Drop clusters with fewer than 2 distinct authors**.
8. For each remaining cluster: compute `author_count`, `dominant_subtype` (mode of member subtypes).
9. **Label via LLM** (if `llm_labeler` is None, use `"cluster_<index>"`):
   ```python
   label = llm_labeler(quotes=[s.verbatim_quote for s in cluster])
   # Prompt enforces: one noun phrase, ≤ 8 words, quote nothing, invent nothing
   ```
10. `slice_id = sha1(anchor.slug + "|" + ",".join(sorted(signal_ids)))[:16]`.

### Definition of done
- `tests/unit/test_clusterer.py` with synthetic signals verifying: Jaccard threshold, subtype gate, cohort boost, <2-author drop, stable slice_id.
- Labeling is decoupled (test passes `llm_labeler=None`).

---

## WO-14 — `critic.py` with `next_test` generator

**File created:** `src/evidentia/critic.py`
**Estimated effort:** 5h

### Public API

```python
def critique_slice(slice: Slice, signals_by_id: dict[str, DemandSignal],
                   anchor: Anchor, env: dict[str, str] | None = None) -> SliceVerdict: ...
```

### Five gates (implement exactly this logic)

```python
def _gate_market_exists(anchor): return anchor.proof_of_market.verified
def _gate_slice_has_voices(slice): return slice.author_count >= 3
def _gate_slice_underserved(slice, anchor, env): ...  # web-search + LLM classify, see below
def _gate_reachable(slice, anchor, signals): ...  # at least one signal URL in primary_channel or cohort subreddit
def _gate_buildable(slice, signals): ...  # heuristic on integration-mention count
```

### `_gate_slice_underserved`
1. Query search provider: `"{slice.label}" app OR saas`.
2. Take top 5 result titles.
3. Single LLM call with strict schema:
   ```json
   {"underserved": "yes|no|unclear", "named_competitors": ["..."]}
   ```
4. Map: `yes` → pass, `no` → fail, `unclear` → fail (conservative) with `named_competitors` echoed into `refine_reason`.

### `_gate_buildable`
Count distinct integration/API mentions in all cluster quotes using a regex list (`stripe`, `quickbooks`, `salesforce`, `twilio`, `oauth`, `sso`, etc — committed as module constant). Pass if count < 4.

### Verdict logic

```python
gates = {m: _gate_market_exists(anchor),
         v: _gate_slice_has_voices(slice),
         u: _gate_slice_underserved(...),
         r: _gate_reachable(...),
         b: _gate_buildable(...)}

if not gates["market_exists"] or not gates["slice_underserved"]:
    verdict = KILL
elif all(gates.values()) and slice.author_count >= 5:
    verdict = PURSUE
else:
    verdict = REFINE
```

### `next_test` templates (module constant, fill via `.format(...)`)

```python
NEXT_TEST_TEMPLATES = {
    "weak_voices": "Post a specific question in {channel} asking users to share experiences with {pain}. PURSUE if ≥ 10 reply-level engagements in 7 days.",
    "borderline_served": "Named competitor(s): {competitors}. Validate differentiation by asking 5 users of {first_competitor} whether {slice_label} would make them switch.",
    "weak_reach": "Identify a primary channel: find a subreddit, newsletter, or conference tag with ≥ 1k members focused on {cohort}. PURSUE if found.",
    "weak_buildable": "Reduce scope to one atomic wedge. Re-run critic with narrowed label '{slice_label} for {cohort} — only {top_feature}'.",
    "landing_page_test": "Run landing-page test on {channel} with copy anchored on '{slice_label}'. PURSUE if ≥ 50 signups in 7 days.",
}
```

**Invariant:** `if verdict == "REFINE": assert next_test is not None`.

For `KILL`, `next_test = None`. For `PURSUE`, `next_test = "Ship a manual wedge. Document traction in outputs/pursued/<slice_id>/traction.md."`.

### Definition of done
- `tests/unit/test_critic.py` covers each gate in isolation + each verdict path + the REFINE-implies-next_test invariant.
- Zero LLM calls in unit tests (monkeypatch provider for `_gate_slice_underserved`).

---

## WO-15 — `outputs.py` + persistent "best ideas" index

**File created:** `src/evidentia/outputs.py`
**Estimated effort:** 3h

### Public API

```python
def write_run(run_dir: Path, anchor: Anchor, signals: list[DemandSignal],
              slices: list[Slice], verdicts: list[SliceVerdict],
              discards: list[dict]) -> None: ...
def append_to_index(index_path: Path, verdicts: list[SliceVerdict],
                    anchor: Anchor, run_dir: Path) -> None: ...
def read_index(index_path: Path) -> list[dict]: ...
def top_ideas(index_path: Path, verdict: str = "PURSUE", n: int = 20) -> list[dict]: ...
```

### Per-run layout

```
outputs/hunts/<anchor_slug>/<iso_timestamp>/
  anchor.json
  signals.json
  slices.json
  verdicts.json
  discard_log.json
  summary.md
```

### Cross-run index — `outputs/best_ideas.jsonl`

Append-only. One line per verdict. Shape:

```json
{"schema_version": 1, "ts": "2026-04-17T18:22:00Z",
 "anchor_slug": "bible-study-apps", "slice_id": "a1b2c3",
 "label": "trauma-aware Bible study for post-evangelical women",
 "verdict": "REFINE", "author_count": 4, "gates": {...},
 "next_test": "...", "run_dir": "outputs/hunts/bible-study-apps/2026-04-17T18:22:00Z"}
```

### Rules
- `append_to_index` is atomic per line (open `"a"`, write one `json.dumps(...) + "\n"`, close).
- `top_ideas` filters by verdict, sorts by `author_count desc, ts desc`, returns top n. Dedup by `slice_id` (keep most recent entry per slice).
- `summary.md` generator produces the human-readable format from `NEXT_PIVOT_v1_architecture.md` §8.

### Definition of done
- `tests/unit/test_outputs.py`: round-trip run → index → top_ideas returns expected results.
- Index tolerates malformed lines (skip with a warning, do not raise).

---

## WO-16 — `generator.py` (the idea generator side)

**File created:** `src/evidentia/generator.py`
**Estimated effort:** 6h

### Design decision
Do **not** port the full 778-line `codex/forensic_engine/idea_generator.py`. Build a leaner, anchor-aware generator tailored to the loop.

### Public API

```python
def generate_ideas_from_anchor(anchor: Anchor, count: int = 10,
                               env: dict[str, str] | None = None,
                               debug_log_path: str | None = None) -> list[dict]: ...

def generate_ideas_from_pursue(pursue_entries: list[dict], count: int = 10, ...) -> list[dict]: ...
```

### `generate_ideas_from_anchor` behavior
1. Build prompt:
   ```
   You are a niche hypothesis generator. Given a proven market and cohort hints, propose {count} narrow product hypotheses that fit the pattern "[market] for [specific cohort with specific pain]". Each hypothesis must be a specific slice, not a generic variant.

   Market: {anchor.market_name}
   Incumbents: {anchor.incumbents}
   Cohort hints: {anchor.cohort_hints}

   Return JSON: {"ideas": [{"label": "...", "cohort": "...", "pain_hypothesis": "...", "search_queries": ["...", "..."]}]}
   Constraints: label is a noun phrase ≤ 10 words. pain_hypothesis is one sentence. search_queries are 2-3 queries that would surface buyer voices for this slice.
   ```
2. Call LLM via provider chain + shape validator (reuse `classifier._validate_classification_shape` pattern).
3. Return list of dicts.

### `generate_ideas_from_pursue` behavior
Given PURSUE entries from `best_ideas.jsonl`, ask LLM to **propose adjacent hypotheses** that share the successful pattern. Prompt similar to above but seeded with prior PURSUEs.

### Non-goals for this WO
- No web search during generation (generator is cheap; validation is where search burns tokens).
- No persistence — generator returns list of dicts. The loop orchestrator (WO-18) decides what to do with them.

### Definition of done
- `tests/unit/test_generator.py` with stubbed LLM provider; asserts shape + count.
- Generator returns consistent JSON shape even when LLM response varies (shape validation + single retry, same pattern as classifier).

---

## WO-17 — CLI: `hunt`, `generate`, `loop` commands

**File:** `src/evidentia/cli.py`
**Estimated effort:** 3h

### New commands

```bash
evidentia anchor list                                   # list all anchors in anchors/
evidentia anchor verify <slug>                          # verify one

evidentia hunt <slug> [--limit N] [--dry-run]           # one full validate run for one anchor
evidentia hunt-all [--limit N] [--dry-run]              # iterate anchors/

evidentia generate --anchor <slug> --count N            # propose N ideas for an anchor
evidentia generate --from-pursues --count N             # propose from best_ideas.jsonl PURSUEs

evidentia loop [--iterations N] [--ideas-per-iter M] [--anchors slug,slug,...]
                                                        # generate → hunt → append → repeat
evidentia best [--verdict PURSUE] [--n 20]              # print top ideas from the index
```

### Plumbing
- `hunt` = `listen → cluster → critique → write_run → append_to_index`.
- `hunt-all` iterates anchors and calls `hunt` per anchor.
- `loop` is WO-18.
- `best` reads `outputs/best_ideas.jsonl` and prints a table (plain text, stdlib — no `rich` dep).

### Definition of done
- `evidentia --help` lists all commands.
- `evidentia hunt <fixture-slug> --dry-run` writes all artifacts without network calls.
- `tests/acceptance/test_hunt_cli.py` covers `hunt --dry-run` end-to-end.

---

## WO-18 — Loop orchestrator

**File created:** `src/evidentia/loop.py`
**Estimated effort:** 3h

### Public API

```python
def run_loop(anchors: list[Anchor], iterations: int = 10,
             ideas_per_iter: int = 10, env: dict[str, str] | None = None) -> dict:
    """
    Returns a summary dict with counts per verdict and total runtime.
    Appends to outputs/best_ideas.jsonl and writes per-anchor run dirs.
    """
```

### Algorithm

```
for i in range(iterations):
    for anchor in anchors:
        # 1. Generate
        ideas = generate_ideas_from_anchor(anchor, count=ideas_per_iter)

        # 2. For each generated idea, treat it as a hypothetical slice label
        #    and run a targeted listen using idea.search_queries
        for idea in ideas:
            signals = listen_for_idea(anchor, idea)   # new helper in reviews.py
            if not signals: continue

            # 3. Cluster these specific signals (may produce 0-3 slices)
            slices = cluster_signals(anchor, signals)

            # 4. Critique each slice
            for slice in slices:
                verdict = critique_slice(slice, signals_by_id, anchor)
                write_run(...)
                append_to_index(...)

    # 5. After each iteration, pull top PURSUEs and feed back into next iter
    pursues = top_ideas(index_path, verdict="PURSUE", n=5)
    if pursues:
        seeded_ideas = generate_ideas_from_pursue(pursues)
        # merge into next iteration's idea list
```

### Stop conditions
- Max iterations reached.
- CLI interrupt (ctrl-c handled gracefully; flush index before exit).
- Optional: `--stop-on-first-pursue` flag.

### Budget controls
- `--max-llm-calls N` hard cap; raise `BudgetExhausted` and flush.
- Log a running token/call counter via the debug log path.

### Definition of done
- `tests/integration/test_loop.py` runs loop end-to-end against fixture anchor + stubbed LLM + stubbed search; asserts index file grows and verdict mix is plausible.

---

## WO-19 — End-to-end + live smoke

**Files:**
- `tests/integration/test_hunt_pipeline.py`
- `tests/integration/test_loop.py` (augment WO-18's)
- `tests/live/test_live_hunt.py` (marked `@pytest.mark.live`)
- `tests/live/test_live_loop.py` (marked `@pytest.mark.live`)

**Estimated effort:** 3h

### Deliverables
1. **Fixture hunt pipeline test**: anchor → stubbed reviews → real clusterer → stubbed critic LLM → verdict artifacts on disk.
2. **Loop integration test**: one anchor, 2 iterations, 3 ideas per iter; assert index has ≥ 1 line and no malformed entries.
3. **Live hunt smoke** (marked, not in CI): run against `bible-study-apps` with `--limit 5`. Assert: runs without crash, writes all 6 artifact files, at least one signal has `proof_level == "fetched"`.
4. **Live loop smoke** (marked): one iteration, two anchors. Assert: `outputs/best_ideas.jsonl` exists and is non-empty.

### Pytest markers (add to `pyproject.toml`)

```toml
[tool.pytest.ini_options]
markers = ["live: real network calls; not for CI"]
```

Default CI invocation: `pytest -m "not live"`.

### Definition of done
- `pytest -m "not live"` green.
- `pytest -m live` green when keys are present; auto-skip otherwise.
- README in `outputs/` describes the layout (one paragraph).

---

## Post-completion checkpoint

After WO-10 through WO-19 merge:

1. `pytest -m "not live"` green.
2. Run: `evidentia hunt-all --limit 5`
3. Run: `evidentia loop --iterations 3 --ideas-per-iter 5 --anchors bible-study-apps,smb-invoicing`
4. Inspect: `evidentia best --n 20`
5. Tag `v0.3.0-niche-hunter-loop`.

At this point the two-part generate-validate loop is real. Every PURSUE in `best_ideas.jsonl` is:
- Grounded in a proven market (anchor with verified proof_of_market)
- Backed by ≥ 5 distinct buyer voices (verified quotes)
- Evaluated by five deterministic gates
- Paired with either a next_test (REFINE) or a ship directive (PURSUE)

The "repo of best ideas" is `outputs/best_ideas.jsonl`. Append-only, grep-friendly, schema-versioned.

---

## What remains *after* WO-19 (explicitly out of scope here)

- **Builder / deployer / tracker** — gated behind shipping one real wedge manually, per `NEXT_PIVOT.md` §7.
- **UI / web app** — gated behind productization gate.
- **Open-source release + tiers** — gated behind at least one customer-validated wedge.
- **Tuning pass** — Jaccard threshold, voice thresholds, subtype taxonomy. Calibrate on real loop output, not in advance.
