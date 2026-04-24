from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import sleep
import re
from urllib.parse import quote_plus
import warnings

from evidentia import auditor
from evidentia.models import Anchor, DemandSignal
from evidentia.providers import _http_json, choose_search_provider, load_external_provider_env
from evidentia.scanners.reddit import scan_reddit_live


_MISSING_FEATURE_PATTERN = re.compile(r"\b(missing|wish it had|should add|needs)\b", re.IGNORECASE)
_USABILITY_PATTERN = re.compile(r"\b(confusing|hard to use|clunky|ui)\b", re.IGNORECASE)
_COHORT_PATTERN = re.compile(r"\b(for men only|not for women|excluded|no option for)\b", re.IGNORECASE)
_PRICING_PATTERN = re.compile(r"\b(too expensive|overpriced|free tier|paywall)\b", re.IGNORECASE)
_SWITCHING_PATTERN = re.compile(r"\b(switching to|looking for alternative|replaced .+ with)\b", re.IGNORECASE)


def _slugify(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "unknown"


def _normalize_timestamp(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _classify_subtype(text: str) -> str:
    lowered = text.lower()
    if _MISSING_FEATURE_PATTERN.search(lowered):
        return "missing_feature"
    if _USABILITY_PATTERN.search(lowered):
        return "usability_complaint"
    if _COHORT_PATTERN.search(lowered):
        return "cohort_exclusion"
    if _PRICING_PATTERN.search(lowered):
        return "pricing_complaint"
    if _SWITCHING_PATTERN.search(lowered):
        return "switching_intent"
    return "unknown"


def _classify_complaint_type(subtype: str, text: str) -> tuple[str, str | None]:
    mapping = {
        "pricing_complaint": "PRICING",
        "usability_complaint": "UX",
        "missing_feature": "MISSING_FEATURE",
        "cohort_exclusion": "NICHE_EXCLUSION",
        "switching_intent": "SCOPE_MISMATCH",
    }
    complaint_type = mapping.get(subtype)
    if complaint_type:
        return complaint_type, None
    return "UNKNOWN_WITH_REASON", f"no confident mapping for subtype='{subtype}' from text pattern matching"


def _lookup_app_id(incumbent: str) -> int | None:
    encoded_incumbent = quote_plus(incumbent)
    payload = _http_json(
        f"https://itunes.apple.com/search?term={encoded_incumbent}&entity=software&limit=1",
        method="GET",
    )
    results = payload.get("results") or []
    if not results:
        return None
    app_id = results[0].get("trackId")
    if app_id is None:
        return None
    return int(app_id)


def _ios_reviews_for_app(incumbent: str, app_id: int) -> list[dict]:
    payload = _http_json(
        f"https://itunes.apple.com/us/rss/customerreviews/page=1/id={app_id}/sortBy=mostRecent/json",
        method="GET",
    )
    entries = ((payload.get("feed") or {}).get("entry")) or []
    reviews: list[dict] = []
    for entry in entries:
        rating_value = str((entry.get("im:rating") or {}).get("label", ""))
        try:
            rating = int(rating_value)
        except ValueError:
            rating = 0
        if rating >= 4:
            continue
        title = str((entry.get("title") or {}).get("label", "")).strip()
        content = str((entry.get("content") or {}).get("label", "")).strip()
        quote = content or title
        if not quote:
            continue
        raw_source_url = str((entry.get("id") or {}).get("label", "")).strip()
        source_url = raw_source_url if raw_source_url.startswith("http") else f"https://apps.apple.com/us/app/id{app_id}"
        reviews.append(
            {
                "source_url": source_url,
                "title": title or f"{incumbent} review",
                "quote": quote,
                "source_text": content or quote,
                "timestamp": str((entry.get("updated") or {}).get("label", "")),
                "author": str(((entry.get("author") or {}).get("name") or {}).get("label", "")) or None,
                "source_kind": "ios_review",
            }
        )
    return reviews


def _reddit_candidates_for_incumbent(incumbent: str, limit: int) -> list[dict]:
    candidates: list[dict] = []
    subreddit_slug = _slugify(incumbent).replace("-", "")

    try:
        direct_payload = _http_json(
            f"https://www.reddit.com/r/{subreddit_slug}/new.json?limit={limit}",
            headers={"Accept": "application/json", "User-Agent": "Evidentia/1.0"},
            method="GET",
        )
        children = ((direct_payload.get("data") or {}).get("children")) or []
        for child in children:
            data = child.get("data") or {}
            permalink = data.get("permalink")
            if not permalink:
                continue
            text = str(data.get("selftext") or data.get("title") or "").strip()
            if not text:
                continue
            timestamp = None
            created_utc = data.get("created_utc")
            if created_utc is not None:
                timestamp = datetime.fromtimestamp(float(created_utc), timezone.utc).isoformat().replace("+00:00", "Z")
            candidates.append(
                {
                    "source_url": f"https://www.reddit.com{permalink}",
                    "title": str(data.get("title") or incumbent),
                    "quote": text,
                    "source_text": text,
                    "timestamp": timestamp,
                    "author": str(data.get("author") or "") or None,
                    "source_kind": "reddit",
                }
            )
    except Exception as exc:  # noqa: BLE001
        warnings.warn(f"reddit subreddit fetch failed for {incumbent}: {exc}", RuntimeWarning)

    try:
        query = f'"{incumbent}" missing OR broken OR hate OR switch'
        for item in scan_reddit_live(query, max_results=limit):
            candidates.append(
                {
                    "source_url": item["source_url"],
                    "title": item["title"],
                    "quote": item["verbatim_quote"],
                    "source_text": item["source_text"],
                    "timestamp": item.get("published_at"),
                    "author": None,
                    "source_kind": "reddit",
                }
            )
    except Exception as exc:  # noqa: BLE001
        warnings.warn(f"reddit search failed for {incumbent}: {exc}", RuntimeWarning)

    return candidates


def _search_candidates(anchor: Anchor, env: dict[str, str], limit: int) -> list[dict]:
    provider = choose_search_provider(env)
    candidates: list[dict] = []
    for query in anchor.primary_channel_queries:
        try:
            for hit in provider.search(query=query, max_results=min(limit, 5)):
                snippet = str(hit.snippet).strip()
                if not snippet:
                    continue
                candidates.append(
                    {
                        "source_url": str(hit.url),
                        "title": str(hit.title or query),
                        "quote": snippet,
                        "source_text": snippet,
                        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "author": None,
                        "source_kind": "search",
                    }
                )
        except Exception as exc:  # noqa: BLE001
            warnings.warn(f"primary channel query failed '{query}': {exc}", RuntimeWarning)
    return candidates


def _to_signal(candidate: dict) -> DemandSignal | None:
    source_url = str(candidate.get("source_url", "")).strip()
    quote = str(candidate.get("quote", "")).strip()
    source_text = str(candidate.get("source_text", "")).strip()
    if not source_url or not quote:
        return None

    verification = auditor.verify_quote(
        {
            "source_url": source_url,
            "verbatim_quote": quote,
            "source_text": source_text,
        }
    )
    if verification.get("proof_level") == "none":
        return None

    timestamp = _normalize_timestamp(candidate.get("timestamp"))
    title = str(candidate.get("title", "")).strip() or None
    subtype = _classify_subtype(f"{title or ''} {source_text}")
    complaint_type, complaint_type_reason = _classify_complaint_type(subtype, f"{title or ''} {source_text}")
    return DemandSignal(
        signal_id=DemandSignal.build_signal_id(source_url, quote),
        source_url=source_url,
        verbatim_quote=quote,
        timestamp=timestamp,
        title=title,
        source_text=source_text or None,
        source_kind=str(candidate.get("source_kind", "unknown")),
        signal_subtype=subtype,
        author=candidate.get("author"),
        verified=bool(verification.get("verified")),
        proof_level=str(verification.get("proof_level", "none")),
        complaint_type=complaint_type,
        complaint_type_reason=complaint_type_reason,
    )


def _sorted_signals(signals: list[DemandSignal]) -> list[DemandSignal]:
    return sorted(
        signals,
        key=lambda item: (item.verified, item.timestamp),
        reverse=True,
    )


def listen(anchor: Anchor, limit: int = 50, env: dict[str, str] | None = None) -> list[DemandSignal]:
    runtime_env = env or load_external_provider_env()
    raw_candidates: list[dict] = []

    for incumbent in anchor.incumbents:
        try:
            app_id = _lookup_app_id(incumbent)
            if app_id is not None:
                raw_candidates.extend(_ios_reviews_for_app(incumbent, app_id))
        except Exception as exc:  # noqa: BLE001
            warnings.warn(f"ios reviews failed for {incumbent}: {exc}", RuntimeWarning)
        finally:
            sleep(2)

        raw_candidates.extend(_reddit_candidates_for_incumbent(incumbent, limit=min(10, limit)))

    raw_candidates.extend(_search_candidates(anchor, runtime_env, limit=min(10, limit)))

    signals: list[DemandSignal] = []
    seen: set[str] = set()
    for candidate in raw_candidates:
        signal = _to_signal(candidate)
        if signal is None:
            continue
        if signal.signal_id in seen:
            continue
        seen.add(signal.signal_id)
        signals.append(signal)

    return _sorted_signals(signals)[:limit]


def listen_for_idea(anchor: Anchor, idea: dict, limit: int = 20, env: dict[str, str] | None = None) -> list[DemandSignal]:
    runtime_env = env or load_external_provider_env()
    provider = choose_search_provider(runtime_env)
    queries = [str(query) for query in idea.get("search_queries", []) if str(query).strip()]
    raw_candidates: list[dict] = []
    for query in queries:
        try:
            for hit in provider.search(query=query, max_results=min(limit, 5)):
                snippet = str(hit.snippet).strip()
                if not snippet:
                    continue
                raw_candidates.append(
                    {
                        "source_url": str(hit.url),
                        "title": str(hit.title or idea.get("label", query)),
                        "quote": snippet,
                        "source_text": snippet,
                        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "author": None,
                        "source_kind": "search",
                    }
                )
        except Exception as exc:  # noqa: BLE001
            warnings.warn(f"listen_for_idea query failed '{query}': {exc}", RuntimeWarning)

    signals: list[DemandSignal] = []
    seen: set[str] = set()
    for candidate in raw_candidates:
        signal = _to_signal(candidate)
        if signal is None or signal.signal_id in seen:
            continue
        seen.add(signal.signal_id)
        signals.append(signal)
    return _sorted_signals(signals)[:limit]
