from evidentia.models import DemandSignal, Opportunity, ProductSpec
from pydantic import ValidationError


def test_signal_requires_source_and_quote():
    signal = DemandSignal(
        source_url="https://example.com/post",
        verbatim_quote="I need this now",
        signal_type="pain",
        source_strength="strong",
    )

    assert str(signal.source_url).startswith("https://")
    assert signal.verbatim_quote == "I need this now"


def test_opportunity_contains_gate_fields():
    opp = Opportunity(
        opportunity_id="opp_001",
        title="Reduce invoice chase time",
        willingness_to_pay="pass",
        distribution_channel="pass",
        data_feasibility="pass",
    )

    assert opp.willingness_to_pay == "pass"


def test_product_spec_requires_review_and_sources():
    spec = ProductSpec(
        opportunity_id="opp_001",
        title="Invoice chase automation",
        approved=False,
        sources=[{"source_url": "https://example.com/post", "verbatim_quote": "I need this"}],
    )

    assert spec.approved is False
    assert len(spec.sources) == 1


def test_signal_rejects_invalid_url_and_empty_quote():
    try:
        DemandSignal(
            source_url="not-a-url",
            verbatim_quote="",
            signal_type="pain",
            source_strength="strong",
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("DemandSignal accepted invalid evidence")


def test_product_spec_rejects_malformed_sources():
    try:
        ProductSpec(
            opportunity_id="opp_001",
            title="Invoice chase automation",
            approved=False,
            sources=[{}],
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("ProductSpec accepted malformed sources")
