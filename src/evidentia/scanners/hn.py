import json

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
    url = (
        "https://hn.algolia.com/api/v1/search_by_date?"
        f"query={query.replace(' ', '+')}&tags=story&hitsPerPage={max_results}"
    )
    payload = resolved_fetch(url)
    hits = payload.get("hits") or []
    normalized: list[dict] = []
    for item in hits[:max_results]:
        source_text = str(item.get("story_text") or item.get("title") or "")
        normalized.append(
            {
                "source": "hn",
                "title": str(item.get("title") or "Untitled HN story"),
                "source_url": f"https://news.ycombinator.com/item?id={item['objectID']}",
                "published_at": item.get("created_at"),
                "verbatim_quote": source_text,
                "source_text": source_text,
                "cluster_id": f"hn:{item['objectID']}",
            }
        )
    return normalized
