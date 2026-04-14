from evidentia.scanners.hn import scan_hn_live


def test_hn_live_scanner_normalizes_algolia_hits():
    def fake_fetch_json(url: str) -> dict:
        return {
            "hits": [
                {
                    "objectID": "123",
                    "title": "Need invoice automation",
                    "story_text": "We would pay for a tool that automates invoice reminders.",
                    "created_at": "2026-04-14T00:00:00Z",
                }
            ]
        }

    results = scan_hn_live("invoice automation", max_results=1, fetch_json=fake_fetch_json)

    assert len(results) == 1
    assert results[0]["source"] == "hn"
    assert results[0]["source_url"] == "https://news.ycombinator.com/item?id=123"
    assert "invoice reminders" in results[0]["source_text"]
    assert results[0]["verbatim_quote"]
