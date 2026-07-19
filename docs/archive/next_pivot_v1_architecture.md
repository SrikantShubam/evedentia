# Evidentia — Niche Hunter Architecture (v1)

**Status:** DRAFT — implementation plan for Weeks 2-4 of `NEXT_PIVOT.md`
**Precondition:** Week 1 work orders (`NEXT_PIVOT_WORKORDERS.md`) must be complete. The codebase must be reduced to `scan / audit / classify / score` with KILL / REFINE / PURSUE verdicts.
**Scope of this doc:** anchor module, review-based scanners, slice clustering, per-slice critic, verdict artifacts with `next_test`.

---

## 1. Conceptual shift

Week 1 trims the existing pipeline. This document describes the **new core**: a market-anchored niche hunter.

```text
Week 1 pipeline (old, trimmed):
  scan(domain) → classify(signal) → score(signal) → verdict(signal)

Weeks 2–4 pipeline (new):
  anchor(market) → listen(anchor) → cluster(signals) → critique(slice) → verdict(slice, with next_test)
```

The unit of analysis moves from **single signal** to **slice**. A slice is a coherent group of complaints within a proven market — e.g. "women seeking trauma-aware Bible study" inside "Bible study apps." The critic rules on the slice, not on individual posts.

---

## 2. Module map

```text
src/evidentia/
  anchor.py         # NEW — market anchors with proof-of-market evidence
  scanners/
    reviews.py      # NEW — app store, G2, Product Hunt, subreddit-per-product
    hn.py           # DEMOTED — builder-voice only, not used for anchor loop
    reddit.py       # KEEP — shared by reviews.py for product-specific subs
    github.py       # DEMOTED — builder-voice, optional
  clusterer.py      # NEW — deterministic slice formation
  critic.py         # NEW — slice-level critic, replaces classifier.py for the anchor loop
  scoring.py        # UPDATED — slice-level verdict, next_test generator
  models.py         # UPDATED — Anchor, Slice, Verdict
  outputs.py        # NEW — verdict artifact writer
  classifier.py     # KEEP for single-signal diagnostic mode only
```

---

## 3. Data models (additive to `models.py`)

```python
@dataclass
class Anchor:
    market_name: str                         # "Bible study apps"
    incumbents: list[str]                    # ["YouVersion", "Bible.is"]
    proof_of_market: DemandSignal            # verified download/revenue/user quote
    cohort_hints: list[str] = field(default_factory=list)  # "women", "post-evangelical"
    primary_channel_queries: list[str] = field(default_factory=list)  # "site:reddit.com/r/exvangelical"

@dataclass
class Slice:
    slice_id: str                            # hash of normalized label + anchor
    anchor: Anchor
    label: str                               # LLM-generated, human-reviewable
    signal_ids: list[str]                    # DemandSignal ids in the cluster
    author_count: int                        # distinct authors
    dominant_subtype: str                    # missing_feature | cohort_exclusion | ...

class Verdict(str, Enum):
    KILL = "KILL"
    REFINE = "REFINE"
    PURSUE = "PURSUE"

@dataclass
class SliceVerdict:
    slice_id: str
    verdict: Verdict
    gates: dict[str, bool]                   # market_exists, slice_has_voices, slice_underserved, reachable, buildable
    heuristics: dict[str, float]             # competition_gap, buildability, reachability_strength
    refine_reason: str | None
    next_test: str | None                    # REQUIRED when verdict == REFINE
    evidence: list[DemandSignal]
```

**Invariant:** a `REFINE` without a `next_test` is a bug. Enforced in `critic.py` tests.

---

## 4. `anchor.py`

### Purpose
An anchor is a claim that a market exists, **with proof**. No anchor, no scan.

### Public API
```python
def load_anchors(path: Path) -> list[Anchor]: ...
def verify_anchor(anchor: Anchor) -> Anchor: ...  # re-runs auditor on proof_of_market
def anchor_from_dict(data: dict) -> Anchor: ...
```

### Storage
Hand-curated YAML at `anchors/<slug>.yaml`. Example:

```yaml
market_name: Bible study apps
incumbents: [YouVersion, Bible.is, Blue Letter Bible]
proof_of_market:
  verbatim_quote: "YouVersion has surpassed 500 million installs"
  source_url: https://youversion.com/press
  timestamp: 2024-11-01T00:00:00Z
  tier: TIER_1_FINANCIAL
  claim_type: EXISTING_SPEND
cohort_hints: [women, post-evangelical, youth]
primary_channel_queries:
  - site:reddit.com/r/Christianity "YouVersion missing"
  - site:reddit.com/r/exvangelical
```

### Validation rules
- `proof_of_market` must pass `auditor.verify_quote` with `proof_level == "fetched"`.
- `incumbents` min length 1, max length 10.
- Anchors that fail verification are skipped with a warning — they do not block other anchors.

### Week 2 deliverable
Five hand-curated anchors committed to `anchors/`:
1. Bible study apps
2. Meditation apps
3. Home-workout apps
4. Resume builders
5. Small-business invoicing

---

## 5. `scanners/reviews.py`

### Purpose
Pull **buyer-voice** complaints from sources where users already pay (or already use) the incumbent. This is what fixes the 100% HOLD problem — willingness_to_pay is implicit in the context, so the classifier is hunting switching intent and cohort exclusion, not initial spend.

### Source adapters (stdlib + existing providers)

| Source | Access | Priority | Notes |
|---|---|---|---|
| iOS App Store RSS reviews | Free, `https://itunes.apple.com/rss/customerreviews/...` | P0 | XML feed, parseable with stdlib |
| Product Hunt comments | HTML scrape via providers chain (Tavily/Brave) | P1 | Use `site:producthunt.com <incumbent>` query |
| G2 / Capterra review excerpts | Search-engine snippets only | P1 | Respect robots; do not crawl page bodies |
| Subreddit per product | Reddit API (already wired) | P0 | Query `r/<product>` and `"<product>"` in reddit search |
| YouTube comments on review videos | Optional for v1 | P2 | Defer unless time permits |

### Public API
```python
def listen(anchor: Anchor, limit: int = 50) -> list[DemandSignal]: ...
```

### Per-signal tagging
Every `DemandSignal` from `reviews.py` gets `signal_subtype`:
- `missing_feature`
- `usability_complaint`
- `cohort_exclusion`
- `pricing_complaint`
- `switching_intent`

Detection is deterministic regex + keyword, not LLM. Subtype drives clusterer grouping.

### Auditor integration
Every signal must pass `auditor.verify_quote` with `proof_level in {"fetched", "in_memory"}`. Reviews that can't be fetched (auth-walled G2 pages) → `in_memory` with the snippet from the search provider. `none` is discarded.

---

## 6. `clusterer.py`

### Purpose
Group `DemandSignal`s from a single anchor into `Slice`s. A slice is a candidate "Bible for X" hypothesis.

### Deterministic algorithm

1. **Normalize** each signal: lowercase, strip punctuation, remove incumbent names.
2. **Token Jaccard** similarity pair-wise over normalized quote + title. Threshold `>= 0.35`.
3. **Subtype gate**: signals only cluster if they share `signal_subtype`.
4. **Cohort keyword match**: if `Anchor.cohort_hints` intersect the normalized text, boost similarity by +0.15.
5. **Single-link clustering** on the resulting graph. Clusters with `author_count < 2` are dropped.

LLM is used **only** to label the resulting clusters:
```python
label = llm.generate_json(
    prompt=f"Label this cluster of complaints in one short phrase. Do not invent details.\nComplaints: {quotes}",
    schema={"label": "str"}
)["label"]
```

### Output
A `list[Slice]` per anchor. Typical yield: 3-15 slices per anchor.

### Why deterministic clustering
LLM-invented clusters drift. Jaccard + subtype gives reproducible, auditable slices. The LLM can only *name* what deterministic code already grouped.

---

## 7. `critic.py`

### Purpose
Rule on each `Slice`. Produce a `SliceVerdict`.

### Five gates

| Gate | Passes if |
|---|---|
| `market_exists` | `anchor.proof_of_market.verified` is True |
| `slice_has_voices` | `slice.author_count >= 3` |
| `slice_underserved` | Web search for `"<slice.label>" app OR saas` returns no top-3 result matching the label. LLM-classified with one structured call |
| `reachable` | `anchor.primary_channel_queries` OR detected cohort subreddit is non-empty, AND reachable channel has ≥ 2 complaints in the cluster |
| `buildable` | Heuristic: fewer than N=4 detected integrations/APIs in the feature request text |

### Verdict rule
```python
if not gates["market_exists"] or not gates["slice_underserved"]:
    verdict = KILL
elif all(gates.values()) and slice.author_count >= 5:
    verdict = PURSUE
else:
    verdict = REFINE
```

### `next_test` generator (the REFINE contract)
When verdict is REFINE, produce a concrete experiment:

| Failing condition | Template for `next_test` |
|---|---|
| `slice_has_voices` (2-4 voices) | "Post a specific question in {channel} asking users to share experiences with {pain}. PURSUE if ≥ 10 reply-level engagements in 7 days." |
| `slice_underserved` borderline | "Named competitor(s) found: {names}. Validate differentiation: ask 5 users of {named} whether {slice.label} would make them switch." |
| `reachable` weak | "Identify a primary channel: find a subreddit, newsletter, or conference tag with ≥ 1k members focused on {cohort}. PURSUE if found." |
| `buildable` weak | "Reduce feature scope to one atomic wedge. Re-run critic with narrowed label." |
| `author_count in [3,4]` but all gates pass | "Run landing-page test on {channel}. PURSUE if ≥ 50 signups in 7 days." |

`next_test` is a string with anchor/slice fields interpolated. It is required. Tests assert `verdict == REFINE implies next_test is not None`.

---

## 8. `outputs.py`

### Purpose
Write verdict artifacts per anchor run. Human-reviewable, grep-friendly.

### Files written per run
```text
outputs/<anchor_slug>/<timestamp>/
  anchor.json                # echoed anchor with verified proof
  signals.json               # all verified DemandSignals
  slices.json                # all slices with labels
  verdicts.json              # list[SliceVerdict]
  discard_log.json           # signals that failed auditor
  summary.md                 # human-readable roll-up: N slices, M PURSUE, K REFINE, L KILL
```

### `summary.md` shape
```markdown
# Bible study apps — 2026-04-24T14:22:00Z

**Proof:** "YouVersion has surpassed 500 million installs" (verified)
**Slices:** 7 | **PURSUE:** 0 | **REFINE:** 3 | **KILL:** 4

## REFINE — "Bible study for women recovering from religious trauma"
- 4 distinct authors, all from r/exvangelical
- Gates: market ✓ voices ✓ underserved ? reachable ✓ buildable ✓
- Why REFINE: slice_underserved borderline (found "Exvangelical Daily")
- Next test: Ask 5 Exvangelical Daily users whether a trauma-aware study tool would make them switch.
...
```

---

## 9. CLI additions

```bash
evidentia anchor list
evidentia anchor verify <slug>
evidentia hunt <slug> [--limit N] [--dry-run]         # = anchor+listen+cluster+critic+outputs
evidentia hunt-all [--limit N]                         # iterate anchors/
```

`scan / classify / score / audit` stay for single-signal diagnostics but are no longer the primary path.

---

## 10. Test plan

### New unit tests
- `tests/unit/test_anchor.py` — YAML load, verification, malformed anchors skipped.
- `tests/unit/test_reviews_scanner.py` — RSS parser, subtype tagger, auditor integration (mocked fetch).
- `tests/unit/test_clusterer.py` — Jaccard threshold, subtype gate, single-link correctness, cohort boost.
- `tests/unit/test_critic.py` — each gate, each verdict path, next_test templates, **REFINE-without-next_test is a test failure**.

### New integration tests
- `tests/integration/test_hunt_pipeline.py` — end-to-end with fixture anchor + fixture reviews → verdicts on disk. Deterministic.
- `tests/integration/test_hunt_discard_log.py` — unverifiable reviews land in `discard_log.json`.

### Acceptance
- `tests/acceptance/test_hunt_cli.py` — `evidentia hunt <fixture-slug> --dry-run` produces all six output files.

### Live (marked, not in CI)
- `tests/live/test_hunt_live.py` — marked `@pytest.mark.live`. Runs one anchor against real iOS RSS + Reddit. Asserts schema validity only, not verdict outcomes.

---

## 11. Phased delivery

### Week 2 — anchor + listen
- `anchor.py`, five hand-curated anchors, verification path.
- `scanners/reviews.py` with iOS RSS + subreddit adapters only.
- Auditor integration with `proof_level`.
- Tests: unit + integration on fixtures.

**Done when:** `evidentia hunt bible-study-apps --dry-run` writes verified signals to disk.

### Week 3 — cluster + critique
- `clusterer.py` with deterministic grouping.
- `critic.py` with five gates, three verdicts, `next_test` templates.
- `outputs.py` with artifact writer.
- Tests: unit + integration + acceptance.

**Done when:** one anchor run writes `verdicts.json` and `summary.md` with plausible slices.

### Week 4 — first real run + productization gate
- Run all five anchors live.
- Hand-review every REFINE — does the `next_test` make sense?
- Pick the strongest PURSUE (or strongest REFINE with cheap next_test).
- **Run the test manually.** This is the validation of the tool itself.
- If the test produces real signal, ship a wedge manually (still no builder).

**Done when:** one real-world experiment has been executed based on an evidentia verdict.

---

## 12. Non-goals for this doc

- **No builder / deployer / tracker.** Deleted in Week 1. Will be reconsidered only after Section 11 Week 4 produces a shipped wedge.
- **No UI.** CLI only. Productization gate per `NEXT_PIVOT.md` Section 7.
- **No LLM-as-judge.** LLM labels clusters and classifies borderline gates (`slice_underserved`). Verdict logic is deterministic.
- **No web crawling at scale.** Respect robots; use search-engine snippets where TOS forbids crawl.

---

## 13. Risks

| Risk | Mitigation |
|---|---|
| iOS RSS rate limits / deprecation | Cache aggressively; switch to scraping only if RSS breaks |
| Subreddit API rate limits | Batch queries; existing provider chain already handles Reddit |
| Clustering produces over-broad slices | Jaccard threshold tunable; test corpus of known-good slices |
| LLM labeling drift | Label only; cluster membership is deterministic, so labels can be regenerated without data loss |
| `slice_underserved` false positives | Require search verification step; borderline → REFINE, never auto-KILL |
| Anchor list goes stale | Quarterly review; anchors are short-lived assets |

---

## 14. Open decisions

1. **Subtype taxonomy:** current list of five subtypes is a guess. Revisit after Week 2 data.
2. **Jaccard threshold 0.35:** tune on real data in Week 3.
3. **PURSUE voice threshold (5):** possibly too low. Reassess after first real run.
4. **Anchor refresh cadence:** if an incumbent pivots, cohort_hints may shift. Manual review for now.
5. **`buildable` heuristic:** integration-count is crude. Acceptable for v1; revisit once we have real PURSUEs to compare.
