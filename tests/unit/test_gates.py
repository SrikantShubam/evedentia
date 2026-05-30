from evidentia.models import Idea, KillCondition, PlayerProfile
from evidentia.tournament.gates import evaluate_gate


def _player() -> PlayerProfile:
    return PlayerProfile(
        id="p1",
        team="Edge Agency",
        skills=["python", "sales"],
        budget_validate_usd=2000,
        budget_build_usd=12000,
        budget_reach_usd=1500,
        weeks_to_ship=8,
        risk="med",
    )


def test_complaint_signal_exists_gate_uses_evidence_ids():
    idea = Idea(
        id="idea-1",
        label="Agency ops simplifier",
        anchor_slug="agency-tools",
        incumbent=None,
        cohort="agencies",
        pain_hypothesis="Ops leads keep paying for broken workflows.",
        kill_condition=KillCondition(description="no complaints", gate_name="complaint_signal_exists"),
        evidence_ids=["sig-1", "sig-2"],
        search_queries=["agency workflow complaints"],
        origin="manual",
        gate_profile="consumer_app",
        gate_profile_source="explicit",
    )
    result = evaluate_gate("complaint_signal_exists", idea, _player())
    assert result.passed is True


def test_three_first_person_voices_requires_three_signals():
    idea = Idea(
        id="idea-2",
        label="Agency ops simplifier",
        anchor_slug="agency-tools",
        incumbent=None,
        cohort="agencies",
        pain_hypothesis="Ops leads keep paying for broken workflows.",
        kill_condition=KillCondition(description="few voices", gate_name="three_first_person_voices"),
        evidence_ids=["sig-1", "sig-2"],
        search_queries=["agency workflow complaints"],
        origin="manual",
        gate_profile="consumer_app",
        gate_profile_source="explicit",
    )
    result = evaluate_gate("three_first_person_voices", idea, _player())
    assert result.passed is False


def test_player_fit_gate_fails_when_timeline_too_short():
    player = PlayerProfile(
        id="p2",
        team="Tiny Team",
        skills=["python"],
        budget_validate_usd=200,
        budget_build_usd=200,
        budget_reach_usd=200,
        weeks_to_ship=1,
        risk="low",
    )
    idea = Idea(
        id="idea-3",
        label="B2B data checker",
        anchor_slug="b2b-tools",
        incumbent=None,
        cohort="ops managers",
        pain_hypothesis="Teams pay for this monthly if onboarding is simple.",
        kill_condition=KillCondition(description="no fit", gate_name="player_fit"),
        evidence_ids=["sig-1", "sig-2", "sig-3"],
        search_queries=["ops managers pain"],
        origin="manual",
        gate_profile="b2b_workflow",
        gate_profile_source="explicit",
    )
    result = evaluate_gate("player_fit", idea, player)
    assert result.passed is False
