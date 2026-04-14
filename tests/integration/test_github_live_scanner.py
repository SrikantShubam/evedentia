from evidentia.scanners.github import scan_github_live


def test_github_live_scanner_normalizes_issue_hits():
    def fake_fetch_json(url: str, headers=None) -> dict:
        return {
            "items": [
                {
                    "title": "Need hosted invoice reminder automation",
                    "body": "We would pay for a hosted tool that automates reminders.",
                    "html_url": "https://github.com/example/project/issues/123",
                    "updated_at": "2026-04-14T00:00:00Z",
                    "id": 123,
                }
            ]
        }

    results = scan_github_live("invoice reminder", max_results=1, fetch_json=fake_fetch_json)

    assert len(results) == 1
    assert results[0]["source"] == "github"
    assert results[0]["source_url"].startswith("https://github.com/")
    assert "would pay" in results[0]["source_text"].lower()
