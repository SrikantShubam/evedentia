"""Evidence-based gating: gates must judge real evidence text, not the idea's
own self-description, and provenance must not launder snippets/LLM output into
first-person voices. Written after the 2026-07-19 live proof (see
docs/LIVE_PROOF_FINDINGS.md) in which 9/9 ideas across 3 markets were killed
by a bridge<->gate vocabulary mismatch."""

from evidentia.models import Idea, KillCondition, PlayerProfile
from evidentia.tournament.gates import evaluate_gate
from evidentia.tournament.settings import FIRST_PERSON_PROVENANCES


def _player() -> PlayerProfile:
    return PlayerProfile(
        id="solo",
        team="solo",
        skills=["python"],
        budget_validate_usd=200,
        budget_build_usd=2000,
        budget_reach_usd=300,
        weeks_to_ship=6,
        risk="med",
    )


def _idea(**overrides) -> Idea:
    base = dict(
        id="idea-ev",
        label="Multiple users report PRICING issues with existing Headspace apps",
        anchor_slug="meditation apps",
        incumbent=None,
        cohort="identified from research",
        pain_hypothesis="Multiple users report PRICING issues with existing Headspace apps",
        kill_condition=KillCondition(description="no first-person pain", gate_name="three_first_person_voices"),
        evidence_ids=["e1", "e2", "e3"],
        search_queries=["meditation app pricing complaints"],
        origin="research_bridge",
        gate_profile="consumer_app",
        gate_profile_source="explicit",
        evidence_provenance={"e1": "verified", "e2": "verified", "e3": "verified"},
        evidence_texts={
            "e1": "Was charged $60 anyways when I cancelled the trial.",
            "e2": "I would happily pay monthly for a version without the upsells.",
            "e3": "The subscription price doubled and support ignored my refund request.",
        },
    )
    base.update(overrides)
    return Idea(**base)


# --- Provenance allowlist: no laundering ---------------------------------

def test_first_person_provenances_exclude_snippets_and_llm_output():
    assert "cited_evidence" not in FIRST_PERSON_PROVENANCES
    assert "llm_inference" not in FIRST_PERSON_PROVENANCES
    assert "llm_educated_guess" not in FIRST_PERSON_PROVENANCES
    assert "verified" in FIRST_PERSON_PROVENANCES


def test_three_first_person_voices_rejects_cited_evidence():
    idea = _idea(evidence_provenance={"e1": "cited_evidence", "e2": "cited_evidence", "e3": "cited_evidence"})
    result = evaluate_gate("three_first_person_voices", idea, _player())
    assert result.passed is False


# --- Spend-signal gates read evidence text -------------------------------

def test_willingness_to_pay_passes_on_evidence_quotes_not_label():
    # Label deliberately contains no spend keywords under \b matching
    idea = _idea(label="Ad-free focus companion", pain_hypothesis="Users abandon incumbents over trust")
    result = evaluate_gate("willingness_to_pay", idea, _player())
    assert result.passed is True


def test_willingness_to_pay_recognizes_real_billing_vocabulary():
    # "charged" / "refund" are how real users talk about money
    idea = _idea(
        label="Ad-free focus companion",
        pain_hypothesis="Users abandon incumbents over trust",
        evidence_texts={"e1": "They charged me twice and refused a refund.", "e2": "x", "e3": "y"},
    )
    result = evaluate_gate("budget_owner_identifiable", idea, _player())
    assert result.passed is True


def test_spend_gate_fails_when_neither_idea_nor_evidence_has_signal():
    idea = _idea(
        label="Ad-free focus companion",
        pain_hypothesis="Users abandon incumbents over trust",
        search_queries=["meditation app complaints"],
        evidence_texts={"e1": "The colors are ugly.", "e2": "Crashes on launch.", "e3": "Font too small."},
    )
    result = evaluate_gate("willingness_to_pay", idea, _player())
    assert result.passed is False


def test_retention_gate_reads_evidence_text():
    idea = _idea(
        label="Ad-free focus companion",
        pain_hypothesis="Users abandon incumbents over trust",
        evidence_texts={"e1": "I cancel and resubscribe monthly depending on content.", "e2": "x", "e3": "y"},
    )
    result = evaluate_gate("retention_plausible", idea, _player())
    assert result.passed is True


def test_negative_gates_ignore_evidence_text():
    # A review complaining about "the market leader" must not fail the
    # niche_not_already_owned structural check for the *idea*.
    idea = _idea(
        evidence_texts={"e1": "Calm is the market leader and it is already solved.", "e2": "x", "e3": "y"},
    )
    result = evaluate_gate("niche_not_already_owned", idea, _player())
    assert result.passed is True
