"""Round-trip test: generator output shape is compatible with Idea(**row).

HANDFOR_REVIEW.md Q3: Generator outputs plain dicts; validator expects Idea(**row).
This test proves shape compatibility without requiring live LLM calls.

For the full end-to-end test (generate → validate with real LLM), see the
live-marked test in tests/live/.
"""

import json

from evidentia.models import Idea


def test_generated_dict_shape_validates_as_idea():
    """A dict matching the generator's output shape must construct via Idea(**row)."""
    sample_generator_output = {
        "id": "gen-test-1",
        "label": "AI onboarding wizard for small agencies",
        "anchor_slug": "onboarding-tools",
        "incumbent": "IncumbentX",
        "cohort": "small agencies with junior onboarding staff",
        "pain_hypothesis": "Teams are willing to pay monthly for faster onboarding.",
        "kill_condition": {
            "description": "Fail if parent_market_exists does not pass.",
            "gate_name": "parent_market_exists",
        },
        "gate_profile": "consumer_app",
        "gate_profile_source": "inferred:0.75",
        "evidence_ids": ["seed-ai-onboarding-wizard-for-small-agencies"],
        "search_queries": [
            "agency onboarding tools pain points",
            "agency onboarding budget software",
        ],
        "origin": "generator",
        "parent_idea_id": None,
        "evidence_provenance": {},
    }

    idea = Idea(**sample_generator_output)
    assert idea.id == "gen-test-1"
    assert idea.label == "AI onboarding wizard for small agencies"
    assert isinstance(idea.kill_condition, dict)
    assert idea.kill_condition["gate_name"] == "parent_market_exists"
    assert idea.gate_profile == "consumer_app"


def test_generated_dict_minimal_fields():
    """A minimal generator dict without optional fields should also construct."""
    minimal = {
        "id": "min-test-1",
        "label": "Minimal idea",
        "cohort": "anyone",
        "pain_hypothesis": "There is pain.",
        "origin": "generator",
        "gate_profile": "consumer_app",
        "gate_profile_source": "explicit",
        "kill_condition": {"description": "test", "gate_name": "parent_market_exists"},
        "evidence_ids": ["sig-1"],
        "search_queries": ["test query"],
        "anchor_slug": None,
        "incumbent": None,
    }

    idea = Idea(**minimal)
    assert idea.id == "min-test-1"
    assert idea.evidence_provenance == {}  # default


def test_generated_dict_rejects_missing_required():
    """Generator output with missing required fields should raise ValueError."""
    import pytest

    bad = {
        "id": "bad-1",
        # missing: label, cohort, pain_hypothesis, origin, gate_profile, gate_profile_source
        "kill_condition": {"description": "x", "gate_name": "x"},
        "evidence_ids": [],
        "search_queries": [],
    }
    with pytest.raises(TypeError):
        Idea(**bad)
