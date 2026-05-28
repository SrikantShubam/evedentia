from evidentia.models import Anchor, DemandSignal, Slice, SliceVerdict


def test_signal_dataclass_instantiation():
    signal = DemandSignal(
        signal_id=DemandSignal.build_signal_id("https://example.com/post", "I need this now"),
        source_url="https://example.com/post",
        verbatim_quote="I need this now",
        timestamp="2026-04-17T00:00:00Z",
        source_kind="reddit",
        signal_subtype="missing_feature",
    )
    assert signal.signal_id
    assert signal.source_url.startswith("https://")


def test_anchor_slice_and_verdict_dataclasses():
    signal = DemandSignal(
        signal_id="sig_1",
        source_url="https://example.com/post",
        verbatim_quote="I need this now",
        timestamp="2026-04-17T00:00:00Z",
    )
    anchor = Anchor(
        slug="test-anchor",
        market_name="Test Market",
        incumbents=["IncumbentA"],
        proof_of_market=signal,
    )
    slice_obj = Slice(
        slice_id="slice_1",
        anchor_slug=anchor.slug,
        label="test slice",
        signal_ids=[signal.signal_id],
        author_count=3,
        dominant_subtype="missing_feature",
    )
    verdict = SliceVerdict(
        slice_id=slice_obj.slice_id,
        anchor_slug=anchor.slug,
        verdict="REFINE",
        gates={"market_exists": True},
        heuristics={"buildability": 0.5},
        refine_reason="test",
        next_test="do something",
        evidence_ids=[signal.signal_id],
    )
    assert anchor.to_dict()["slug"] == "test-anchor"
    assert slice_obj.to_dict()["author_count"] == 3
    assert verdict.to_dict()["schema_version"] == 1
