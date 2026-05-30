import json

import pytest

from evidentia.classifier import ClassifierError, classify_candidate


class StubProvider:
    name = "stub"

    def generate_json(self, prompt: str, model: str) -> dict:
        return {
            "willingness_to_pay": "pass",
            "distribution_channel": "pass",
            "data_feasibility": "pass",
            "competition_gap": 0.8,
            "buildability": 0.6,
            "reachability_strength": 0.7,
        }


def _candidate() -> dict:
    return {
        "title": "Invoice reminder automation",
        "source_text": "Teams say they would pay for this if it saved AR time.",
        "verbatim_quote": "would pay for this",
        "source_url": "https://news.ycombinator.com/item?id=1",
    }


def test_classify_candidate_uses_llm_output_for_gate_fields():
    classified = classify_candidate(_candidate(), provider=StubProvider(), model="stub-model")
    assert classified["willingness_to_pay"] == "pass"
    assert classified["distribution_channel"] == "pass"
    assert classified["competition_gap"] == 0.8


class FailingProvider:
    name = "failing"

    def generate_json(self, prompt: str, model: str) -> dict:
        raise RuntimeError("timeout")


def test_classify_candidate_falls_back_to_next_provider():
    classified = classify_candidate(
        _candidate(),
        provider_chain=[(FailingProvider(), "fail-model"), (StubProvider(), "stub-model")],
    )
    assert classified["willingness_to_pay"] == "pass"


class MessyProvider:
    name = "messy"

    def generate_json(self, prompt: str, model: str) -> dict:
        return {
            "willingness_to_pay": "High",
            "distribution_channel": "Direct",
            "data_feasibility": "Moderate",
            "competition_gap": 0.9,
            "buildability": 0.6,
            "reachability_strength": 0.2,
        }


def test_classify_candidate_normalizes_llm_labels():
    classified = classify_candidate(_candidate(), provider=MessyProvider(), model="messy-model")
    assert classified["willingness_to_pay"] == "pass"
    assert classified["distribution_channel"] == "pass"
    assert classified["data_feasibility"] == "pass"
    assert classified["competition_gap"] == 0.9
    assert classified["buildability"] == 0.6
    assert classified["reachability_strength"] == 0.2


def test_classification_prompt_caps_source_text():
    from evidentia.classifier import _classification_prompt

    long_candidate = {
        "title": "test",
        "verbatim_quote": "quote",
        "source_text": "x" * 5000,
    }
    prompt = _classification_prompt(long_candidate)
    assert prompt.count("x") <= 1000


def test_tester_recruitment_forces_willingness_to_pay_fail():
    candidate = {
        "title": "Need 20 testers for Money Master",
        "source_text": "I will test back immediately for 14 days.",
        "verbatim_quote": "Need 20 testers, I will test back",
        "source_url": "https://www.reddit.com/r/TestersCommunity/comments/abc/",
    }
    classified = classify_candidate(candidate, provider=StubProvider(), model="stub-model")
    assert classified["willingness_to_pay"] == "fail"
    assert classified["distribution_channel"] == "pass"
    assert classified["data_feasibility"] == "pass"


@pytest.mark.parametrize(
    "label,expected",
    [
        ("strong", "pass"),
        ("confirmed", "pass"),
        ("explicit", "pass"),
        ("0.7", "pass"),
        ("0.3", "fail"),
        ("insufficient evidence", "fail"),
        ("n/a", "fail"),
        ("none", "fail"),
    ],
)
def test_normalize_gate_extended_labels(label, expected):
    from evidentia.classifier import _normalize_gate

    assert _normalize_gate(label) == expected


def test_classify_candidate_debug_log(tmp_path):
    log_path = tmp_path / "log.jsonl"
    classify_candidate(
        {"title": "x", "verbatim_quote": "y", "source_text": "z"},
        provider=StubProvider(),
        model="fake",
        debug_log_path=str(log_path),
    )
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert "raw_response" in entry and "normalized" in entry and "prompt" in entry


def test_validate_classification_shape():
    from evidentia.classifier import _validate_classification_shape

    assert _validate_classification_shape(
        {
            "willingness_to_pay": "pass",
            "distribution_channel": "pass",
            "data_feasibility": "pass",
            "competition_gap": 0.5,
            "buildability": 0.5,
            "reachability_strength": 0.5,
        }
    ) == []
    assert _validate_classification_shape({"willingness_to_pay": "yes"})


def test_classifier_retries_on_bad_shape():
    calls = {"n": 0}

    class FlakeyProvider:
        def generate_json(self, prompt, model):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"willingness_to_pay": "yes"}
            return {
                "willingness_to_pay": "pass",
                "distribution_channel": "pass",
                "data_feasibility": "pass",
                "competition_gap": 0.5,
                "buildability": 0.5,
                "reachability_strength": 0.5,
            }

    result = classify_candidate(
        {"title": "t", "verbatim_quote": "q", "source_text": "s"},
        provider=FlakeyProvider(),
        model="fake",
    )
    assert calls["n"] == 2
    assert result["willingness_to_pay"] == "pass"


def test_classifier_raises_after_retries_exhausted():
    class BadProvider:
        def generate_json(self, prompt, model):
            return {"nope": "bad"}

    with pytest.raises(ClassifierError):
        classify_candidate(
            {"title": "t", "verbatim_quote": "q", "source_text": "s"},
            provider_chain=[(BadProvider(), "m")],
        )
