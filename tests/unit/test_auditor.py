from evidentia.auditor import verify_quote


def test_verify_quote_fetched_path(monkeypatch):
    from evidentia import auditor

    monkeypatch.setattr(
        auditor,
        "_fetch_page_text",
        lambda url, **kw: "some page with the verbatim quote inside",
    )
    result = verify_quote(
        {
            "source_url": "https://example.com/x",
            "verbatim_quote": "verbatim quote",
            "source_text": "unrelated",
        }
    )
    assert result["verified"] is True
    assert result["proof_level"] == "fetched"


def test_verify_quote_in_memory_fallback(monkeypatch):
    from evidentia import auditor

    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url, **kw: None)
    result = verify_quote(
        {
            "source_url": "https://example.com/x",
            "verbatim_quote": "present here",
            "source_text": "present here",
        }
    )
    assert result["verified"] is True
    assert result["proof_level"] == "in_memory"


def test_verify_quote_unverifiable(monkeypatch):
    from evidentia import auditor

    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url, **kw: None)
    result = verify_quote(
        {
            "source_url": "https://example.com/x",
            "verbatim_quote": "not anywhere",
            "source_text": "unrelated",
        }
    )
    assert result["verified"] is False
    assert result["proof_level"] == "none"
    assert result["discard_reason"] == "quote_not_verifiable"
