from __future__ import annotations

import json

from evidentia import critic
from evidentia.clusterer import cluster_signals
from evidentia.models import Anchor, DemandSignal
from evidentia.outputs import append_to_index, write_run


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
        primary_channel_queries=["site:reddit.com/r/fixtureapp missing feature"],
    )


def _signals() -> list[DemandSignal]:
    return [
        DemandSignal(
            signal_id="s1",
            source_url="https://www.reddit.com/r/fixtureapp/comments/1",
            verbatim_quote="Wish it had better onboarding for women",
            timestamp="2026-04-17T00:00:00Z",
            title="missing onboarding",
            source_text="Wish it had better onboarding for women",
            signal_subtype="missing_feature",
            author="u1",
            verified=True,
            proof_level="in_memory",
        ),
        DemandSignal(
            signal_id="s2",
            source_url="https://www.reddit.com/r/fixtureapp/comments/2",
            verbatim_quote="Need women-specific onboarding and safer language",
            timestamp="2026-04-17T00:01:00Z",
            title="women onboarding request",
            source_text="Need women-specific onboarding and safer language",
            signal_subtype="missing_feature",
            author="u2",
            verified=True,
            proof_level="in_memory",
        ),
        DemandSignal(
            signal_id="s3",
            source_url="https://www.reddit.com/r/fixtureapp/comments/3",
            verbatim_quote="Looking for alternatives with gentler onboarding",
            timestamp="2026-04-17T00:02:00Z",
            title="switching away",
            source_text="Looking for alternatives with gentler onboarding",
            signal_subtype="missing_feature",
            author="u3",
            verified=True,
            proof_level="in_memory",
        ),
    ]


def test_hunt_pipeline_fixture(monkeypatch, tmp_path):
    anchor = _anchor()
    signals = _signals()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        critic,
        "_gate_slice_underserved",
        lambda slice_obj, anchor, env, **kwargs: (True, {"underserved": "yes", "named_competitors": []}),
    )

    slices = cluster_signals(anchor, signals, jaccard_threshold=0.15)
    assert slices
    signals_by_id = {signal.signal_id: signal for signal in signals}
    verdicts = [critic.critique_slice(slice_obj, signals_by_id, anchor, env={"EVIDENTIA_DRY_RUN": "1"}) for slice_obj in slices]

    run_dir = tmp_path / "outputs" / "hunts" / anchor.slug / "2026-04-17T18-22-00Z"
    index_path = tmp_path / "outputs" / "best_ideas.jsonl"
    write_run(run_dir, anchor, signals, slices, verdicts, discards=[])
    append_to_index(index_path, verdicts, anchor, run_dir)

    for filename in ("anchor.json", "signals.json", "slices.json", "verdicts.json", "discard_log.json", "summary.md"):
        assert (run_dir / filename).exists(), filename

    rows = [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows
    assert rows[0]["schema_version"] == 1
