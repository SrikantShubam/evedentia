from evidentia.models import Idea, KillCondition, PlayerProfile, TerminalVerdict
from evidentia.tournament.engine import run_tournament


def _player(max_llm_calls: int = 200) -> PlayerProfile:
    return PlayerProfile(
        id="agency-1",
        team="Edge Agency",
        skills=["python", "sales"],
        budget_validate_usd=3000,
        budget_build_usd=15000,
        budget_reach_usd=2000,
        weeks_to_ship=8,
        risk="med",
        max_llm_calls_per_tournament=max_llm_calls,
    )


def _idea(idea_id: str, profile: str = "consumer_app") -> Idea:
    return Idea(
        id=idea_id,
        label="Onboarding assistant for agencies",
        anchor_slug="onboarding-tools",
        incumbent="IncumbentX",
        cohort="small agencies with junior onboarding staff",
        pain_hypothesis="Teams are willing to pay monthly for faster onboarding and fewer errors.",
        kill_condition=KillCondition(description="No market", gate_name="parent_market_exists"),
        evidence_ids=["sig-1", "sig-2", "sig-3", "sig-4"],
        search_queries=["agency onboarding complaints", "agency onboarding budget"],
        origin="manual",
        gate_profile=profile,
        gate_profile_source="explicit",
    )


def test_tournament_engine_returns_rankable_winner_for_strong_fixture():
    result = run_tournament(
        ideas=[_idea("idea-1"), _idea("idea-2")],
        player=_player(),
        tournament_id="t-strong",
        gate_profile="consumer_app",
    )
    assert result.is_rankable is True
    winners = [state for state in result.ideas if state.terminal_verdict in {TerminalVerdict.PURSUE_SPIKE, TerminalVerdict.SHORTLIST}]
    assert winners


def test_tournament_engine_marks_unrankable_when_budget_skips_required_gates():
    result = run_tournament(
        ideas=[_idea("idea-1")],
        player=_player(max_llm_calls=1),
        tournament_id="t-budget",
        gate_profile="consumer_app",
    )
    assert result.is_rankable is False
    assert all(state.terminal_verdict == TerminalVerdict.INSUFFICIENT_EVIDENCE for state in result.ideas)
    assert result.memo is not None
    assert result.memo.winner is None
