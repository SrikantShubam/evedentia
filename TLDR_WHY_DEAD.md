# TLDR: Why Evidentia is dead

**Verdict: kill the project. 2026-07-20.**

## The one-line reason

Not the code. The founder pattern: three full rebuilds (`kimi/` → `codex/` →
`main/`), four rewritten product visions, ~6+ months, ~6.5k LOC, 242 tests —
and **zero conversations with a human who might pay**. The one thing that was
never tried is the only thing that was ever going to answer whether this is
a business. That's not a coincidence you fix by rebuilding again.

## What was actually true about the code (for the record)

- The engine was real and, after a day of fixes on 2026-07-20, technically
  worked: app-review mining produced genuine, verbatim, quotable user pain
  (meditation market: 93 real reviews, correctly discriminated PURSUE_SPIKE
  verdicts). See `main/docs/LIVE_PROOF_FINDINGS.md`.
- Before those fixes, the tournament engine killed 9/9 ideas across 3 live
  markets for a mechanical reason (bridge/gate vocabulary mismatch) that had
  nothing to do with market quality — the "84 tests pass, engine gate passed
  2/3 markets" claims in `ACTIVE_ARCHITECTURE.md` did not survive a live run.
- Docs across the repo repeatedly claimed features/rewrites as done that the
  code didn't match (`docs/MASTER_DOC_INDEX.md` itself documents 21 prior
  discrepancies found by an internal reviewer). This wasn't a one-time slip;
  it was the recurring failure mode of the project.
- None of this — bugs, doc drift, missing SaaS layer (no auth, no billing,
  no deploy) — was ever the real blocker. All of it was fixable in days.
  What was never attempted, across three rewrites, was asking a stranger
  for $49.

## The actual test that was proposed and never run

Pick 3 app-market memos, personally pitch 10 real people, ask for money
upfront. Cost: ~$50, ~2 weeks, zero more code. If a founder won't run that
after being told directly it's the only test that matters, the idea's
technical merit is irrelevant — distribution and sales motion, not
engineering, was always the constraint, and rebuilding the engine a fourth
time would just repeat the pattern instead of testing it.

## What's salvageable if anyone ever revisits this

- The App Store review-mining path (`main/src/evidentia/scanners/reviews.py`
  + `research.py`'s app_store branch) is the one component that produced
  real, non-fabricated evidence. If this idea ever comes back, it should
  start with a sale of that output, not another scan of the market.
- Full technical audit, live-run evidence, and fix history: see
  `main/docs/LIVE_PROOF_FINDINGS.md`, `main/docs/KEY_ROTATION.md`, and
  commits `8bbf400`..`45a2fe5` on `feat/edge-tournament-phase0`
  (pushed to `github.com/SrikantShubam/evedentia`).

## What is not being blamed

The idea itself — "mine real app reviews into evidence-backed validation
reports" — was never disproven by a market. It was simply never tested by
the one person positioned to test it. That is the actual cause of death.
