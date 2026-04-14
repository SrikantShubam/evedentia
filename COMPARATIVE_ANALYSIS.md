# Comparative Analysis

## Scope

This comparison is based on the markdown corpus in `codex/`, `kimi/`, and `main/final_pivot.md`.
It separates three things:

1. documented capability
2. claimed implementation status
3. proven live capability

That distinction matters because several `kimi` documents use completion language that is not backed by the same level of evidence as the `codex` foundation docs or the corrected framing in `final_pivot.md`.

## Bottom Line

The `codex` corpus documents a narrower but better-grounded evidence engine:
- hardened evidence schema
- audit and discard workflow
- deduplication and freshness decay
- hard gates and survivor-only scoring
- dry-run and benchmark-oriented CLI support

The `kimi` corpus describes a larger end-to-end product pipeline:
- hunters
- auditors
- prosecutor
- reality spike generation
- live integration and production-ready positioning

But most of that broader framing is documented as implementation progress or completion claims inside markdown, not as independently demonstrated live capability.

`final_pivot.md` corrects the framing by treating the current repo as a pre-implementation evidence engine plus a future product pipeline:
- evidence collection, verification, scoring, and skeptical review are inherited foundations
- spec generation, build, ship, and tracking are new product-direction layers
- only the foundation should be treated as established from the corpus

## What `codex/` Actually Supports

The `codex` documents consistently support a deterministic MVP around evidence handling.

Supported by the corpus:
- an `EvidenceObject` schema
- authority tiers and claim types
- auditor-lite normalization and schema validation
- cluster deduplication
- hard killer detection
- coverage matrix gating
- gate-first verdicting: `KILL`, `REJECT`, `SURVIVE`
- survivor-only scoring with freshness decay
- prosecutor-style gap reporting
- hunter prompt packs
- dry-run mode and key readiness reporting

What this corpus does not prove:
- live search coverage across multiple providers
- production-grade quote verification against live pages
- real product shipping
- deploy-and-track workflows

In short, `codex/` is the strongest evidence for the deterministic validation core, not for the full product pipeline.

## What `kimi/` Adds

The `kimi` corpus expands the pipeline substantially.

It documents:
- five hunter roles
- auditor verification
- prosecutor review
- reality spike generation
- API and CLI entry points
- live search integration
- fallback provider support
- example tests and simulations
- multiple completion summaries

This is useful as architectural intent and as evidence that the project was being extended beyond the base engine.

However, the corpus also contains repeated claims such as:
- "production ready"
- "complete"
- "live integration"
- "all roadmap items completed"

Those statements should be treated as documented claims inside the corpus, not as proof of live operational maturity.

The strongest evidence in `kimi/` is still mixed:
- some docs include concrete commands, test outputs, and run logs
- other docs are retrospective summaries that assert broad completion

So `kimi/` supports the existence of a larger system design, but not all of its claimed maturity.

## Corrected Framing from `final_pivot.md`

`final_pivot.md` is the correcting document.

Its main contribution is not new mechanics; it is a stricter interpretation of the repository's state:
- the repo has evidence-engine foundations
- the broader product pipeline is a pivot, not settled fact
- build, ship, and track are staged layers, not equally proven capabilities
- documented completion language must not be confused with live proof

The pivot also sharpens the product direction:
- scan existing demand signals
- score opportunities
- write a spec
- optionally build
- optionally ship
- optionally track traction

This is more defensible than claiming the system already has full production productization.

## Evidence vs Claim

| Area | `codex/` | `kimi/` | `final_pivot.md` |
|---|---|---|---|
| Evidence schema and gates | Documented clearly | Documented clearly | Reused as foundation |
| Deterministic scoring | Documented clearly | Documented clearly | Reaffirmed |
| Hunter/auditor/prosecutor/reality spike pipeline | Mostly prompt/plan level | Documented as implemented | Treated as future pipeline layers |
| Live capability | Dry-run and benchmark claims only | Mixed, mostly asserted in docs | Explicitly not assumed |
| Productization | Not claimed | Often claimed | Deferred until after real use |

## Corrected Conclusion

The evidence-supported conclusion is:

`codex/` establishes a solid deterministic validation core.
`kimi/` documents an expanded pipeline, but much of its maturity is asserted rather than proven.
`final_pivot.md` is the authoritative correction: Evidentia should be framed as an internal demand-to-product pipeline with staged, not yet equally proven, layers.

So the right way to describe the repository is not "fully production-ready validation platform."
It is:

> a validated evidence engine with documented extensions toward spec generation, build, ship, and tracking, where only the evidence core is clearly supported by the corpus.

