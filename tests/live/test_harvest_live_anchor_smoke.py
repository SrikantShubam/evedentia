from __future__ import annotations

import pytest

from evidentia.anchor import load_all_anchors
from evidentia.providers import load_external_provider_env
from evidentia.scanners.reviews import listen


@pytest.mark.live
def test_harvest_live_anchor_smoke():
    env = load_external_provider_env()
    anchors = load_all_anchors()
    if not anchors:
        pytest.skip("no verifiable anchors available")
    anchor = next((item for item in anchors if item.slug == "bible-study-apps"), anchors[0])
    signals = listen(anchor, limit=10, env=env)
    if not signals:
        pytest.skip("live harvest returned no signals")
    assert all(signal.source_url for signal in signals)
    assert all(signal.verbatim_quote for signal in signals)
    assert all(signal.complaint_type for signal in signals)
