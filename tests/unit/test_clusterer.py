from __future__ import annotations

from evidentia.clusterer import cluster_signals
from evidentia.models import Anchor, DemandSignal


def _anchor(*, cohort_hints: list[str] | None = None) -> Anchor:
    return Anchor(
        slug="fitness-apps",
        market_name="Fitness apps",
        incumbents=["Acme Fit"],
        proof_of_market=DemandSignal(
            signal_id="proof",
            source_url="https://example.com/proof",
            verbatim_quote="millions of users",
            timestamp="2026-01-01T00:00:00Z",
            verified=True,
            proof_level="fetched",
        ),
        cohort_hints=cohort_hints or [],
    )


def _signal(
    signal_id: str,
    quote: str,
    *,
    subtype: str = "missing_feature",
    author: str | None = None,
    title: str = "",
) -> DemandSignal:
    return DemandSignal(
        signal_id=signal_id,
        source_url=f"https://example.com/{signal_id}",
        verbatim_quote=quote,
        timestamp="2026-04-17T00:00:00Z",
        title=title or None,
        signal_subtype=subtype,
        author=author,
        verified=True,
        proof_level="in_memory",
    )


def test_cluster_signals_applies_jaccard_threshold_and_stable_slice_id():
    anchor = _anchor()
    signals = [
        _signal("s1", "Need csv export for invoice reports", author="u1"),
        _signal("s2", "Wish it had csv export for reports", author="u2"),
        _signal("s3", "The onboarding is confusing and clunky", subtype="usability_complaint", author="u3"),
    ]

    first = cluster_signals(anchor, signals, jaccard_threshold=0.35, llm_labeler=None)
    second = cluster_signals(anchor, signals, jaccard_threshold=0.35, llm_labeler=None)

    assert len(first) == 1
    assert first[0].signal_ids == ["s1", "s2"]
    assert first[0].slice_id == second[0].slice_id
    assert first[0].label == "cluster_1"


def test_cluster_signals_enforces_subtype_gate():
    anchor = _anchor()
    signals = [
        _signal("s1", "Need csv export for invoice reports", subtype="missing_feature", author="u1"),
        _signal("s2", "Need csv export for invoice reports", subtype="pricing_complaint", author="u2"),
    ]

    slices = cluster_signals(anchor, signals, jaccard_threshold=0.1)
    assert slices == []


def test_cluster_signals_applies_cohort_boost():
    anchor = _anchor(cohort_hints=["women"])
    signals = [
        _signal("s1", "Need onboarding templates for women professionals", author="u1"),
        _signal("s2", "Wish it had onboarding templates for professionals", author="u2"),
    ]

    slices = cluster_signals(anchor, signals, jaccard_threshold=0.55)
    assert len(slices) == 1
    assert slices[0].signal_ids == ["s1", "s2"]


def test_cluster_signals_drops_clusters_with_less_than_two_authors():
    anchor = _anchor()
    signals = [
        _signal("s1", "Need csv export for invoices", author="same-user"),
        _signal("s2", "Wish it had csv export too", author="same-user"),
    ]

    slices = cluster_signals(anchor, signals, jaccard_threshold=0.2)
    assert slices == []
