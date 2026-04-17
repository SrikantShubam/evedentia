from __future__ import annotations

import json

from evidentia.loop import run_loop
from evidentia.models import Anchor, DemandSignal, Slice, SliceVerdict


def _anchor() -> Anchor:
    return Anchor(
        slug="fixture-anchor",
        market_name="Fixture Market",
        incumbents=["FixtureApp"],
        proof_of_market=DemandSignal(
            signal_id="proof",
            source_url="https://example.com/proof",
            verbatim_quote="fixture market exists",
            timestamp="2026-01-01T00:00:00Z",
            verified=True,
            proof_level="fetched",
        ),
        cohort_hints=["women"],
        primary_channel_queries=["site:reddit.com/r/fixtureapp missing"],
    )


def test_run_loop_appends_index_and_returns_summary(monkeypatch, tmp_path):
    anchor = _anchor()
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        "evidentia.loop.generate_ideas_from_anchor",
        lambda anchor, count=10, env=None: [
            {"label": "idea one", "cohort": "women", "pain_hypothesis": "pain", "search_queries": ["q1", "q2"]},
            {"label": "idea two", "cohort": "women", "pain_hypothesis": "pain", "search_queries": ["q3", "q4"]},
        ][:count],
    )
    monkeypatch.setattr(
        "evidentia.loop.generate_ideas_from_pursue",
        lambda pursue_entries, count=10, env=None: [
            {"label": "seeded idea", "cohort": "women", "pain_hypothesis": "pain", "search_queries": ["q5", "q6"]}
        ][:count],
    )
    monkeypatch.setattr(
        "evidentia.loop.listen_for_idea",
        lambda anchor, idea, limit=20, env=None: [
            DemandSignal(
                signal_id=f"{idea['label']}-s1",
                source_url="https://www.reddit.com/r/fixtureapp/comments/1",
                verbatim_quote="Need this missing feature",
                timestamp="2026-04-17T00:00:00Z",
                author="u1",
                signal_subtype="missing_feature",
                verified=True,
                proof_level="in_memory",
            ),
            DemandSignal(
                signal_id=f"{idea['label']}-s2",
                source_url="https://www.reddit.com/r/fixtureapp/comments/2",
                verbatim_quote="Looking for alternative app now",
                timestamp="2026-04-17T00:01:00Z",
                author="u2",
                signal_subtype="switching_intent",
                verified=True,
                proof_level="in_memory",
            ),
        ],
    )
    monkeypatch.setattr(
        "evidentia.loop.cluster_signals",
        lambda anchor, signals, jaccard_threshold=0.35, llm_labeler=None: [
            Slice(
                slice_id=f"slice-{signals[0].signal_id}",
                anchor_slug=anchor.slug,
                label="fixture slice",
                signal_ids=[signal.signal_id for signal in signals],
                author_count=5,
                dominant_subtype="missing_feature",
            )
        ],
    )
    monkeypatch.setattr(
        "evidentia.loop.critique_slice",
        lambda slice, signals_by_id, anchor, env=None: SliceVerdict(
            slice_id=slice.slice_id,
            anchor_slug=anchor.slug,
            verdict="PURSUE" if "idea one" in slice.slice_id else "REFINE",
            gates={
                "market_exists": True,
                "slice_has_voices": True,
                "slice_underserved": True,
                "reachable": True,
                "buildable": True,
            },
            heuristics={"competition_gap": 1.0, "buildability": 1.0, "reachability_strength": 1.0},
            refine_reason=None,
            next_test="Ship manual wedge.",
            evidence_ids=list(signals_by_id.keys()),
        ),
    )

    summary = run_loop([anchor], iterations=2, ideas_per_iter=2, env={})

    index_path = tmp_path / summary["index_path"]
    assert summary["iterations_completed"] == 2
    assert summary["verdict_counts"]["PURSUE"] >= 1
    assert index_path.exists()

    lines = [line for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 1
    for line in lines:
        payload = json.loads(line)
        assert payload["schema_version"] == 1
        assert payload["slice_id"]
