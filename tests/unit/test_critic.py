from __future__ import annotations

import pytest

from evidentia import critic
from evidentia.models import Anchor, DemandSignal, Slice, Verdict


def _anchor(*, market_verified: bool = True) -> Anchor:
    return Anchor(
        slug="bible-study-apps",
        market_name="Bible study apps",
        incumbents=["YouVersion"],
        proof_of_market=DemandSignal(
            signal_id="proof",
            source_url="https://example.com/proof",
            verbatim_quote="market exists",
            timestamp="2026-01-01T00:00:00Z",
            verified=market_verified,
            proof_level="fetched" if market_verified else "none",
        ),
        cohort_hints=["post-evangelical"],
        primary_channel_queries=["site:reddit.com/r/exvangelical YouVersion missing"],
    )


def _signal(signal_id: str, *, author: str, quote: str = "Need trauma-aware content", url: str | None = None) -> DemandSignal:
    return DemandSignal(
        signal_id=signal_id,
        source_url=url or f"https://www.reddit.com/r/exvangelical/comments/{signal_id}",
        verbatim_quote=quote,
        timestamp="2026-04-17T00:00:00Z",
        signal_subtype="missing_feature",
        author=author,
        verified=True,
        proof_level="fetched",
    )


def _slice(author_count: int, signal_ids: list[str]) -> Slice:
    return Slice(
        slice_id="slice-1",
        anchor_slug="bible-study-apps",
        label="trauma-aware bible study for women",
        signal_ids=signal_ids,
        author_count=author_count,
        dominant_subtype="missing_feature",
    )


def test_gate_market_exists():
    assert critic._gate_market_exists(_anchor(market_verified=True)) is True
    assert critic._gate_market_exists(_anchor(market_verified=False)) is False


def test_gate_slice_has_voices():
    assert critic._gate_slice_has_voices(_slice(3, ["s1", "s2", "s3"])) is True
    assert critic._gate_slice_has_voices(_slice(2, ["s1", "s2"])) is False


def test_gate_reachable():
    reachable = critic._gate_reachable(
        _slice(3, ["s1", "s2", "s3"]),
        _anchor(),
        [
            _signal("s1", author="u1", url="https://www.reddit.com/r/exvangelical/comments/abc"),
            _signal("s2", author="u2", url="https://example.com/no-channel"),
        ],
    )
    unreachable = critic._gate_reachable(
        _slice(3, ["s1", "s2", "s3"]),
        _anchor(),
        [_signal("s1", author="u1", url="https://example.com/no-channel")],
    )
    assert reachable is True
    assert unreachable is False


def test_gate_buildable_counts_integrations():
    signals = [
        _signal("s1", author="u1", quote="Need stripe and quickbooks sync"),
        _signal("s2", author="u2", quote="Also need salesforce and twilio integration"),
    ]
    assert critic._gate_buildable(_slice(3, ["s1", "s2"]), signals) is False
    assert critic._gate_buildable(_slice(3, ["s1", "s2"]), [_signal("s3", author="u3", quote="Need stripe sync")]) is True


def test_gate_slice_underserved_uses_search_and_llm():
    class FakeSearchProvider:
        def search(self, query: str, max_results: int = 5):  # noqa: ARG002
            return [type("Hit", (), {"title": "Incumbent app for this niche"})()]

    class FakeLlmProvider:
        def generate_json(self, prompt: str, model: str):  # noqa: ARG002
            return {"underserved": "yes", "named_competitors": ["Incumbent App"]}

    passed, details = critic._gate_slice_underserved(
        _slice(3, ["s1", "s2", "s3"]),
        _anchor(),
        env={},
        search_provider=FakeSearchProvider(),
        llm_provider=FakeLlmProvider(),
        llm_model="fake",
    )
    assert passed is True
    assert details["named_competitors"] == ["Incumbent App"]


def test_verdict_kill_when_market_or_underserved_fails(monkeypatch):
    signals = {signal.signal_id: signal for signal in [_signal("s1", author="u1"), _signal("s2", author="u2"), _signal("s3", author="u3")]}
    test_slice = _slice(3, list(signals.keys()))

    monkeypatch.setattr(critic, "_gate_slice_underserved", lambda *_args, **_kwargs: (True, {"underserved": "yes", "named_competitors": []}))
    verdict_market_fail = critic.critique_slice(test_slice, signals, _anchor(market_verified=False), env={})
    assert verdict_market_fail.verdict == Verdict.KILL.value
    assert verdict_market_fail.next_test is None

    monkeypatch.setattr(critic, "_gate_slice_underserved", lambda *_args, **_kwargs: (False, {"underserved": "no", "named_competitors": ["Foo"]}))
    verdict_underserved_fail = critic.critique_slice(test_slice, signals, _anchor(), env={})
    assert verdict_underserved_fail.verdict == Verdict.KILL.value
    assert verdict_underserved_fail.next_test is None


def test_verdict_pursue_and_refine_paths(monkeypatch):
    pursue_signals = {
        signal.signal_id: signal
        for signal in [
            _signal("s1", author="u1"),
            _signal("s2", author="u2"),
            _signal("s3", author="u3"),
            _signal("s4", author="u4"),
            _signal("s5", author="u5"),
        ]
    }
    pursue_slice = _slice(5, list(pursue_signals.keys()))

    monkeypatch.setattr(critic, "_gate_slice_underserved", lambda *_args, **_kwargs: (True, {"underserved": "yes", "named_competitors": []}))
    pursue = critic.critique_slice(pursue_slice, pursue_signals, _anchor(), env={})
    assert pursue.verdict == Verdict.PURSUE.value
    assert pursue.next_test is not None

    refine_signals = {signal.signal_id: signal for signal in [_signal("s1", author="u1"), _signal("s2", author="u2"), _signal("s3", author="u3")]}
    refine_slice = _slice(3, list(refine_signals.keys()))
    refine = critic.critique_slice(refine_slice, refine_signals, _anchor(), env={})
    assert refine.verdict == Verdict.REFINE.value
    assert refine.next_test is not None


def test_refine_requires_next_test(monkeypatch):
    signals = {signal.signal_id: signal for signal in [_signal("s1", author="u1"), _signal("s2", author="u2"), _signal("s3", author="u3")]}
    test_slice = _slice(3, list(signals.keys()))
    monkeypatch.setattr(critic, "_gate_slice_underserved", lambda *_args, **_kwargs: (True, {"underserved": "yes", "named_competitors": []}))
    monkeypatch.setattr(critic, "_build_refine_next_test", lambda *_args, **_kwargs: None)
    with pytest.raises(AssertionError):
        critic.critique_slice(test_slice, signals, _anchor(), env={})
