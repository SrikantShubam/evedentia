# Evidentia Live Scan — External Reviewer Audit
**Query**: `expense tracking` | **Sources**: HN, Reddit, GitHub | **Max per source**: 3
**Reviewer**: External technical review — no prior context assumed
**Date**: 2026-04-15

---

## Verdict: 3 / 10

The pipeline is structurally present but effectively non-functional as a demand-signal detector.
Zero PURSUE results on a legitimate, high-interest query (`expense tracking`) is the loudest signal
a system can produce that something is broken. Every finding below ties back to that single fact.

---

## The Good (what actually works)

| # | What | Why it matters |
|---|------|----------------|
| G1 | Multi-source fetching works | HN, Reddit, GitHub all returned responses |
| G2 | Freshness decay formula exists | Correct decay over 365 days |
| G3 | Hard-gate concept is sound | Binary pass/fail before heuristic scoring is the right architecture |
| G4 | Auditor fetches live URLs | Fetched proof > in-memory proof is a correct hierarchy |
| G5 | Dedup + rank pipeline is plumbed | `dedupe_by_cluster` → `rank_opportunities` flow is correct |

---

## The Bad (design flaws producing silent wrong answers)

### B1 — 100% HOLD rate means the classifier is lying or the LLM is misconfigured

All 9 items return HOLD. The `score_opportunity` function only returns HOLD when at least one of
`willingness_to_pay`, `distribution_channel`, `data_feasibility` is not `"pass"`. Three questions:

1. **Which gate is failing for every single item?** The UI does not show gate verdicts, so the
   user cannot diagnose this. This is a usability failure — HOLD without a reason is a black box.
2. **Why does "Show HN: Kontora — Self-hosted finance dashboard for freelancers in Germany" fail?**
   Its text explicitly discusses SaaS vs open-core pricing, states a reachable audience (freelancers
   in Germany), and uses publicly accessible data. This is a textbook PURSUE signal. If it's HOLD,
   the classifier is wrong.
3. **The uniform 0.80 / 0.70 / 0.60 scores across 7 of 9 items are damning.** These are the
   exact example values embedded in the classifier prompt. The LLM is copy-pasting the template for
   numeric fields. That means every numeric score is fabricated, not reasoned.

**Root cause**: The classifier prompt embeds literal example values (`"competition_gap": 0.8,
"buildability": 0.7, "reachability_strength": 0.6`) in its required output format. Most LLMs
will anchor on those values rather than reason from the source text.

### B2 — GitHub Issues is the wrong data source

GitHub issue search for "expense tracking" returns implementation tickets inside developer
repos — feature requests that developers wrote for their own products. These are supply-side
artefacts, not end-user demand signals. The three GitHub results:

- `github:4245049346` — body: "Expense Tracking" (2 words, no content)
- `github:4109102537` — onepointhub developer feature spec with acceptance criteria
- `github:4203140037` — school project repo

None of these represent a person wanting to pay for something. The GitHub scanner is structurally
mis-aimed. It should target repo discussions, issue *comments* with engagement, or explicit
"request" labels — not title-matching issues in any repo.

### B3 — Duplicate results pass through dedup

The iOS car maintenance app ("New iOS app for tracking car projects and maintenance") appears twice:
- `reddit:/r/iosapps/comments/1sm74ir/...`
- `reddit:/r/iOSAppsMarketing/comments/1sm731e/...`

Different permalink → different `cluster_id` → dedup does not catch it. The dedup logic is
purely ID-based. Same content posted across subreddits produces duplicate opportunities.

### B4 — HTML entities in verbatim quotes are not decoded

The HN `source_text` is raw HTML from the Algolia API. The verbatim quote for the Kontora item
contains `&#x27;` (apostrophe) and `&#x2F;` (slash). This means:

1. The LLM classifier receives HTML-encoded text as its signal, degrading classification quality.
2. The auditor's `verify_quote` check does a substring match — the raw HTML quote will not match
   a decoded page body, causing false verification failures.

`scan_hn_live` must HTML-decode `story_text` before using it.

### B5 — Keyword search has zero semantic filtering

"Show HN: Is Hormuz open yet?" appears in expense tracking results because the post body mentions
"expense" somewhere. HN Algolia full-text search returns false positives. There is no relevance
threshold, no title-match weighting, no minimum score gate on the search response itself.

### B6 — No minimum signal quality threshold

A GitHub issue with title "Expense Tracking" and body "Expense Tracking" passes through
verification (the verbatim quote matches the source text trivially — the quote IS the title).
The auditor's `verify_quote` is exploitable by degenerate content where the "quote" is the title.

---

## The Ugly (fundamental conceptual misfires)

### U1 — Buyer signals vs builder signals — the classifier cannot tell them apart

The classifier prompt asks for `willingness_to_pay = pass if the signal contains clear spend
intent, pricing discussion, budget mention`. But the Kontora HN post is a **builder** discussing
their own pricing model, not a **buyer** expressing intent to pay. The pipeline treats both as
equivalent. This is a category error that no amount of prompt tuning will fully fix — the scanner
needs to prefer buyer-perspective sources (complaints, "looking for", budget mentions) over
builder-perspective sources (Show HN, launching, "I built this").

### U2 — SaveSage Pro promotional content is treated as a market signal

A Reddit post from r/LooteraShopper offering ₹74/month with cashback codes is pure marketing spam.
It has no demand signal value. The pipeline has no spam/promotional filter. Any sub with promotion
rules ignored will pollute the results.

### U3 — The output display shows heuristic scores for HOLD items

The UI renders `competition_gap`, `buildability`, `reachability_strength` for items where verdict
is HOLD. These scores are meaningless for HOLD — the hard gates failed so the heuristic never ran.
Displaying them suggests false confidence that the item was properly evaluated. The UI should show
the gate results (which gate failed and why) instead of the heuristic scores when verdict is HOLD.

### U4 — The pipeline treats all sources equally

An HN post with 400 upvotes and 200 comments is treated identically to an HN story with 0 points.
A Reddit post with 1000 karma from a signal-rich subreddit is equivalent to a 1-point post from a
promotional sub. Engagement volume is a demand signal in itself — the scoring model ignores it.

---

## Failure Summary Table

| ID | Severity | Category | One-line Description |
|----|----------|----------|---------------------|
| F1 | CRITICAL | Classifier | Uniform 0.80/0.70/0.60 scores — LLM echoing prompt example values |
| F2 | CRITICAL | Classifier | All HOLD — gate failure diagnosis invisible to user |
| F3 | CRITICAL | Source | GitHub Issue scanner returns implementation tickets, not demand |
| F4 | HIGH | Scanner | HTML entities not decoded in HN `source_text` / `verbatim_quote` |
| F5 | HIGH | Scanner | No relevance filtering — off-topic results pass through |
| F6 | HIGH | Dedup | Content-identical cross-platform posts not deduplicated |
| F7 | HIGH | Classifier | No buyer vs builder signal distinction |
| F8 | MEDIUM | Scanner | No minimum engagement filter (upvotes, comments) |
| F9 | MEDIUM | UI | HOLD items show heuristic scores instead of gate failure details |
| F10 | MEDIUM | Scanner | Promotional/spam content has no filter |
| F11 | LOW | Auditor | Degenerate quote (title = quote) trivially passes verification |

---

## Completion Score: 38 / 100

| Area | Score | Notes |
|------|-------|-------|
| Architecture / plumbing | 75/100 | Correct pipeline shape, proper stage separation |
| Classifier accuracy | 5/100 | 100% HOLD, uniform scores = broken in practice |
| Source quality | 20/100 | GitHub wrong source type; no spam/relevance filter |
| Deduplication | 40/100 | ID-based only; cross-platform duplicates pass through |
| UI signal clarity | 25/100 | Gate reasons hidden; heuristic scores shown for HOLD |
| Scanner data quality | 35/100 | HTML entities, no engagement weighting |
| **Overall** | **38/100** | Zero correct PURSUE on a valid query |
