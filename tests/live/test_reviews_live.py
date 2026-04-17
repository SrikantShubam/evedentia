from __future__ import annotations

import pytest

from evidentia.anchor import load_all_anchors
from evidentia.scanners.reviews import listen


@pytest.mark.live
def test_reviews_live_smoke():
    anchors = load_all_anchors()
    if not anchors:
        pytest.skip("no verified anchors available for live run")

    target = next((item for item in anchors if item.slug == "bible-study-apps"), anchors[0])
    signals = listen(target, limit=3)
    if not signals:
        pytest.skip("live sources returned no signals")

    signal = signals[0]
    assert signal.signal_id
    assert signal.source_url.startswith("http")
    assert signal.verbatim_quote
    assert signal.proof_level in {"fetched", "in_memory"}
