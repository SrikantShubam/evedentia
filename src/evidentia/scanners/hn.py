import html
import json
from urllib.parse import urlencode

from evidentia.providers import _http_json


def scan_hn_fixture(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    return [
        {
            "source": "hn",
            "title": item["title"],
            "source_url": item["url"],
            "published_at": item.get("created_at"),
            "verbatim_quote": item.get("quote", item["title"]),
            "source_text": item.get("source_text", item.get("quote", item["title"])),
            "willingness_to_pay": item.get("willingness_to_pay", "unknown"),
            "distribution_channel": item.get("distribution_channel", "unknown"),
            "data_feasibility": item.get("data_feasibility", "unknown"),
            "competition_gap": item.get("competition_gap", 0),
            "buildability": item.get("buildability", 0),
            "reachability_strength": item.get("reachability_strength", 0),
            "cluster_id": item.get("cluster_id", item["url"]),
        }
        for item in payload["items"]
    ]


def scan_hn_live(query: str, max_results: int = 3, fetch_json=None) -> list[dict]:
    resolved_fetch = fetch_json or _http_json
    query_string = urlencode({"query": query, "tags": "story", "hitsPerPage": max_results})
    url = f"https://hn.algolia.com/api/v1/search_by_date?{query_string}"
    payload = resolved_fetch(url)
    hits = payload.get("hits") or []
    normalized: list[dict] = []
    for item in hits[:max_results]:
        object_id = item.get("objectID")
        if not object_id:
            continue
        # Algolia returns HTML-escaped text; decode so verbatim quotes match the real page.
        source_text = html.unescape(str(item.get("story_text") or item.get("title") or ""))
        normalized.append(
            {
                "source": "hn",
                "title": html.unescape(str(item.get("title") or "Untitled HN story")),
                "source_url": f"https://news.ycombinator.com/item?id={object_id}",
                "published_at": item.get("created_at"),
                "verbatim_quote": source_text,
                "source_text": source_text,
                "cluster_id": f"hn:{object_id}",
            }
        )
    return normalized
