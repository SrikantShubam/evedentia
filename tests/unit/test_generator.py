from __future__ import annotations

from evidentia.generator import GeneratorError, generate_ideas_from_anchor, generate_ideas_from_pursue
from evidentia.models import Anchor, DemandSignal


def _anchor() -> Anchor:
    return Anchor(
        slug="bible-study-apps",
        market_name="Bible study apps",
        incumbents=["YouVersion", "Bible.is"],
        proof_of_market=DemandSignal(
            signal_id="proof",
            source_url="https://example.com/proof",
            verbatim_quote="market exists",
            timestamp="2026-01-01T00:00:00Z",
            verified=True,
            proof_level="fetched",
        ),
        cohort_hints=["women", "post-evangelical"],
    )


def test_generate_ideas_from_anchor_shape_and_count():
    class FakeProvider:
        def generate_json(self, prompt: str, model: str):  # noqa: ARG002
            return {
                "ideas": [
                    {
                        "label": "trauma-aware bible plans",
                        "cohort": "post-evangelical women",
                        "pain_hypothesis": "Current apps feel spiritually unsafe after deconstruction.",
                        "search_queries": [
                            "site:reddit.com/r/exvangelical bible app missing",
                            "post evangelical bible study app alternative",
                        ],
                    },
                    {
                        "label": "audio-first bible plans",
                        "cohort": "commuters",
                        "pain_hypothesis": "Commute windows make text-heavy plans hard to complete.",
                        "search_queries": [
                            "bible app audio study complaints",
                            "reddit bible app commuting",
                        ],
                    },
                ]
            }

    ideas = generate_ideas_from_anchor(
        _anchor(),
        count=2,
        provider_chain=[(FakeProvider(), "fake-model")],
        env={},
    )

    assert len(ideas) == 2
    expected_keys = {
        "label",
        "cohort",
        "pain_hypothesis",
        "search_queries",
        "kill_condition",
        "gate_profile",
        "gate_profile_source",
        "evidence_ids",
        "origin",
        "anchor_slug",
        "incumbent",
        "parent_idea_id",
    }
    assert all(set(idea.keys()) == expected_keys for idea in ideas)
    assert all(isinstance(idea["search_queries"], list) for idea in ideas)
    assert all(isinstance(idea["evidence_ids"], list) and idea["evidence_ids"] for idea in ideas)
    assert all(idea["origin"] == "generator" for idea in ideas)
    assert all(isinstance(idea["kill_condition"], dict) for idea in ideas)


def test_generate_ideas_from_pursue_returns_adjacent_hypotheses():
    class FakeProvider:
        def generate_json(self, prompt: str, model: str):  # noqa: ARG002
            return {
                "ideas": [
                    {
                        "label": "guided bible plans for grief recovery",
                        "cohort": "grief support groups",
                        "pain_hypothesis": "General plans do not address grief-specific emotional triggers.",
                        "search_queries": [
                            "grief support bible app missing",
                            "christian grief recovery study app",
                        ],
                    }
                ]
            }

    ideas = generate_ideas_from_pursue(
        [{"label": "trauma-aware bible plans", "anchor_slug": "bible-study-apps", "next_test": "Run LP test"}],
        count=1,
        provider_chain=[(FakeProvider(), "fake-model")],
        env={},
    )

    assert len(ideas) == 1
    assert ideas[0]["cohort"] == "grief support groups"
    assert ideas[0]["origin"] == "reentry"


def test_generate_ideas_retries_once_on_invalid_shape():
    calls = {"count": 0}

    class FlakyProvider:
        def generate_json(self, prompt: str, model: str):  # noqa: ARG002
            calls["count"] += 1
            if calls["count"] == 1:
                return {"ideas": [{"label": "incomplete"}]}
            return {
                "ideas": [
                    {
                        "label": "niche idea",
                        "cohort": "specific cohort",
                        "pain_hypothesis": "A focused pain statement.",
                        "search_queries": ["query one", "query two"],
                    }
                ]
            }

    ideas = generate_ideas_from_anchor(
        _anchor(),
        count=1,
        provider_chain=[(FlakyProvider(), "fake-model")],
        env={},
    )

    assert calls["count"] == 2
    assert ideas[0]["label"] == "niche idea"


def test_generate_ideas_raises_when_chain_exhausted():
    class BadProvider:
        def generate_json(self, prompt: str, model: str):  # noqa: ARG002
            return {"invalid": "shape"}

    try:
        generate_ideas_from_anchor(_anchor(), count=1, provider_chain=[(BadProvider(), "bad-model")], env={})
    except GeneratorError:
        pass
    else:
        raise AssertionError("expected GeneratorError when provider chain is exhausted")
