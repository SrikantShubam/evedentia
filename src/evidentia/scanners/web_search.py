from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from evidentia.providers import choose_search_provider, ProviderError


def scan_web_search_live(query: str, max_results: int = 5) -> list[dict]:
    if not query or not query.strip():
        return []
    provider = choose_search_provider()
    try:
        hits = provider.search(query, max_results=max_results)
    except ProviderError:
        return []
    candidates = []
    for hit in hits:
        if not hit.url:
            continue
        url_hash = hashlib.sha256(hit.url.encode()).hexdigest()[:12]
        snippet = hit.snippet or hit.title or query
        candidates.append({
            "source": "web_search",
            "title": hit.title or query,
            "source_url": hit.url,
            "published_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "verbatim_quote": snippet,
            "source_text": snippet,
            "cluster_id": f"web:{url_hash}",
        })
    return candidates
