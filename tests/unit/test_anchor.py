from pathlib import Path

import pytest


def test_load_and_verify_fixture_anchor(tmp_path, monkeypatch):
    from evidentia import anchor, auditor

    monkeypatch.setattr(
        auditor,
        "_fetch_page_text",
        lambda url, **kw: "YouVersion has surpassed 500 million installs today",
    )
    yaml_text = """
slug: test-anchor
market_name: Test Market
incumbents: [IncumbentA]
proof_of_market:
  verbatim_quote: "YouVersion has surpassed 500 million installs"
  source_url: https://example.com/press
  timestamp: 2024-11-01T00:00:00Z
cohort_hints: []
primary_channel_queries: []
"""
    path = tmp_path / "a.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    loaded = anchor.load_anchor(path)
    verified = anchor.verify_anchor(loaded)
    assert verified.proof_of_market.verified is True
    assert verified.proof_of_market.proof_level == "fetched"


def test_unverifiable_anchor_raises(tmp_path, monkeypatch):
    from evidentia import anchor, auditor

    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url, **kw: None)
    yaml_text = """
slug: bad-anchor
market_name: Bad Market
incumbents: [IncumbentA]
proof_of_market:
  verbatim_quote: "not present anywhere"
  source_url: https://example.com/press
  timestamp: 2024-11-01T00:00:00Z
cohort_hints: []
primary_channel_queries: []
"""
    path = tmp_path / "b.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    loaded = anchor.load_anchor(path)
    with pytest.raises(anchor.AnchorVerificationError):
        anchor.verify_anchor(loaded)


def test_load_all_anchors_skips_unverifiable(tmp_path, monkeypatch):
    from evidentia import anchor, auditor

    good = """
slug: good-anchor
market_name: Good Market
incumbents: [IncumbentA]
proof_of_market:
  verbatim_quote: "good quote"
  source_url: https://example.com/good
  timestamp: 2024-11-01T00:00:00Z
cohort_hints: []
primary_channel_queries: []
"""
    bad = """
slug: bad-anchor
market_name: Bad Market
incumbents: [IncumbentA]
proof_of_market:
  verbatim_quote: "bad quote"
  source_url: https://example.com/bad
  timestamp: 2024-11-01T00:00:00Z
cohort_hints: []
primary_channel_queries: []
"""
    (tmp_path / "good.yaml").write_text(good, encoding="utf-8")
    (tmp_path / "bad.yaml").write_text(bad, encoding="utf-8")

    def _fake_fetch(url, **kwargs):
        if "good" in url:
            return "this page has good quote"
        return None

    monkeypatch.setattr(auditor, "_fetch_page_text", _fake_fetch)
    anchors = anchor.load_all_anchors(tmp_path)
    assert [item.slug for item in anchors] == ["good-anchor"]

