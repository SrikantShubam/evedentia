from evidentia.models import ProductSpec


def write_spec(opportunity: dict) -> ProductSpec:
    sources = opportunity.get("verified_sources", opportunity.get("verified_signals", []))
    if not sources:
        raise ValueError("verified sources are required to write a spec")

    return ProductSpec(
        opportunity_id=opportunity["opportunity_id"],
        title=opportunity["title"],
        approved=False,
        sources=sources,
    )
