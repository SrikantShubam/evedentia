def verify_quote(source_text: str, source_url: str, verbatim_quote: str) -> dict:
    if verbatim_quote in source_text:
        return {"verified": True, "source_url": source_url}
    return {"verified": False, "source_url": source_url, "reason": "quote_not_found"}
