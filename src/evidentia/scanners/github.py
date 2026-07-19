import json
from urllib.parse import urlencode

from evidentia.providers import _http_json

_MIN_BODY_CHARS = 40


def scan_github_fixture(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    return [
        {
            "source": "github",
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


def scan_github_live(query: str, max_results: int = 3, fetch_json=None) -> list[dict]:
    resolved_fetch = fetch_json or _http_json
    query_string = urlencode({"q": f"{query} label:enhancement", "per_page": max_results})
    url = f"https://api.github.com/search/issues?{query_string}"
    payload = resolved_fetch(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "Evidentia/1.0"})
    items = payload.get("items") or []
    normalized: list[dict] = []
    for item in items:
        if len(normalized) >= max_results:
            break
        html_url = item.get("html_url")
        if not html_url:
            continue
        title = str(item.get("title") or "")
        body = str(item.get("body") or "").strip()
        # Title-echo or near-empty bodies carry no usable demand evidence.
        if len(body) < _MIN_BODY_CHARS or body == title.strip():
            continue
        source_text = body
        normalized.append(
            {
                "source": "github",
                "title": str(item.get("title") or "Untitled GitHub issue"),
                "source_url": str(html_url),
                "published_at": item.get("updated_at"),
                "verbatim_quote": source_text,
                "source_text": source_text,
                "cluster_id": f"github:{item.get('id', 'unknown')}",
            }
        )
    return normalized
