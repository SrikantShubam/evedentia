from __future__ import annotations

import html
import re
import urllib.request


_AUDITOR_USER_AGENT = "evidentia/0.1"
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def _strip_html_tags(raw_text: str) -> str:
    without_tags = _HTML_TAG_PATTERN.sub(" ", raw_text)
    unescaped = html.unescape(without_tags)
    return _WHITESPACE_PATTERN.sub(" ", unescaped).strip()


def _normalize_text(raw_text: str) -> str:
    text = raw_text.lower()
    text = re.sub(r"[^\w\s]", " ", text)  # Replace punctuation with spaces
    return _WHITESPACE_PATTERN.sub(" ", text).strip()


def _fetch_page_text(url: str, max_bytes: int = 102_400, timeout: float = 15.0) -> str | None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": _AUDITOR_USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_bytes = response.read(max_bytes)
    except Exception:  # noqa: BLE001
        return None

    decoded = raw_bytes.decode("utf-8", errors="replace")
    return _strip_html_tags(decoded)


def verify_quote(candidate: dict | None = None, **legacy_kwargs) -> dict:
    if candidate is None:
        candidate = legacy_kwargs
    source_url = str(candidate.get("source_url", ""))
    quote = str(candidate.get("verbatim_quote", ""))
    normalized_quote = _normalize_text(quote)

    if not source_url or not normalized_quote:
        return {
            "verified": False,
            "source_url": source_url,
            "proof_level": "none",
            "discard_reason": "quote_not_verifiable",
            "reason": "quote_not_verifiable",
        }

    fetched_text = _fetch_page_text(source_url)
    if fetched_text is not None:
        if normalized_quote in _normalize_text(fetched_text):
            return {"verified": True, "source_url": source_url, "proof_level": "fetched"}

    source_text = str(candidate.get("source_text", ""))
    if normalized_quote and source_text and normalized_quote in _normalize_text(source_text):
        return {"verified": True, "source_url": source_url, "proof_level": "in_memory"}

    return {
        "verified": False,
        "source_url": source_url,
        "proof_level": "none",
        "discard_reason": "quote_not_verifiable",
        "reason": "quote_not_verifiable",
    }
