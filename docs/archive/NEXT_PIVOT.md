# NEXT_PIVOT.md — Evidentia: Niche Hunter

> **Refined thesis:** Don't validate arbitrary ideas. Find underserved slices within *already-proven* markets. A billion-download Bible app tells you the market exists — your job is to find the "Bible for X" that hasn't been built yet, and prove real users are asking for it.
>
> **Role:** Internal tool. Harsh critic. Three verdicts only: **KILL / PURSUE / REFINE**.

**Drafted:** 2026-04-17
**Supersedes:** `final_pivot.md` (demand-to-product pipeline was too broad)

---

## 1. Why `main` Drifted

`final_pivot.md` expanded scope from *validation* to *scan → spec → build → ship → track*. Build, ship, and track are stubs (see `REVIEW_REPORT.md` FP-09 to FP-11). Scope expanded faster than the validation core matured. Meanwhile the **actual dream** — finding underserved niches inside proven markets — was never built.

| What was dreamed | What was built |
|---|---|
| Start from a proven market, find the unmet slice | Scan HN/Reddit firehose for generic complaints |
| Harsh critic returns KILL / PURSUE / **REFINE** | Pipeline returns SKIP / HOLD / PURSUE (no REFINE) |
| Evidence rooted in real user listening | 100% HOLD on live data (FP-01) |
| Verified quotes from pages | Substring check on scanner's own response text (FP-02) |
| Anti-slop validator | Validator that builds stub Next.js apps |

**Cut build, ship, track.** They distract from the thing that isn't working yet: the critic.

---

## 2. Three Verdicts, Defined

| Verdict | Meaning | Required evidence |
|---|---|---|
| **KILL** | Market doesn't exist, or the slice is already saturated | Hard gate fail OR incumbent owns the niche with no dissatisfaction signal |
| **PURSUE** | Proven market + underserved slice + reachable audience | All hard gates pass AND competition gap ≥ 0.6 AND ≥ 3 distinct buyer voices |
| **REFINE** | Real signal but current framing is wrong | Hard gates pass but niche is too broad/too narrow, OR dissatisfaction signal without spend signal — output a **narrowed hypothesis** |

**REFINE is the key missing verdict.** It is not purgatory. It must produce:
- Why the current framing fails
- A narrower (or adjacent) hypothesis to test next
- The specific evidence gap that would flip it to PURSUE

---

## 3. Niche Hunter: New Core Loop

Replace generic "scan a domain" with **market-anchored niche discovery**:

```text
anchor      — pick a proven market (app, category, incumbent)
listen      — pull user reviews, complaints, feature requests from that market
cluster     — group complaints into candidate underserved slices
critique    — apply hard gates + REFINE logic per slice
verdict     — KILL / PURSUE / REFINE per slice, with narrowed hypothesis
```

### Anchor sources (new)

These matter more than HN/Reddit for the "Bible for Women" pattern:

- **App store reviews** (iOS RSS feeds are free, Android via scraping)
- **Product Hunt comments** on category leaders
- **G2 / Capterra** review sections (free-tier scraping)
- **YouTube comments** on popular review videos in the category
- **Subreddit complaints** specifically about a named incumbent (`r/productname`, `site:reddit.com "X is missing"`)

HN and GitHub stay, but demoted — they're builder-voice sources, not buyer-voice.

### Why this fixes the 100% HOLD problem

The current classifier sees random HN posts with no spend context and correctly marks them fail. Anchoring to a **paid incumbent** means every complaint is *already* a paying user — willingness_to_pay is implicit and you're hunting for *switching intent*, not *initial intent*. Much higher signal density.

---

## 4. The Harsh Critic — Concrete Architecture

### A. Anchor module (new: `anchor.py`)
```python
Anchor = {
  "market_name": "Bible study apps",
  "incumbents": ["YouVersion", "Bible.is", "Blue Letter Bible"],
  "proof_of_market": {
    "downloads": "500M+ YouVersion",
    "source_url": "...",
    "verbatim_quote": "..."
  }
}
```
Market proof is itself an `EvidenceObject`. No anchor without a verified downloads/revenue/users quote. **No anchor, no scan.**

### B. User-listening scanner (new: `scanners/reviews.py`)
- Input: anchor
- Output: complaint-class `DemandSignal`s from app stores, G2, subreddits
- Each signal tagged `signal_subtype`: `missing_feature`, `usability_complaint`, `cohort_exclusion` (e.g. "no content for women"), `pricing_complaint`

### C. Niche clusterer (new: `clusterer.py`)
Groups signals into **candidate slices**. Each slice = one "Bible for X" hypothesis. Cluster by:
- Shared missing feature
- Shared excluded cohort
- Shared workflow pain

LLM used only for labeling clusters, never for inventing them. Cluster membership is deterministic (embedding similarity + keyword overlap).

### D. Critic (rewritten classifier)
Per slice, not per raw signal. Gates:

| Gate | Passes if |
|---|---|
| `market_exists` | Anchor has verified downloads/revenue proof |
| `slice_has_voices` | ≥ 3 distinct authors in the cluster |
| `slice_underserved` | No named incumbent already targeting this slice (web search check) |
| `reachable` | The cohort has an identifiable channel (subreddit, conference, newsletter) |
| `buildable` | Wedge is feasible for a solo builder in < 30 days |

**KILL** if market_exists fails OR slice_underserved fails.
**PURSUE** if all pass AND ≥ 5 distinct buyer voices.
**REFINE** otherwise: output narrowed hypothesis explaining which gate is close-but-not-there.

### E. Verdict artifact (new shape)
```json
{
  "anchor": "Bible study apps",
  "slice": "Bible study for women recovering from religious trauma",
  "verdict": "REFINE",
  "evidence": [...],
  "gaps": {
    "slice_underserved": "unclear — two small competitors found",
    "reachable": "pass — r/exvangelical, r/deconstruction"
  },
  "refined_hypothesis": "Narrow to post-evangelical women 25-40. Validate via r/exvangelical poll.",
  "next_test": "Post a landing page with email capture in r/exvangelical. PURSUE if ≥ 50 signups in 7 days."
}
```

**REFINE must produce a next_test.** A verdict without a concrete next action is the same failure mode as the current HOLD bucket.

---

## 5. Fixes for Current Issues (concrete, mapped to REVIEW_REPORT)

| Issue | Fix | Effort |
|---|---|---|
| FP-01 100% HOLD rate | Anchor-first scanning (Section 3). Plus: log 10 raw LLM responses, tune `_normalize_gate` to actual vocabulary. Plus: structured-output tool-use (JSON schema enforcement) instead of prompt-begging | 1 day |
| FP-02 fake auditor | Implement `urllib.request` fetch with 50KB cap. Tag signals `proof_level: fetched` vs `in_memory`. Discard anything that can't be fetched after 2 retries | 3h |
| FP-03 `LIVE_SCANNERS["hn"] = None` | One-line registry fix + integration test that iterates registry | 15m |
| FP-05 `can_deploy` boolean | Strict `is True` check | 15m |
| FP-06 models unused | Validate `DemandSignal` at scanner boundary, not at spec-write | 2h |
| FP-10 empty spec writer | **Drop spec_writer entirely for now.** Verdicts are the product. PRDs come later, manually, after a PURSUE | — |
| Build / ship / track are stubs | **Delete `builder.py`, `deployer.py`, `tracker.py`.** Out of scope for the critic. Add back only after first real PURSUE is validated manually | 30m |
| No REFINE verdict | Add to `scoring.py` verdict enum + critic logic | 4h |
| No niche discovery | Build `anchor.py` + `scanners/reviews.py` + `clusterer.py` | ~1 week |

---

## 6. Revised File Tree

```text
src/evidentia/
  cli.py
  models.py               # Anchor, DemandSignal, Slice, Verdict
  providers.py            # keep
  anchor.py               # NEW — anchor validation
  scanners/
    reviews.py            # NEW — app stores, G2, reddit-by-product
    hn.py                 # keep, demoted
    github.py             # keep, demoted
    reddit.py             # keep, demoted
  auditor.py              # rewrite: real fetch
  clusterer.py            # NEW — slice discovery
  critic.py               # replaces classifier.py
  scoring.py              # add REFINE verdict
  outputs.py              # verdict artifact writers

# DELETE
  builder.py              # out of scope
  deployer.py             # out of scope
  tracker.py              # out of scope
  spec_writer.py          # out of scope until first PURSUE
  server.py               # premature
```

Roughly 40% of existing Python disappears. The surviving code gets sharper.

---

## 7. Phased Plan (weeks, not months)

### Week 1 — Reset
- Delete builder/deployer/tracker/spec_writer/server
- Fix FP-01, FP-02, FP-03, FP-05
- Add REFINE verdict + narrowed-hypothesis output
- All tests green on fixtures

### Week 2 — Anchor + review scanning
- `anchor.py` with ≥ 5 hand-curated anchors (Bible, meditation, fitness, invoicing, resume builders)
- App store RSS scanner (iOS is free)
- Subreddit-by-product scanner
- Quote verification required

### Week 3 — Clustering + critic
- Deterministic clustering of complaints per anchor
- Critic runs per slice, not per signal
- Produces KILL / PURSUE / REFINE with evidence trace

### Week 4 — First real run
- Run against 5 anchors
- Hand-review every REFINE output — does the narrowed hypothesis make sense?
- Ship the best PURSUE manually (no builder needed)
- This is the validation of the tool itself

**Gate to productization:** the tool has produced at least one PURSUE that led to a real shipped wedge with real signups. Until then, no UI, no tiers, no open source launch.

---

## 8. Open Questions

1. **Anchor discovery:** hand-curated at first, or also scanned? Recommend hand-curated — anchors are rare and precious, not a firehose.
2. **LLM role:** keep strictly as a labeler (cluster names, gap summaries). Never as a judge. The critic logic is deterministic.
3. **Freshness:** app store reviews skew recent. Reddit threads can be years old. Decay function needs per-source calibration.
4. **Kill the keyless fallback?** DuckDuckGo results are too noisy for anchor verification. Tavily or Brave should be mandatory for Week 2+.

---

## 9. What This Buys You

- **A working critic** instead of a broken pipeline
- The **REFINE verdict** that was missing — where most real ideas actually land
- **Market-anchored discovery** — the "Bible for Women" pattern, finally implemented
- **Shorter codebase, sharper scope** — the parts that work stay, the parts that drift go
- A clear **productization gate**: one real PURSUE shipped before anything is sold

The original dream, minus the drift.
