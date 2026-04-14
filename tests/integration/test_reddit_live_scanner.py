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
