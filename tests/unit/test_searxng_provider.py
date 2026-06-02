"""Tests for SearXNGSearchProvider in providers.py.

These tests verify:
- SearXNG returns real search results for a niche query
- Empty queries are handled without network calls
- Unreachable SearXNG raises ProviderError (not generic exception)

Prerequisites: SearXNG must be running at 127.0.0.1:8888
with format=json enabled in settings.yml.
"""

import os
import pytest


# --- Helpers ---

def _provider():
    from evidentia.providers import SearXNGSearchProvider
    url = os.environ.get("SEARXNG_URL", "http://127.0.0.1:8888")
    return SearXNGSearchProvider(base_url=url)


# --- Tests ---

def test_searxng_returns_hits():
    """SearXNG at 127.0.0.1:8888 responds with real results."""
    provider = _provider()
    hits = provider.search("latest technology trends", max_results=3)
    assert len(hits) > 0, (
        "SearXNG must return at least one result. "
        "Is SearXNG running at 127.0.0.1:8888? "
        "Run: docker run -d --name evidentia-searxng -p 127.0.0.1:8888:8080 "
        "-v %cd%/searxng/settings.yml:/etc/searxng/settings.yml:ro searxng/searxng"
    )
    for h in hits:
        assert h.url.startswith("http"), f"Bad URL: {h.url}"
        assert len(h.title) > 0, f"Empty title for {h.url}"
        assert len(h.snippet) > 0, f"Empty snippet for {h.url}"


def test_searxng_empty_query_returns_empty():
    """Empty or whitespace query returns empty list without network call."""
    provider = _provider()
    assert provider.search("", max_results=5) == []
    assert provider.search("   ", max_results=5) == []


def test_searxng_unreachable_raises_provider_error():
    """Unreachable SearXNG raises ProviderError, not a generic exception."""
    from evidentia.providers import SearXNGSearchProvider, ProviderError

    provider = SearXNGSearchProvider(
        base_url="http://127.0.0.1:19999",
        timeout=2,
    )
    with pytest.raises(ProviderError):
        provider.search("test", max_results=1)


def test_searxng_max_results_respected():
    """Provider never returns more than max_results hits."""
    provider = _provider()
    hits = provider.search("software", max_results=2)
    assert len(hits) <= 2


def test_searxng_hits_have_valid_searchhit_shape():
    """Every returned hit matches the SearchHit dataclass shape."""
    from evidentia.providers import SearchHit
    provider = _provider()
    hits = provider.search("test", max_results=2)
    for h in hits:
        assert isinstance(h, SearchHit)
        assert isinstance(h.title, str)
        assert isinstance(h.url, str)
        assert isinstance(h.snippet, str)
