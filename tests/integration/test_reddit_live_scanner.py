from evidentia.scanners.reddit import scan_reddit_live


def test_reddit_live_scanner_normalizes_json_hits():
    def fake_fetch_json(url: str, headers=None) -> dict:
        return {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Paying for invoice reminder tooling",
                            "selftext": "We would pay for better AR reminders.",
                            "permalink": "/r/startups/comments/abc123/paying_for_invoice_reminder_tooling/",
                            "created_utc": 1713052800,
                        }
                    }
                ]
            }
        }

    results = scan_reddit_live("invoice reminder", max_results=1, fetch_json=fake_fetch_json)

    assert len(results) == 1
    assert results[0]["source"] == "reddit"
    assert results[0]["source_url"].startswith("https://www.reddit.com/")
    assert "would pay" in results[0]["source_text"].lower()


def test_reddit_live_scanner_url_encodes_reserved_characters():
    seen = {}

    def fake_fetch_json(url: str, headers=None) -> dict:
        seen["url"] = url
        return {"data": {"children": []}}

    scan_reddit_live("accounts & billing?", max_results=1, fetch_json=fake_fetch_json)

    assert "accounts+%26+billing%3F" in seen["url"]


def test_reddit_live_scanner_skips_hits_without_permalink():
    def fake_fetch_json(url: str, headers=None) -> dict:
        return {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Paying for invoice reminder tooling",
                            "selftext": "We would pay for better AR reminders.",
                            "created_utc": 1713052800,
                        }
                    }
                ]
            }
        }

    assert scan_reddit_live("invoice reminder", max_results=1, fetch_json=fake_fetch_json) == []
