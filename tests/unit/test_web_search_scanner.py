"""Tests for the web_search scanner.

Verifies that scan_web_search_live() produces candidate dicts with the
exact shape required by the scan pipeline (verify_quote → classify → score).

Prerequisites: SearXNG must be running at 127.0.0.1:8888.
"""

# --- Tests ---

def test_candidate_has_all_required_keys():
    """Every candidate dict has all 7 required keys.
    
    Note: SearXNG upstream engines may be rate-limited. This test
    skips if no results are returned (infra issue, not code issue).
    """
    from evidentia.scanners.web_search import scan_web_search_live

    required = {
        "source", "title", "source_url", "published_at",
        "verbatim_quote", "source_text", "cluster_id",
    }
    candidates = scan_web_search_live("latest technology trends", max_results=3)
    if len(candidates) == 0:
        import pytest
        pytest.skip("SearXNG returned 0 results — upstream rate limit or infra issue")
    for i, c in enumerate(candidates):
        missing = required - set(c.keys())
        assert not missing, f"Candidate {i}: missing keys {missing}"


def test_candidate_source_is_web_search():
    """Every candidate has source='web_search'."""
    from evidentia.scanners.web_search import scan_web_search_live

    candidates = scan_web_search_live("test", max_results=3)
    for c in candidates:
        assert c["source"] == "web_search"


def test_candidate_urls_start_with_http():
    """Every source_url is a valid HTTP(S) URL."""
    from evidentia.scanners.web_search import scan_web_search_live

    candidates = scan_web_search_live("test", max_results=3)
    for c in candidates:
        assert c["source_url"].startswith("http"), (
            f"Bad URL: {c['source_url']}"
        )


def test_candidate_titles_are_non_empty():
    """Every candidate has a non-empty title."""
    from evidentia.scanners.web_search import scan_web_search_live

    candidates = scan_web_search_live("test", max_results=3)
    for c in candidates:
        assert len(c["title"]) > 0, f"Empty title for {c.get('source_url')}"


def test_cluster_ids_are_unique():
    """No two candidates share a cluster_id."""
    from evidentia.scanners.web_search import scan_web_search_live

    candidates = scan_web_search_live("biodegradable packaging", max_results=5)
    ids = [c["cluster_id"] for c in candidates]
    assert len(ids) == len(set(ids)), (
        f"Duplicate cluster IDs found: {ids}"
    )


def test_cluster_id_starts_with_web_prefix():
    """All cluster_ids follow the 'web:{hash}' format."""
    from evidentia.scanners.web_search import scan_web_search_live

    candidates = scan_web_search_live("test", max_results=3)
    for c in candidates:
        assert c["cluster_id"].startswith("web:"), (
            f"Expected 'web:...' but got '{c['cluster_id']}'"
        )


def test_verbatim_quote_equals_source_text():
    """source_text mirrors verbatim_quote for web search results."""
    from evidentia.scanners.web_search import scan_web_search_live

    candidates = scan_web_search_live("test", max_results=3)
    for c in candidates:
        assert c["verbatim_quote"] == c["source_text"], (
            f"Mismatch for {c['source_url']}"
        )


def test_published_at_is_iso_format():
    """published_at is a valid ISO 8601 timestamp."""
    from evidentia.scanners.web_search import scan_web_search_live

    candidates = scan_web_search_live("test", max_results=3)
    for c in candidates:
        assert "T" in c["published_at"], (
            f"Expected ISO format, got '{c['published_at']}'"
        )


def test_max_results_respected():
    """Scanner never returns more than max_results candidates."""
    from evidentia.scanners.web_search import scan_web_search_live

    candidates = scan_web_search_live("software", max_results=2)
    assert len(candidates) <= 2
