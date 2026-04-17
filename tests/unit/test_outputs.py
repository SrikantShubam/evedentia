from __future__ import annotations

from evidentia.models import Anchor, DemandSignal, Slice, SliceVerdict
from evidentia.outputs import append_to_index, read_index, top_ideas, write_run


def _anchor() -> Anchor:
    return Anchor(
        slug="bible-study-apps",
        market_name="Bible study apps",
        incumbents=["YouVersion"],
        proof_of_market=DemandSignal(
            signal_id="proof",
            source_url="https://example.com/proof",
            verbatim_quote="market exists",
            timestamp="2026-01-01T00:00:00Z",
            verified=True,
            proof_level="fetched",
        ),
    )


def _signals() -> list[DemandSignal]:
    return [
        DemandSignal(
            signal_id="s1",
            source_url="https://example.com/s1",
            verbatim_quote="Need trauma-aware bible plans",
            timestamp="2026-04-17T01:00:00Z",
            author="u1",
            signal_subtype="missing_feature",
            verified=True,
            proof_level="in_memory",
        ),
        DemandSignal(
            signal_id="s2",
            source_url="https://example.com/s2",
            verbatim_quote="Switching away from current app",
            timestamp="2026-04-17T01:01:00Z",
            author="u2",
            signal_subtype="switching_intent",
            verified=True,
            proof_level="in_memory",
        ),
    ]


def _slices() -> list[Slice]:
    return [
        Slice(
            slice_id="slice_a",
            anchor_slug="bible-study-apps",
            label="trauma-aware bible study for women",
            signal_ids=["s1", "s2"],
            author_count=2,
            dominant_subtype="missing_feature",
        )
    ]


def _verdicts(verdict: str = "REFINE") -> list[SliceVerdict]:
    return [
        SliceVerdict(
            slice_id="slice_a",
            anchor_slug="bible-study-apps",
            verdict=verdict,
            gates={
                "market_exists": True,
                "slice_has_voices": True,
                "slice_underserved": True,
                "reachable": True,
                "buildable": True,
            },
            heuristics={"competition_gap": 1.0, "buildability": 1.0, "reachability_strength": 1.0},
            refine_reason="insufficient_voice_density_for_pursue" if verdict == "REFINE" else None,
            next_test="Run landing-page test." if verdict == "REFINE" else "Ship manual wedge.",
            evidence_ids=["s1", "s2"],
        )
    ]


def test_write_run_and_index_round_trip(tmp_path):
    anchor = _anchor()
    signals = _signals()
    slices = _slices()
    verdicts = _verdicts()
    run_dir = tmp_path / "outputs" / "hunts" / anchor.slug / "2026-04-17T18-22-00Z"
    index_path = tmp_path / "outputs" / "best_ideas.jsonl"

    write_run(run_dir, anchor, signals, slices, verdicts, discards=[{"reason": "quote_not_verifiable"}])

    for filename in ("anchor.json", "signals.json", "slices.json", "verdicts.json", "discard_log.json", "summary.md"):
        assert (run_dir / filename).exists(), filename

    append_to_index(index_path, verdicts, anchor, run_dir)
    rows = read_index(index_path)
    assert len(rows) == 1
    assert rows[0]["schema_version"] == 1
    assert rows[0]["slice_id"] == "slice_a"
    assert rows[0]["label"] == "trauma-aware bible study for women"


def test_top_ideas_dedupes_and_skips_malformed_lines(tmp_path):
    anchor = _anchor()
    index_path = tmp_path / "outputs" / "best_ideas.jsonl"

    run_a = tmp_path / "outputs" / "hunts" / anchor.slug / "2026-04-17T18-22-00Z"
    write_run(run_a, anchor, _signals(), _slices(), _verdicts("PURSUE"), discards=[])
    append_to_index(index_path, _verdicts("PURSUE"), anchor, run_a)

    with index_path.open("a", encoding="utf-8") as fh:
        fh.write("{bad-json-line}\n")

    run_b = tmp_path / "outputs" / "hunts" / anchor.slug / "2026-04-17T18-30-00Z"
    newer_slice = [
        Slice(
            slice_id="slice_a",
            anchor_slug="bible-study-apps",
            label="trauma-aware bible study for women",
            signal_ids=["s1", "s2", "s3"],
            author_count=5,
            dominant_subtype="missing_feature",
        ),
        Slice(
            slice_id="slice_b",
            anchor_slug="bible-study-apps",
            label="audio-first bible plans for commuters",
            signal_ids=["s4", "s5"],
            author_count=4,
            dominant_subtype="usability_complaint",
        ),
    ]
    write_run(run_b, anchor, _signals(), newer_slice, _verdicts("PURSUE") + [
        SliceVerdict(
            slice_id="slice_b",
            anchor_slug="bible-study-apps",
            verdict="PURSUE",
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
            evidence_ids=["s4", "s5"],
        )
    ], discards=[])
    append_to_index(index_path, _verdicts("PURSUE"), anchor, run_b)
    append_to_index(
        index_path,
        [
            SliceVerdict(
                slice_id="slice_b",
                anchor_slug="bible-study-apps",
                verdict="PURSUE",
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
                evidence_ids=["s4", "s5"],
            )
        ],
        anchor,
        run_b,
    )

    rows = read_index(index_path)
    assert len(rows) == 3

    pursue = top_ideas(index_path, verdict="PURSUE", n=20)
    assert [row["slice_id"] for row in pursue] == ["slice_a", "slice_b"]
    assert pursue[0]["run_dir"].endswith("2026-04-17T18-30-00Z")
