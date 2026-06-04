from evidentia.models import Idea, KillCondition, PlayerProfile, TerminalVerdict
from evidentia.tournament.engine import run_tournament
from evidentia.tournament.verdict import SHORTLIST_CONFIDENCE_THRESHOLD


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


def _idea(
    idea_id: str,
    *,
    label: str = "Onboarding assistant for agencies",
    cohort: str = "small agencies with junior onboarding staff",
    pain: str = "Teams are willing to pay monthly for faster onboarding and fewer errors with repeat retention.",
    profile: str = "consumer_app",
    queries: list[str] | None = None,
) -> Idea:
    return Idea(
        id=idea_id,
        label=label,
        anchor_slug="onboarding-tools",
        incumbent="IncumbentX",
        cohort=cohort,
        pain_hypothesis=pain,
        kill_condition=KillCondition(description="No market", gate_name="parent_market_exists"),
        evidence_ids=["sig-1", "sig-2", "sig-3", "sig-4"],
        evidence_provenance={"sig-1": "verified", "sig-2": "verified", "sig-3": "verified", "sig-4": "verified"},
        search_queries=queries or ["agency onboarding complaints", "agency onboarding budget"],
        origin="manual",
        gate_profile=profile,
        gate_profile_source="explicit",
    )


def test_acceptance_strong_evidence_has_terminal_viable_winner():
    result = run_tournament(
        ideas=[_idea("i-1"), _idea("i-2")],
        player=_player(),
        tournament_id="t-acc-strong",
        gate_profile="consumer_app",
    )
    viable = [state for state in result.ideas if state.terminal_verdict in {TerminalVerdict.PURSUE_SPIKE, TerminalVerdict.SHORTLIST}]
    assert viable
    winner = max(viable, key=lambda state: state.confidence_score_so_far)
    if winner.terminal_verdict == TerminalVerdict.PURSUE_SPIKE:
        assert winner.confidence_score_so_far >= SHORTLIST_CONFIDENCE_THRESHOLD


def test_acceptance_happy_incumbent_zero_winner_diagnosis_mentions_niche_gate():
    result = run_tournament(
        ideas=[
            _idea(
                "i-kill-1",
                pain="dominant incumbent already solved this and market leader controls it",
                label="Dominant incumbent market leader",
            ),
            _idea(
                "i-kill-2",
                pain="already solved by dominant incumbent and market leader",
                label="Already solved segment",
            ),
        ],
        player=_player(),
        tournament_id="t-acc-kill",
        gate_profile="consumer_app",
    )
    assert all(state.terminal_verdict == TerminalVerdict.KILL for state in result.ideas)
    assert result.memo is not None
    assert result.memo.zero_winner_diagnosis is not None
    assert "niche_not_already_owned" in result.memo.zero_winner_diagnosis


def test_acceptance_no_spend_zero_winner_diagnosis_mentions_wtp():
    result = run_tournament(
        ideas=[
                _idea(
                    "i-nospend-1",
                    pain="Teams repeat this workflow weekly with retention pressure and switching friction.",
                    queries=["agency onboarding friction", "agency onboarding retention pain"],
                ),
                _idea(
                    "i-nospend-2",
                    pain="Repeated retention pain with workflow friction and no billing ownership.",
                    queries=["onboarding friction examples", "retention workflow blockers"],
                ),
        ],
        player=_player(),
        tournament_id="t-acc-nospend",
        gate_profile="consumer_app",
    )
    assert all(state.terminal_verdict == TerminalVerdict.INSUFFICIENT_EVIDENCE for state in result.ideas)
    assert result.memo is not None
    assert result.memo.zero_winner_diagnosis is not None
    assert "willingness_to_pay" in result.memo.zero_winner_diagnosis


def test_acceptance_budget_exhausted_unrankable_has_no_winner():
    result = run_tournament(
        ideas=[_idea("i-budget-1")],
        player=_player(max_llm_calls=1),
        tournament_id="t-acc-budget",
        gate_profile="consumer_app",
    )
    assert result.is_rankable is False
    assert result.memo is not None
    assert result.memo.winner is None


def test_acceptance_profile_routing_uses_b2b_gates():
    result = run_tournament(
        ideas=[_idea("i-b2b-1", profile="b2b_workflow")],
        player=_player(),
        tournament_id="t-acc-b2b",
        gate_profile="b2b_workflow",
    )
    gate_names = {gate.gate_name for gate in result.ideas[0].gate_results}
    assert "budget_owner_identifiable" in gate_names
    assert "complaint_signal_exists" not in gate_names
