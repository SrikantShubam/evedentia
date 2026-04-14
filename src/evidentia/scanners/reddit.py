import json
from datetime import datetime, timezone

from evidentia.providers import _http_json


def scan_reddit_fixture(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    return [
        {
            "source": "reddit",
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


def scan_reddit_live(query: str, max_results: int = 3, fetch_json=None) -> list[dict]:
    resolved_fetch = fetch_json or _http_json
    encoded_query = query.replace(" ", "+")
    url = f"https://www.reddit.com/search.json?q={encoded_query}&limit={max_results}&sort=new"
    payload = resolved_fetch(url, headers={"Accept": "application/json", "User-Agent": "Evidentia/1.0"})
    children = ((payload.get("data") or {}).get("children")) or []
    normalized: list[dict] = []
    for child in children[:max_results]:
        item = child.get("data") or {}
        source_text = str(item.get("selftext") or item.get("title") or "")
        created_utc = item.get("created_utc")
        published_at = None
        if created_utc is not None:
            published_at = datetime.fromtimestamp(float(created_utc), timezone.utc).isoformat().replace("+00:00", "Z")
        normalized.append(
            {
                "source": "reddit",
                "title": str(item.get("title") or "Untitled Reddit post"),
                "source_url": f"https://www.reddit.com{item.get('permalink', '')}",
                "published_at": published_at,
                "verbatim_quote": source_text,
                "source_text": source_text,
                "cluster_id": f"reddit:{item.get('permalink', item.get('id', 'unknown'))}",
            }
        )
    return normalized
