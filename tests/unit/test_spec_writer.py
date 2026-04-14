from evidentia.models import ProductSpec
from evidentia.spec_writer import write_spec
import pytest


def test_spec_includes_verified_sources_only():
    opportunity = {
        "opportunity_id": "opp_001",
        "title": "Invoice chase automation",
        "verified_sources": [
            {"source_url": "https://example.com/post", "verbatim_quote": "I need this"},
        ],
    }

    spec = write_spec(opportunity)

    assert isinstance(spec, ProductSpec)
    assert spec.opportunity_id == "opp_001"
    assert str(spec.sources[0].source_url) == "https://example.com/post"


def test_spec_writer_rejects_missing_verified_sources():
    with pytest.raises(ValueError, match="verified sources"):
        write_spec({"opportunity_id": "opp_001", "title": "Invoice chase automation"})
