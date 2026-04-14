import json


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
