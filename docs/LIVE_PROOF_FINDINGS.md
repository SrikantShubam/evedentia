# Live Proof Findings — 2026-07-19

Three real markets run end-to-end (research → bridge → tournament → memo) with an
honest solo-founder profile (`outputs/solo_profile.json`, $2k build budget) and
verified-working providers (Groq/OpenRouter/Tavily/DDG).

**Engine-gate verdict: FAIL 3/3.** Every market produced a 100% KILL rate at the
same gate for the same mechanical reason, and the final memo is empty boilerplate.
This contradicts ACTIVE_ARCHITECTURE.md's "passed 2/3 markets" claim.

## Runs

| Market | Query | Evidence | Ideas | Verdicts |
| --- | --- | --- | --- | --- |
| SMB invoicing | "invoicing software for small service businesses" | 40 web snippets (Reddit 403-blocked) | 2 | 2× KILL @ budget_owner_identifiable |
| Meditation apps | "meditation apps" | 93 real App Store reviews | 4 | 4× KILL @ budget_owner_identifiable |
| Resume builders | "resume builder for career changers" | 54 web snippets | 3 | 3× KILL @ budget_owner_identifiable |

Artifacts: `outputs/live_research_*.json`, `outputs/live_ideas_*.jsonl`,
`outputs/live_tournament_*.json`, `outputs/live_memo_meditation.md`.

## Root causes, ranked

### 1. Research layer fabricates evidence for non-app markets (research.py)
- Web competitor "discovery" splits search-result titles: 7 of 8 invoicing
  "competitors" were keyword phrases ("Free invoicing software for small
  businesses"), not companies. Only Invoice Ninja was real.
- "Reviews" for web competitors are search snippets from a
  `"{name} review complaint problem"` query. Listicle marketing copy
  ("Best billing & invoicing software: 1. Bookipi...") was classified as a
  BILLING_ABUSE user complaint at 0.8 confidence; site chrome ("Sign In Sign
  Up Now") became an ADS complaint. The n=11 "HIGH severity opportunity" was
  11 pieces of vendor marketing.
- Severity is a constant, not a measurement: app-store reviews are hardcoded
  rating=2 → severity always 7; web snippets → severity always 5.
- Every report appends "All claims linked to source reviews." unconditionally.
- **The App Store path is the one genuinely good component**: meditation run
  found real competitors (Headspace, Calm, Insight Timer) and 93 real
  complaints with verbatim quotes ("charged $60 anyways", "playlists broken
  for weeks"). Classifier labels are rough (redesign complaint → ADS;
  billing complaint → TRUST_PRIVACY) but the underlying evidence is real.

### 2. Bridge launders provenance and flattens ideas (tournament/qualify + bridge)
- All web_search snippet evidence is relabeled `cited_evidence`, which is in
  FIRST_PERSON_PROVENANCES — marketing copy upgraded to first-person voice.
- FIRST_PERSON_PROVENANCES also includes `llm_inference` and
  `llm_educated_guess`: LLM guesses count as human voices. This guts the
  anti-hallucination contract.
- Idea labels are raw gap-description strings ("Multiple users report
  BILLING_ABUSE issues with existing Free invoicing software...").
- "Named kill condition per idea" (spec's flagship tenet) is the same
  boilerplate on every idea: `{"description": "No market evidence"}`.
- Gate profile auto-detection assigned `b2b_workflow` to consumer meditation
  apps, routing Headspace complaints through procurement gates.

### 3. Tournament gates are vacuous and vocabulary-mismatched (tournament/gates.py)
- Gates are keyword matches on the idea's own self-generated text — the
  system grades its own homework. `willingness_to_pay` passes iff the idea
  text contains pay/price/budget/subscription/invoice as whole words.
- The bridge's label vocabulary never contains those words:
  "invoicing" ≠ "invoice", "PRICING" ≠ "price" under \b matching. Result:
  `budget_owner_identifiable` fails for 9/9 ideas across all markets — a
  structural 100% kill rate caused by two components not sharing a vocabulary.
- Three different business questions (complaint_signal, repeat_purchase,
  procurement_path) collapse to the same check: "has ≥1 evidence id".
- Gate "confidence" values are hardcoded per-gate constants; the 0.93 shown
  on every KILL is a baseline, not a measurement.

### 4. The memo is not a sellable artifact (tournament/memo.py)
20 lines of template: "Winner: none / for: No winner evidence available /
against: No winner available." No market context, no quotes, no competitor
names, no reasoning. Nobody pays for this.

### 5. Misc
- `run_provider_smoke` reports success on key *presence* without calling the
  API — a smoke test that cannot fail meaningfully.
- Reddit scraping via public search.json is 403-blocked; one of three
  first-person evidence sources is silently dead (was swallowed by
  `except: pass` until this run).

## What is worth salvaging

The App Store review-mining path produces real, quotable, verifiable user
pain for any app-shaped market. That is the sellable core. The tournament,
as implemented, subtracts value: it destroys real evidence with fake gates.

## Implications for the commercial plan

The "$149 validation memo" cannot ship on this pipeline. Before any pitch:
1. Fix the bridge↔gate vocabulary mismatch (or replace keyword gates with
   evidence-based checks) so verdicts respond to evidence, not labels.
2. Restrict FIRST_PERSON_PROVENANCES to actual first-person sources.
3. Make the memo assemble the real assets: verbatim quotes, competitor list,
   complaint clusters, source links.
4. Either fix web-market research (real entity extraction, real review
   sources e.g. Trustpilot/G2) or scope the product honestly to app markets.
