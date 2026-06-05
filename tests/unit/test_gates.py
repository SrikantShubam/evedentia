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


def test_contains_any_word_boundary_does_not_match_substring():
    """Word-boundary matching: 'pay' must not match 'payment'."""
    from evidentia.tournament.gates import _contains_any

    assert _contains_any("we will pay monthly", ["pay", "price"]) is True
    assert _contains_any("payment processing", ["pay", "price"]) is False
    assert _contains_any("priceless artifact", ["pay", "price"]) is False
    assert _contains_any("budget is tight", ["pay", "price", "budget"]) is True


def test_three_first_person_voices_accepts_cited_evidence():
    """cited_evidence (from web search) should count as first-person voice."""
    idea = Idea(
        id="idea-cite",
        label="Tool",
        anchor_slug="a",
        incumbent=None,
        cohort="users",
        pain_hypothesis="Painful workflow.",
        kill_condition=KillCondition(description="few voices", gate_name="three_first_person_voices"),
        evidence_ids=["e1", "e2", "e3"],
        evidence_provenance={"e1": "cited_evidence", "e2": "cited_evidence", "e3": "cited_evidence"},
        search_queries=["workflow pain"],
        origin="manual",
        gate_profile="consumer_app",
        gate_profile_source="explicit",
    )
    result = evaluate_gate("three_first_person_voices", idea, _player())
    assert result.passed is True


def test_three_first_person_voices_rejects_synthetic():
    """Synthetic evidence (no matching provenance) should not count."""
    idea = Idea(
        id="idea-syn",
        label="Tool",
        anchor_slug="a",
        incumbent=None,
        cohort="users",
        pain_hypothesis="Painful workflow.",
        kill_condition=KillCondition(description="few voices", gate_name="three_first_person_voices"),
        evidence_ids=["e1", "e2", "e3"],
        evidence_provenance={"e1": "synthetic", "e2": "synthetic", "e3": "synthetic"},
        search_queries=["workflow pain"],
        origin="manual",
        gate_profile="consumer_app",
        gate_profile_source="explicit",
    )
    result = evaluate_gate("three_first_person_voices", idea, _player())
    assert result.passed is False


def test_gate_confidence_reads_from_settings():
    """Gate confidence should come from GATE_CONFIDENCE_CONFIG, not hardcoded."""
    from evidentia.tournament.settings import gate_confidence_base

    idea = Idea(
        id="idea-conf",
        label="Test",
        anchor_slug="a",
        incumbent="Inc",
        cohort="users",
        pain_hypothesis="Test.",
        kill_condition=KillCondition(description="x", gate_name="parent_market_exists"),
        evidence_ids=["e1"],
        search_queries=["q"],
        origin="manual",
        gate_profile="consumer_app",
        gate_profile_source="explicit",
    )
    result = evaluate_gate("parent_market_exists", idea, _player())
    expected = gate_confidence_base("parent_market_exists", passed=True)
    assert result.confidence == expected
