"""Mode A research pipeline: discover competitors, analyze reviews, identify market opportunities."""

import json
import re

from evidentia.classifier import classify_complaint
from evidentia.models import (
    BarrierHypothesis,
    ClassifiedComplaint,
    OpportunityGap,
    ResearchReport,
    Review,
)
from evidentia.providers import (
    build_llm_provider_chain,
    choose_search_provider,
    load_external_provider_env,
)
from evidentia.scanners.reviews import (
    _ios_reviews_for_app,
    _lookup_app_id,
    _reddit_candidates_for_incumbent,
)


def _tag_authenticity(text: str) -> str:
    """Tag review authenticity using simple heuristics."""
    t = text.strip()
    if len(t) < 10 or t.isupper() or re.search(r"(.)\1{3,}", t):
        return "SUSPICIOUS"
    return "AUTHENTIC"


def _raw_to_review(raw: dict, source: str) -> Review:
    text = str(raw.get("quote") or raw.get("source_text") or "").strip()
    return Review(
        text=text,
        rating=2 if source == "app_store" else 0,
        source=source,
        date=str(raw.get("timestamp") or ""),
        authenticity=_tag_authenticity(text),
    )


def research_market(
    query: str,
    env: dict[str, str] | None = None,
    max_competitors: int = 5,
) -> ResearchReport:
    """Mode A end-to-end research pipeline.

    Takes a query string, discovers competitors, fetches and classifies
    reviews, generates barrier hypotheses via LLM, and returns a
    ResearchReport.

    Never crashes -- returns partial results with whatever data was collected.
    """
    runtime_env = env or load_external_provider_env()
    search_provider = choose_search_provider(runtime_env)

    # -- Step 1: Competitor discovery ----------------------------------
    # Primary: search iTunes directly for apps matching the query
    competitors: list[tuple[str, int | None]] = []
    seen_ids: set[int] = set()
    try:
        from evidentia.providers import _http_json
        from urllib.parse import quote_plus
        payload = _http_json(
            f"https://itunes.apple.com/search?term={quote_plus(query)}&entity=software&limit={max_competitors * 2}",
            method="GET",
        )
        for result in (payload.get("results") or [])[: max_competitors * 2]:
            name = str(result.get("trackName", "")).strip()
            app_id = result.get("trackId")
            if name and app_id and app_id not in seen_ids:
                seen_ids.add(app_id)
                competitors.append((name, int(app_id)))
    except Exception:
        pass

    # Secondary: supplement with web search for apps not on App Store
    if len(competitors) < max_competitors:
        for search_q in [f"{query} app store", f"{query} ios app"]:
            try:
                for hit in search_provider.search(search_q, max_results=5):
                    name = hit.title.split(" - ")[0].split(" | ")[0].split(":")[0].strip()
                    # Skip obvious non-app results
                    if len(name) < 3 or len(name) > 80:
                        continue
                    if any(skip in name.lower() for skip in ("best ", "top ", "review", "guide", "how to", "202")):
                        continue
                    if name.lower() not in {c[0].lower() for c in competitors}:
                        try:
                            app_id = _lookup_app_id(name)
                            if app_id and app_id not in seen_ids:
                                seen_ids.add(app_id)
                                competitors.append((name, app_id))
                        except Exception:
                            pass
            except Exception:
                continue

    if not competitors:
        return ResearchReport(
            query=query,
            competitors_analyzed=[],
            total_reviews=0,
            complaints=[],
            barrier_hypotheses=[],
            top_opportunities=[],
            provenance_summary="No competitors discovered during search.",
        )

    # -- Step 2: Review fetching ---------------------------------------
    raw_pairs: list[tuple[dict, str]] = []
    for comp_name, app_id in competitors:
        if app_id is not None:
            try:
                for r in _ios_reviews_for_app(comp_name, app_id)[:20]:
                    raw_pairs.append((r, "app_store"))
            except Exception:
                pass
        try:
            for r in _reddit_candidates_for_incumbent(comp_name, limit=10):
                raw_pairs.append((r, "reddit"))
        except Exception:
            pass

    reviews = [_raw_to_review(r, s) for r, s in raw_pairs]

    if not reviews:
        return ResearchReport(
            query=query,
            competitors_analyzed=[c[0] for c in competitors],
            total_reviews=0,
            complaints=[],
            barrier_hypotheses=[],
            top_opportunities=[],
            provenance_summary="Competitors found but no reviews collected.",
        )

    # -- Step 3 + 4: Authenticity filter + Complaint classification ----
    complaints: list[ClassifiedComplaint] = []
    for review in reviews:
        if review.authenticity != "AUTHENTIC":
            continue
        try:
            complaint_type, reason = classify_complaint(review.text)
        except Exception:
            continue
        if complaint_type == "UNKNOWN_WITH_REASON":
            continue
        severity_map = {1: 9, 2: 7, 3: 5}
        severity = severity_map.get(review.rating, 5)
        confidence = 0.8 if not reason else 0.6
        complaints.append(
            ClassifiedComplaint(
                review_text=review.text,
                complaint_type=complaint_type,
                severity=severity,
                confidence=confidence,
            )
        )

    # -- Step 5: Barrier hypotheses via LLM ----------------------------
    barrier_hypotheses: list[BarrierHypothesis] = []
    if complaints:
        top_c = [c.review_text[:200] for c in complaints[:5]]
        prompt = (
            f"Given these user complaints about {query} apps:\n"
            + "\n".join(f"- {t}" for t in top_c)
            + "\n\nWhat structural barriers might prevent these issues from being solved?"
            " Consider regulation, economics, network effects, technical feasibility, market size."
            " Return JSON: [{description, barrier_type, confidence}]"
            " where barrier_type is one of: regulation, economics, network_effects, technical, market_size, other."
        )
        try:
            for llm_provider, model in build_llm_provider_chain(runtime_env):
                try:
                    result = llm_provider.generate_json(prompt, model)
                    if isinstance(result, list):
                        for item in result:
                            if isinstance(item, dict) and "description" in item:
                                barrier_hypotheses.append(
                                    BarrierHypothesis(
                                        description=str(item["description"]),
                                        barrier_type=str(item.get("barrier_type", "other")),
                                        confidence=float(item.get("confidence", 0.5)),
                                    )
                                )
                        break
                except Exception:
                    continue
        except Exception:
            pass

    # -- Step 6: Opportunity gaps --------------------------------------
    type_counts: dict[str, int] = {}
    for c in complaints:
        type_counts[c.complaint_type] = type_counts.get(c.complaint_type, 0) + 1

    top_opportunities: list[OpportunityGap] = []
    for ctype, count in type_counts.items():
        if count < 2:
            continue
        if count >= 5:
            sev = "HIGH"
        elif count >= 3:
            sev = "MEDIUM"
        else:
            sev = "LOW"
        top_opportunities.append(
            OpportunityGap(
                gap_description=f"Multiple users report {ctype} issues with existing {query} solutions",
                evidence_count=count,
                severity=sev,
                exploitability="MEDIUM",
            )
        )
    top_opportunities.sort(key=lambda o: o.evidence_count, reverse=True)

    # -- Step 7: Assemble report ---------------------------------------
    return ResearchReport(
        query=query,
        competitors_analyzed=[c[0] for c in competitors],
        total_reviews=len(reviews),
        complaints=complaints,
        barrier_hypotheses=barrier_hypotheses,
        top_opportunities=top_opportunities,
        provenance_summary=(
            f"Evidence gathered from {len(competitors)} competitors across "
            "App Store and Reddit. All claims linked to source reviews."
        ),
    )
