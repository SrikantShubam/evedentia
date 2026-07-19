"""Tests verifying the web_search scanner is properly registered.

These tests ensure the scanner is discoverable by the scan pipeline
(LIVE_SCANNERS dict) and the CLI dispatcher (_run_live_source).
"""


def test_web_search_in_live_scanners():
    """web_search is a registered key in LIVE_SCANNERS."""
    from evidentia.scanners import LIVE_SCANNERS
    assert "web_search" in LIVE_SCANNERS, (
        "web_search must be a key in LIVE_SCANNERS dict"
    )


def test_web_search_scanner_is_callable():
    """The registered scanner module exports a callable scan function."""
    from evidentia.scanners.web_search import scan_web_search_live
    assert callable(scan_web_search_live)


def test_web_search_in_cli_dispatcher():
    """_run_live_source accepts 'web_search' as a valid source."""
    from evidentia.cli import _run_live_source

    # Should not raise on valid source name
    try:
        candidates, attempt = _run_live_source("web_search", "test", 1)
    except Exception as exc:
        # May fail if SearXNG is down, but should NOT fail with
        # "unsupported live source" or ImportError
        error_msg = str(exc).lower()
        assert "unsupported" not in error_msg, (
            f"web_search not recognized by _run_live_source: {exc}"
        )
        assert "import" not in error_msg.lower(), (
            f"Import failed for web_search scanner: {exc}"
        )
        # Expected failure mode: ProviderError from SearXNG being down
        assert "providererror" in error_msg.lower() or \
               "transport_error" in str(candidates).lower(), (
            f"Unexpected error for web_search source: {exc}"
        )


def test_choose_search_provider_returns_fallback():
    """choose_search_provider returns FallbackSearchProvider (tries SearXNG first)."""
    from evidentia.providers import choose_search_provider
    provider = choose_search_provider()
    assert provider.name == "fallback", (
        f"Expected 'fallback' provider, got '{provider.name}'. "
        "choose_search_provider should return FallbackSearchProvider."
    )


def test_fallback_tries_searxng_first():
    """FallbackSearchProvider lists SearXNG as first provider (index 0)."""
    from evidentia.providers import FallbackSearchProvider
    provider = FallbackSearchProvider(searxng_url="http://127.0.0.1:8888")
    assert provider._providers[0].name == "searxng"
    assert any(p.name == "duckduckgo_web" for p in provider._providers)
