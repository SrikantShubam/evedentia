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


def test_choose_search_provider_default_is_ddg():
    """choose_search_provider returns DuckDuckGo by default (no env set)."""
    import os
    from evidentia.providers import choose_search_provider

    provider = choose_search_provider()
    assert provider.name == "duckduckgo_web", (
        f"Expected 'duckduckgo_web' provider, got '{provider.name}'. "
        "Default should be DuckDuckGo when SEARXNG_URL is not set."
    )


def test_choose_search_provider_searxng_when_url_set():
    """choose_search_provider returns SearXNG when SEARXNG_URL is set."""
    import os
    os.environ["SEARXNG_URL"] = "http://127.0.0.1:8888"
    from evidentia.providers import choose_search_provider
    provider = choose_search_provider()
    assert provider.name == "searxng"
