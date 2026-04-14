from evidentia.auditor import verify_quote


def test_verify_quote_accepts_exact_match(tmp_path):
    source_text = "I need invoice chasing automation."
    result = verify_quote(
        source_text=source_text,
        source_url="https://example.com/post",
        verbatim_quote="invoice chasing automation",
    )

    assert result["verified"] is True


def test_verify_quote_rejects_missing_quote():
    result = verify_quote(
        source_text="Hello world",
        source_url="https://example.com/post",
        verbatim_quote="missing fragment",
    )

    assert result["verified"] is False
    assert result["reason"] == "quote_not_found"
