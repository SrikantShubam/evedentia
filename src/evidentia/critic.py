from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any

from evidentia.models import Anchor, DemandSignal, Slice, SliceVerdict, Verdict
from evidentia.providers import choose_llm_provider, choose_search_provider, load_external_provider_env


NEXT_TEST_TEMPLATES = {
    "weak_voices": "Post a specific question in {channel} asking users to share experiences with {pain}. PURSUE if >= 10 reply-level engagements in 7 days.",
    "borderline_served": "Named competitor(s): {competitors}. Validate differentiation by asking 5 users of {first_competitor} whether {slice_label} would make them switch.",
    "weak_reach": "Identify a primary channel: find a subreddit, newsletter, or conference tag with >= 1k members focused on {cohort}. PURSUE if found.",
    "weak_buildable": "Reduce scope to one atomic wedge. Re-run critic with narrowed label '{slice_label} for {cohort} - only {top_feature}'.",
    "landing_page_test": "Run landing-page test on {channel} with copy anchored on '{slice_label}'. PURSUE if >= 50 signups in 7 days.",
}

_INTEGRATION_KEYWORDS = (
    "stripe",
    "quickbooks",
    "salesforce",
    "twilio",
    "oauth",
    "sso",
    "slack",
    "hubspot",
    "zapier",
    "xero",
)

_INTEGRATION_PATTERNS = tuple(re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE) for keyword in _INTEGRATION_KEYWORDS)
_SUBREDDIT_PATTERN = re.compile(r"(?:^|[\s/])r/([a-z0-9_]+)", re.IGNORECASE)
_DOMAIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?([a-z0-9.-]+\.[a-z]{2,})", re.IGNORECASE)


def _gate_market_exists(anchor: Anchor) -> bool:
    return bool(anchor.proof_of_market.verified)


def _gate_slice_has_voices(slice_obj: Slice) -> bool:
    return slice_obj.author_count >= 3


def _validate_underserved_response(payload: Any) -> list[str]:
    violations: list[str] = []
    if not isinstance(payload, dict):
        return ["response must be an object"]
    if payload.get("underserved") not in {"yes", "no", "unclear"}:
        violations.append("underserved must be yes|no|unclear")
    competitors = payload.get("named_competitors")
    if not isinstance(competitors, list) or any(not isinstance(item, str) for item in competitors):
        violations.append("named_competitors must be a list[str]")
    return violations


def _underserved_prompt(slice_obj: Slice, result_titles: list[str]) -> str:
    rendered_titles = "\n".join(f"- {title}" for title in result_titles[:5]) or "- (no results)"
    return (
        "Classify whether this niche slice is underserved.\n"
        "Return JSON only with this exact shape:\n"
        '{"underserved": "yes|no|unclear", "named_competitors": ["..."]}\n\n'
        f"Slice label: {slice_obj.label}\n"
        "Top search result titles:\n"
        f"{rendered_titles}\n"
    )


def _safe_competitors(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    normalized: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _gate_slice_underserved(
    slice_obj: Slice,
    anchor: Anchor,
    env: dict[str, str],
    *,
    search_provider=None,
    llm_provider=None,
    llm_model: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    del anchor
    if str(env.get("EVIDENTIA_DRY_RUN", "")).strip().lower() in {"1", "true", "yes"}:
        return True, {"underserved": "yes", "named_competitors": [], "titles": []}

    query = f'"{slice_obj.label}" app OR saas'
    titles: list[str] = []
    try:
        resolved_search_provider = search_provider or choose_search_provider(env)
        hits = resolved_search_provider.search(query=query, max_results=5)
        titles = [str(hit.title).strip() for hit in hits if str(getattr(hit, "title", "")).strip()][:5]
    except Exception as exc:  # noqa: BLE001
        return False, {"underserved": "unclear", "named_competitors": [], "error": str(exc), "titles": titles}

    resolved_llm_provider = llm_provider
    resolved_llm_model = llm_model
    if resolved_llm_provider is None or resolved_llm_model is None:
        try:
            resolved_llm_provider, resolved_llm_model = choose_llm_provider(env)
        except Exception as exc:  # noqa: BLE001
            return False, {"underserved": "unclear", "named_competitors": [], "error": str(exc), "titles": titles}

    prompt = _underserved_prompt(slice_obj, titles)
    response: dict[str, Any] | Any
    try:
        response = resolved_llm_provider.generate_json(prompt=prompt, model=resolved_llm_model)
    except Exception as exc:  # noqa: BLE001
        return False, {"underserved": "unclear", "named_competitors": [], "error": str(exc), "titles": titles}

    violations = _validate_underserved_response(response)
    if violations:
        corrective_prompt = (
            f"{prompt}\nYour previous response was invalid: {', '.join(violations)}. "
            "Return ONLY the required JSON object."
        )
        try:
            response = resolved_llm_provider.generate_json(prompt=corrective_prompt, model=resolved_llm_model)
        except Exception as exc:  # noqa: BLE001
            return False, {"underserved": "unclear", "named_competitors": [], "error": str(exc), "titles": titles}
        violations = _validate_underserved_response(response)
    if violations:
        return False, {"underserved": "unclear", "named_competitors": [], "error": "; ".join(violations), "titles": titles}

    state = str(response["underserved"])
    competitors = _safe_competitors(response.get("named_competitors"))
    return state == "yes", {"underserved": state, "named_competitors": competitors, "titles": titles}


def _primary_channel_markers(anchor: Anchor) -> tuple[set[str], set[str]]:
    domains: set[str] = set()
    subreddits: set[str] = set()
    for query in anchor.primary_channel_queries:
        lowered = query.lower()
        domains.update(domain for domain in _DOMAIN_PATTERN.findall(lowered) if "." in domain)
        subreddits.update(_SUBREDDIT_PATTERN.findall(lowered))
    return domains, subreddits


def _cohort_subreddits(anchor: Anchor) -> set[str]:
    slugs: set[str] = set()
    for hint in anchor.cohort_hints:
        normalized = re.sub(r"[^a-z0-9]+", "", hint.lower())
        if normalized:
            slugs.add(normalized)
    return slugs


def _gate_reachable(slice_obj: Slice, anchor: Anchor, signals: list[DemandSignal]) -> bool:
    del slice_obj
    domains, query_subreddits = _primary_channel_markers(anchor)
    cohort_subreddits = _cohort_subreddits(anchor)
    for signal in signals:
        url = signal.source_url.lower()
        if any(domain in url for domain in domains):
            return True
        if any(f"/r/{subreddit}" in url for subreddit in query_subreddits):
            return True
        if any(f"/r/{subreddit}" in url for subreddit in cohort_subreddits):
            return True
    return False


def _integration_mentions(signals: list[DemandSignal]) -> set[str]:
    mentions: set[str] = set()
    for signal in signals:
        corpus = f"{signal.verbatim_quote} {signal.source_text or ''}"
        for keyword, pattern in zip(_INTEGRATION_KEYWORDS, _INTEGRATION_PATTERNS, strict=True):
            if pattern.search(corpus):
                mentions.add(keyword)
    return mentions


def _gate_buildable(slice_obj: Slice, signals: list[DemandSignal]) -> bool:
    del slice_obj
    return len(_integration_mentions(signals)) < 4


def _next_test_context(slice_obj: Slice, anchor: Anchor, competitors: list[str] | None = None) -> dict[str, str]:
    first_query = anchor.primary_channel_queries[0] if anchor.primary_channel_queries else f"reddit.com/r/{anchor.slug.replace('-', '')}"
    cohort = anchor.cohort_hints[0] if anchor.cohort_hints else "core users"
    pain = slice_obj.label.lower()
    return {
        "channel": first_query,
        "pain": pain,
        "competitors": ", ".join(competitors or []) or "unknown",
        "first_competitor": (competitors or ["named incumbent"])[0],
        "slice_label": slice_obj.label,
        "cohort": cohort,
        "top_feature": "one core workflow improvement",
    }


def _build_refine_next_test(
    slice_obj: Slice,
    anchor: Anchor,
    gates: dict[str, bool],
    *,
    competitors: list[str] | None = None,
) -> str:
    context = _next_test_context(slice_obj, anchor, competitors=competitors)
    if not gates["slice_has_voices"]:
        return NEXT_TEST_TEMPLATES["weak_voices"].format(**context)
    if not gates["reachable"]:
        return NEXT_TEST_TEMPLATES["weak_reach"].format(**context)
    if not gates["buildable"]:
        return NEXT_TEST_TEMPLATES["weak_buildable"].format(**context)
    if competitors:
        return NEXT_TEST_TEMPLATES["borderline_served"].format(**context)
    return NEXT_TEST_TEMPLATES["landing_page_test"].format(**context)


def _refine_reason(gates: dict[str, bool], underserved_state: str, competitors: list[str], slice_obj: Slice) -> str:
    failed = [name for name, passed in gates.items() if not passed]
    if failed:
        if "slice_underserved" in failed and underserved_state == "unclear":
            if competitors:
                return f"slice_underserved:unclear competitors={', '.join(competitors)}"
            return "slice_underserved:unclear"
        return f"gate_failures:{','.join(failed)}"
    if slice_obj.author_count < 5:
        return "insufficient_voice_density_for_pursue"
    return "requires_additional_validation"


def critique_slice(
    slice: Slice,
    signals_by_id: dict[str, DemandSignal],
    anchor: Anchor,
    env: dict[str, str] | None = None,
) -> SliceVerdict:
    runtime_env = env or load_external_provider_env()
    signals = [signals_by_id[signal_id] for signal_id in slice.signal_ids if signal_id in signals_by_id]

    market_exists = _gate_market_exists(anchor)
    slice_has_voices = _gate_slice_has_voices(slice)
    slice_underserved, underserved_detail = _gate_slice_underserved(slice, anchor, runtime_env)
    reachable = _gate_reachable(slice, anchor, signals)
    buildable = _gate_buildable(slice, signals)

    gates = {
        "market_exists": market_exists,
        "slice_has_voices": slice_has_voices,
        "slice_underserved": slice_underserved,
        "reachable": reachable,
        "buildable": buildable,
    }
    heuristics = {
        "competition_gap": 1.0 if slice_underserved else 0.0,
        "buildability": 1.0 if buildable else 0.0,
        "reachability_strength": 1.0 if reachable else 0.0,
    }

    competitors = _safe_competitors(underserved_detail.get("named_competitors"))
    underserved_state = str(underserved_detail.get("underserved", "unclear"))

    if not gates["market_exists"] or not gates["slice_underserved"]:
        verdict = Verdict.KILL.value
        next_test = None
    elif all(gates.values()) and slice.author_count >= 5:
        verdict = Verdict.PURSUE.value
        next_test = "Ship a manual wedge. Document traction in outputs/pursued/<slice_id>/traction.md."
    else:
        verdict = Verdict.REFINE.value
        next_test = _build_refine_next_test(slice, anchor, gates, competitors=competitors)

    refine_reason = _refine_reason(gates, underserved_state, competitors, slice)
    if verdict == Verdict.PURSUE.value:
        refine_reason = None
    if verdict == Verdict.KILL.value and not refine_reason:
        refine_reason = "critical_gate_failed"

    if verdict == Verdict.REFINE.value:
        assert next_test is not None

    return SliceVerdict(
        slice_id=slice.slice_id,
        anchor_slug=slice.anchor_slug,
        verdict=verdict,
        gates=gates,
        heuristics=heuristics,
        refine_reason=refine_reason,
        next_test=next_test,
        evidence_ids=[signal.signal_id for signal in signals],
        schema_version=1,
    )


def to_dict(verdict: SliceVerdict) -> dict[str, Any]:
    return asdict(verdict)
