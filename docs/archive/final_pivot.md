# final_pivot.md - Evidentia: Demand-to-Product Pipeline

> Pivot: from "validate someone else's idea" to "find credible demand, turn it into a spec, then optionally build and ship."
>
> Internal tool first. Productize only after using it to ship real products.

**Last updated:** 2026-04-14  
**Status:** PRE-IMPLEMENTATION - rewritten to align with the repo evidence

---

## 1. What Changed

### Why the prior direction was weak

| Prior pattern | Problem |
|---|---|
| "Bring me your idea and I will validate it" | Weak ICP and low leverage; it ends in a verdict, not momentum |
| Spend-first hunting on the public web | Strong spend proof is rare in public sources, so discovery stalls too early |
| Readiness claims ahead of proof | Existing docs mixed simulations, dry-runs, and "production ready" language too loosely |
| Validation without execution | Even a correct verdict is still just an opinion if it never becomes a spec or product |

### Why this pivot is stronger

| New pattern | Advantage |
|---|---|
| Find demand that already exists | Pain, requests, and complaints are good discovery signals for ranking |
| Use the tool internally first | Clear user and feedback loop: if it saves time, it is useful immediately |
| Move beyond verdicts | The system can progress from evidence to spec, then optionally into build/ship |
| Delay productization | "We used this to ship products" is stronger than "trust the framework" |

### Pipeline

**Scan -> Score -> Spec -> Build -> Ship -> Track**

This file treats those as staged layers, not equally-proven capabilities.

---

## 2. Evidence Boundary

### What the existing repo history supports

The current markdown corpus supports these foundations:

- Evidence collection patterns
- Verification/auditing concepts
- Deterministic gate-first scoring
- Prosecutor/reality-spike style skepticism
- CLI-first workflow design

### What this pivot adds

These are new product-direction additions, not inherited proof from Codex/Kimi:

- Product spec generation
- App/code generation
- Deployment workflows
- Traction tracking

That distinction matters. Existing repo docs justify reusing parts of the evidence engine. They do **not** prove that builder, deployer, or tracker components already exist at production quality.

---

## 3. Product Definition

Evidentia becomes an internal demand-to-product pipeline that:

1. Scans public sources such as Reddit, Hacker News, GitHub, and the open web for pain, requests, complaints, and explicit spend where available.
2. Scores opportunities using inherited hard gates plus additional ranking heuristics.
3. Writes a product spec for a chosen opportunity.
4. Optionally generates a deployable wedge product from that spec.
5. Optionally deploys it.
6. Optionally tracks early traction signals.

### What it is not

- Not a market-report generator
- Not a fully autonomous startup builder
- Not a replacement for human approval before build, deploy, or outreach

### User flow

```text
evidentia scan --domain fintech
  -> ranked opportunities
evidentia spec --opportunity opp_003
  -> PRD + tech spec
evidentia build --spec specs/opp_003.json
  -> generated app
evidentia ship --target vercel
  -> deployment URL
evidentia track --project opp_003
  -> visits, signups, revenue proxy metrics
```

---

## 4. Scoring Model

### Inherited hard gates

This pivot keeps the inherited Codex/Kimi gate-first semantics. The hard gates remain:

1. `willingness_to_pay`
2. `distribution_channel`
3. `data_feasibility`

If any hard gate fails:

- verdict = `HOLD` or `SKIP`
- score = `0`
- no automated build should proceed

### New ranking heuristics

These are useful, but they are **not** hard gates:

- `competition_gap`: evidence of dissatisfaction with incumbents
- `buildability`: whether a small wedge looks realistic for agent-assisted build
- `reachability_strength`: how cheap and direct the channel appears

### Mapping from Codex to Evidentia

| Codex concept | Evidentia concept |
|---|---|
| `EvidenceObject` | `DemandSignal` |
| `AuthorityTier` | `SignalStrength` |
| `ClaimType` | `SignalType` |
| `KILL / REJECT / SURVIVE` | `SKIP / HOLD / PURSUE` |
| `willingness_to_pay` | explicit spend evidence before `PURSUE` |
| `distribution_channel` | reachability evidence |
| `data_feasibility` | feasibility/buildability evidence |

### Important clarification

Pain, requests, and complaints are valid **discovery** signals. They are not by themselves enough for a `PURSUE` verdict. `PURSUE` still requires the inherited hard-gate evidence.

---

## 5. Technical Architecture

### Runtime stack

| Layer | Choice | Notes |
|---|---|---|
| Runtime | Python 3.12+ | Reuse existing repo patterns and LLM tooling |
| CLI | Click + Rich | Good fit for internal workflow |
| Generated app | Next.js 15 | Default wedge product target |
| Data store | SQLite first | Move later only if the tool proves useful |
| Deployment | Vercel default, Railway fallback | Keep the first path simple |
| LLM provider | Claude primary | Best fit for tool use and code generation |
| Search | Tavily primary, keyless fallbacks available | Avoid blocking on paid APIs |

### System shape

```text
scan -> verify -> score -> spec -> build -> ship -> track
```

Where:

- `scan/verify/score` are the core evidence engine
- `spec` is the first new layer
- `build/ship/track` are optional follow-on layers

---

## 6. Anti-Hallucination Contract

Every factual claim must remain traceable to fetched or fixture-backed source material.

### Rules

| Rule | Enforcement |
|---|---|
| No signal without URL | Schema requires `source_url` |
| No signal without verbatim quote | Schema requires `verbatim_quote` |
| Quotes must exist on page or fixture | Verification step required |
| LLMs may classify, not invent evidence | Search/fetch creates candidates; LLM labels them |
| Structured output only | JSON/tool output required |
| Refuse-if-unsure | Null classification allowed |
| Invalid data is rejected, not repaired by prose | Schema validation between phases |

### Verification pipeline

```text
Search result
  -> fetch page or fixture text
  -> verify quote exists
  -> classify with structured output
  -> validate schema
  -> write DemandSignal
```

Anything that fails verification goes to `discard_log.json` with a reason code.

---

## 7. Subagent Pattern

Use subagents for narrow tasks, not for open-ended autonomy.

### Recommended pattern

- Small parallel agents for source-specific scanning
- A deterministic verification pass over fetched text
- One synthesis/spec-writing agent after evidence is stable
- Main orchestrator decides phase boundaries and writes artifacts

### Anti-patterns

- Agent chains deciding their own next steps
- Passing shared state through prompt text
- Long autonomous loops with no artifact boundary

---

## 8. Test-First Plan

### Proof levels

This project must distinguish three proof levels:

1. **Fixture proof**: deterministic tests against saved inputs
2. **Dry-run proof**: provider selection, query planning, and pipeline wiring
3. **Live proof**: real external retrieval and one real shipped product

Never describe fixture proof as live proof.

### Test structure

```text
tests/
  unit/
  integration/
  acceptance/
  fixtures/
```

### Acceptance criteria examples

- A known domain with strong evidence can produce at least one `PURSUE`
- A nonsense domain does not produce `PURSUE`
- Every output signal traces to source material
- Failed verification appears in `discard_log.json`
- Ranking heuristics can reorder two otherwise-valid opportunities without changing hard-gate semantics

---

## 9. Fallback Strategy

Every external dependency needs a degraded but usable path.

| Layer | Primary | Fallbacks |
|---|---|---|
| Search | Tavily | DuckDuckGo, Wikipedia, SearxNG, Brave |
| Reddit | Reddit API | Old Reddit JSON, web search |
| HN | Algolia | Firebase API, web search |
| GitHub | REST API | unauth search, web search |
| LLM classify/spec | Claude | OpenRouter, Groq, local Ollama-compatible path |
| Fetching | urllib/basic HTTP | Firecrawl if needed, or mark unverifiable |
| Deploy | Vercel | Railway, local/manual preview |

### Principle

Keyless modes are first-class. The system must not require paid API access to validate its own basic architecture.

---

## 10. Reuse Map

### From Codex

| Component | Reuse level | Notes |
|---|---|---|
| Auditor/verifier concepts | Medium | Reuse likely, but verify actual behavior before depending on it |
| Provider abstraction | High | Good candidate for reuse with new providers |
| Env/config loader | High | Straight reuse |
| Key status reporting | High | Straight reuse with new key names |
| Scoring engine | Medium | Adapt semantics to demand signals |
| Data models | Medium | Keep the pattern, change the schema |
| Test patterns | High | Reuse test style and fixture discipline |

### From Kimi

| Component | Reuse level | Notes |
|---|---|---|
| Hunter/scanner shape | Medium | Good orchestration pattern |
| Supervisor/coordinator pattern | Medium | Useful for source-parallel scanning |
| Phase-oriented pipeline thinking | Medium | Reuse at the architecture level, not as proof of build/ship features |

### Build fresh

- Product spec writer
- Builder
- Deployer
- Tracker
- Final CLI flow for the new product direction

---

## 11. Common Pitfalls

| Pitfall | Mitigation |
|---|---|
| Overstating what tests prove | Always label proof as fixture, dry-run, or live |
| Assuming repo docs equal code maturity | Verify reusable components in code and tests before relying on them |
| Confusing discovery signals with commitment signals | Pain/requests rank ideas; hard gates still control `PURSUE` |
| Hallucinated market data | URL + quote + verification required |
| API-cost sprawl | Budget caps and fallback chains |
| Human removed from the loop | Human approval before build, deploy, and outreach |
| Happy-market wedge trap | Use `competition_gap` as a ranking heuristic and review prompt |

---

## 12. Restrictions

### Non-negotiable rules

1. Never fabricate a `DemandSignal`.
2. Never skip verification for any signal that claims to be verified.
3. Never classify from summaries when the quote text is unavailable.
4. Never deploy without explicit human approval.
5. Never use nondeterministic production logic where deterministic logic is possible.
6. Never commit secrets.
7. Never run live API acceptance tests in CI.
8. Every new behavior needs a corresponding test.
9. Every LLM call in the pipeline must return structured output.
10. Keep agents thin and phase-bounded.

### Scoring rules

```text
1. Gate before score.
2. Hard gates:
   - willingness_to_pay
   - distribution_channel
   - data_feasibility
3. Ranking heuristics:
   - competition_gap
   - buildability
   - reachability_strength
4. Deduplicate by source cluster.
5. Apply freshness decay.
6. Score only survivors.
```

---

## 13. Implementation Phases

### Phase 0 - Foundation

- Create project structure
- Port reusable env/providers/test helpers
- Define `DemandSignal`, `Opportunity`, `ProductSpec`
- Rebuild deterministic scoring around inherited hard gates
- Write unit and integration tests first

### Phase 1 - Scanner + verifier

- Implement HN first
- Add quote verification against fixtures/pages
- Prove deterministic scan -> verify -> score

### Phase 2 - Multi-source ranking

- Add Reddit and GitHub
- Add source-parallel scanning
- Add ranking heuristics without changing hard-gate semantics

### Phase 3 - Spec writer

- Generate structured product specs from verified opportunities
- Add human review gate before build

### Phase 4 - Builder

- Generate a wedge app from a reviewed spec
- Prove the result can lint/build locally

### Phase 5 - Ship + track

- Deploy to Vercel or Railway
- Collect basic metrics

### Phase 6 - Live proof

- Run the pipeline on real domains
- Ship at least one real product
- Track real traffic and document results

---

## 14. Definition of Done

### Core evidence MVP

Done when:

1. `scan` produces ranked opportunities from multiple sources
2. Every surviving signal is traceable to source material
3. Hard gates are enforced deterministically
4. Acceptance tests pass in fixture mode
5. Dry-run mode works without paid APIs

### Product-spec MVP

Done when:

1. `spec` generates a valid structured product spec from a chosen opportunity
2. The spec only cites verified source material
3. Human review is required before build

### Full internal pipeline

Done when:

1. `build` produces a locally runnable wedge app
2. `ship` can deploy that app
3. `track` returns real metrics
4. At least one real product has been shipped with the workflow

### Productization gate

Do not sell the tool until:

1. It has been used to ship multiple products
2. At least one shipped product has real customer traction
3. The CLI workflow is stable enough to wrap in a UI

---

## Appendix A - Keyless Baseline

Minimum viable setup should work with:

- HN Algolia
- DuckDuckGo or Wikipedia
- GitHub unauth search
- Fixtures for deterministic tests
- Optional local Ollama-compatible path for low-cost experimentation

Paid providers improve the system. They must not be prerequisites for proving the architecture.

---

## Appendix B - Target File Structure

```text
evidentia/
  pyproject.toml
  .env.example
  final_pivot.md
  evidentia/
    cli.py
    models.py
    scoring.py
    auditor.py
    providers.py
    scanners/
    classifier.py
    spec_writer.py
    builder.py
    deployer.py
    tracker.py
  tests/
    unit/
    integration/
    acceptance/
    fixtures/
  outputs/
```
