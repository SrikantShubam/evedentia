from __future__ import annotations

from evidentia.models import Anchor, DemandSignal
from evidentia.scanners import reviews


def _anchor_fixture() -> Anchor:
    return Anchor(
        slug="test-anchor",
        market_name="Test Market",
        incumbents=["Acme App"],
        proof_of_market=DemandSignal(
            signal_id="proof1",
            source_url="https://example.com/proof",
            verbatim_quote="market exists",
            timestamp="2026-01-01T00:00:00Z",
            verified=True,
            proof_level="fetched",
        ),
        cohort_hints=["women"],
        primary_channel_queries=["site:reddit.com acme app missing feature"],
    )


def test_listen_collects_and_tags_signals(monkeypatch):
    anchor = _anchor_fixture()

    def fake_http_json(url, **kwargs):  # noqa: ARG001
        if "itunes.apple.com/search" in url:
            return {"results": [{"trackId": 12345}]}
        if "itunes.apple.com/us/rss/customerreviews" in url:
            return {
                "feed": {
                    "entry": [
                        {
                            "im:rating": {"label": "2"},
                            "title": {"label": "Needs better women onboarding"},
                            "content": {"label": "Wish it had better onboarding for women"},
                            "id": {"label": "https://apps.example/reviews/1"},
                            "updated": {"label": "2026-04-17T12:01:00Z"},
                            "author": {"name": {"label": "ios_user_1"}},
                        },
                        {
                            "im:rating": {"label": "5"},
                            "title": {"label": "Great app"},
                            "content": {"label": "Love it"},
                            "id": {"label": "https://apps.example/reviews/2"},
                            "updated": {"label": "2026-04-17T12:00:00Z"},
                            "author": {"name": {"label": "ios_user_2"}},
                        },
                    ]
                }
            }
        if "reddit.com/r/acmeapp/new.json" in url:
            return {
                "data": {
                    "children": [
                        {
                            "data": {
                                "permalink": "/r/acmeapp/comments/abc123/help/",
                                "title": "Too expensive now",
                                "selftext": "This is too expensive and behind a paywall",
                                "author": "reddit_user_1",
                                "created_utc": 1713350000,
                            }
                        }
                    ]
                }
            }
        raise AssertionError(f"unexpected url {url}")

    class FakeSearchProvider:
        def search(self, query: str, max_results: int = 5):  # noqa: ARG002
            return [
                type(
                    "Hit",
                    (),
                    {
                        "title": "Switching thread",
                        "url": "https://example.com/search/switching",
                        "snippet": "I am looking for alternative tools after replacing Acme",
                    },
                )(),
                type(
                    "Hit",
                    (),
                    {
                        "title": "Discarded hit",
                        "url": "https://example.com/search/discard",
                        "snippet": "discard this result",
                    },
                )(),
            ]

    def fake_verify_quote(candidate):
        quote = str(candidate.get("verbatim_quote", ""))
        if "discard this result" in quote:
            return {"verified": False, "proof_level": "none"}
        return {"verified": True, "proof_level": "in_memory"}

    monkeypatch.setattr(reviews, "_http_json", fake_http_json)
    monkeypatch.setattr(reviews, "scan_reddit_live", lambda query, max_results=3: [  # noqa: ARG005
        {
            "source": "reddit",
            "title": "Acme is clunky",
            "source_url": "https://www.reddit.com/r/acmeapp/comments/clunky/",
            "verbatim_quote": "The UI is confusing and hard to use",
            "source_text": "The UI is confusing and hard to use",
            "cluster_id": "reddit:/r/acmeapp/comments/clunky/",
            "published_at": "2026-04-17T12:02:00Z",
        }
    ])
    monkeypatch.setattr(reviews, "choose_search_provider", lambda env: FakeSearchProvider())  # noqa: ARG005
    monkeypatch.setattr(reviews.auditor, "verify_quote", fake_verify_quote)
    monkeypatch.setattr(reviews, "sleep", lambda seconds: None)  # noqa: ARG005

    signals = reviews.listen(anchor, limit=20, env={})

    assert len(signals) >= 4
    assert all(isinstance(signal, DemandSignal) for signal in signals)
    assert all(signal.proof_level in {"fetched", "in_memory"} for signal in signals)
    assert all(signal.signal_id for signal in signals)
    assert all("discard" not in signal.source_url for signal in signals)
    assert "missing_feature" in {signal.signal_subtype for signal in signals}
    assert "pricing_complaint" in {signal.signal_subtype for signal in signals}
    assert "usability_complaint" in {signal.signal_subtype for signal in signals}
    assert "switching_intent" in {signal.signal_subtype for signal in signals}
    assert all(signal.complaint_type for signal in signals)
    unknowns = [signal for signal in signals if signal.complaint_type == "UNKNOWN_WITH_REASON"]
    assert all(signal.complaint_type_reason for signal in unknowns)


def test_listen_survives_single_source_failures(monkeypatch):
    anchor = _anchor_fixture()

    class FakeSearchProvider:
        def search(self, query: str, max_results: int = 5):  # noqa: ARG002
            return [
                type(
                    "Hit",
                    (),
                    {
                        "title": "Fallback signal",
                        "url": "https://example.com/fallback",
                        "snippet": "needs a better feature for women",
                    },
                )()
            ]

    monkeypatch.setattr(reviews, "_http_json", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(reviews, "scan_reddit_live", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(reviews, "choose_search_provider", lambda env: FakeSearchProvider())  # noqa: ARG005
    monkeypatch.setattr(reviews.auditor, "verify_quote", lambda candidate: {"verified": True, "proof_level": "in_memory"})
    monkeypatch.setattr(reviews, "sleep", lambda seconds: None)  # noqa: ARG005

    signals = reviews.listen(anchor, limit=5, env={})

    assert signals
    assert signals[0].source_url == "https://example.com/fallback"
