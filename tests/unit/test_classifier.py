from evidentia.classifier import classify_candidate


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


def test_classify_candidate_uses_llm_output_for_gate_fields():
    candidate = {
        "title": "Invoice reminder automation",
        "source_text": "Teams say they would pay for this if it saved AR time.",
        "verbatim_quote": "would pay for this",
        "source_url": "https://news.ycombinator.com/item?id=1",
    }

    classified = classify_candidate(candidate, provider=StubProvider(), model="stub-model")

    assert classified["willingness_to_pay"] == "pass"
    assert classified["distribution_channel"] == "pass"
    assert classified["competition_gap"] == 0.8


class FailingProvider:
    name = "failing"

    def generate_json(self, prompt: str, model: str) -> dict:
        raise RuntimeError("timeout")


def test_classify_candidate_falls_back_to_next_provider():
    candidate = {
        "title": "Invoice reminder automation",
        "source_text": "Teams say they would pay for this if it saved AR time.",
        "verbatim_quote": "would pay for this",
        "source_url": "https://news.ycombinator.com/item?id=1",
    }

    classified = classify_candidate(
        candidate,
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
            "competition_gap": "High",
            "buildability": "Moderate",
            "reachability_strength": "Low",
        }


def test_classify_candidate_normalizes_llm_labels():
    candidate = {
        "title": "Invoice reminder automation",
        "source_text": "Teams say they would pay for this if it saved AR time.",
        "verbatim_quote": "would pay for this",
        "source_url": "https://news.ycombinator.com/item?id=1",
    }

    classified = classify_candidate(candidate, provider=MessyProvider(), model="messy-model")

    assert classified["willingness_to_pay"] == "pass"
    assert classified["distribution_channel"] == "pass"
    assert classified["data_feasibility"] == "pass"
    assert classified["competition_gap"] == 1.0
    assert classified["buildability"] == 0.6
    assert classified["reachability_strength"] == 0.2
