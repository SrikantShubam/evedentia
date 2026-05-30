from __future__ import annotations

from datetime import datetime, timezone

from evidentia.models import (
    GateResult,
    GateStatus,
    Idea,
    IdeaState,
    PlayerProfile,
    RoundOutcome,
    TerminalVerdict,
    TournamentResult,
)
from evidentia.tournament.confidence import confidence_product, is_rankable as is_idea_rankable
from evidentia.tournament.gates import evaluate_gate
from evidentia.tournament.memo import build_decision_memo
from evidentia.tournament.profiles import COST_FREE, COST_LLM_PAID_SEARCH, PROFILES, required_gates
from evidentia.tournament.verdict import derive_terminal_verdict


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _cost_for_gate(profile_name: str, gate_name: str) -> str:
    for spec in PROFILES[profile_name]:
        if spec.gate_name == gate_name:
            return spec.cost_tier
    raise ValueError(f"gate '{gate_name}' not registered in profile '{profile_name}'")


def run_tournament(
    *,
    ideas: list[Idea],
    player: PlayerProfile,
    tournament_id: str,
    gate_profile: str | None = None,
    parent_tournament_id: str | None = None,
    reentry_depth: int = 0,
) -> TournamentResult:
    llm_calls_used = 0
    paid_queries_used = 0
    total_llm_cost_usd = 0.0
    states: list[IdeaState] = []
    started_at = _utc_now()

    for idea in ideas:
        profile_name = gate_profile or idea.gate_profile
        results: list[GateResult] = []
        stop_early = False
        for gate_name in required_gates(profile_name):
            if stop_early:
                results.append(
                    GateResult(
                        gate_name=gate_name,
                        status=GateStatus.SKIPPED,
                        outcome=None,
                        evidence_ids=[],
                        confidence=None,
                        killed_by="prior_gate_failure",
                        llm_cost_usd=0.0,
                        error=None,
                    )
                )
                continue

            cost_tier = _cost_for_gate(profile_name, gate_name)
            needs_llm = cost_tier != COST_FREE
            needs_paid_query = cost_tier == COST_LLM_PAID_SEARCH
            if needs_llm and llm_calls_used + 1 > player.max_llm_calls_per_tournament:
                results.append(
                    GateResult(
                        gate_name=gate_name,
                        status=GateStatus.SKIPPED,
                        outcome=None,
                        evidence_ids=[],
                        confidence=None,
                        killed_by="budget_exhausted_llm_calls",
                        llm_cost_usd=0.0,
                        error=None,
                    )
                )
                stop_early = True
                continue
            if needs_paid_query and paid_queries_used + 1 > player.max_paid_queries_per_tournament:
                results.append(
                    GateResult(
                        gate_name=gate_name,
                        status=GateStatus.SKIPPED,
                        outcome=None,
                        evidence_ids=[],
                        confidence=None,
                        killed_by="budget_exhausted_paid_queries",
                        llm_cost_usd=0.0,
                        error=None,
                    )
                )
                stop_early = True
                continue

            eval_result = evaluate_gate(gate_name, idea, player)
            if needs_llm:
                llm_calls_used += 1
                total_llm_cost_usd += 0.02
            if needs_paid_query:
                paid_queries_used += 1
                total_llm_cost_usd += 0.05

            results.append(
                GateResult(
                    gate_name=gate_name,
                    status=GateStatus.COMPLETED,
                    outcome=RoundOutcome.PASS if eval_result.passed else RoundOutcome.FAIL,
                    evidence_ids=eval_result.evidence_ids,
                    confidence=eval_result.confidence if eval_result.passed else None,
                    killed_by=gate_name if not eval_result.passed else None,
                    llm_cost_usd=0.07 if needs_paid_query else (0.02 if needs_llm else 0.0),
                    error=None,
                )
            )
            if not eval_result.passed:
                stop_early = True

        state = IdeaState(
            idea=idea,
            gate_results=results,
            confidence_score_so_far=1.0,
            is_complete=False,
            terminal_verdict=None,
        )
        state.confidence_score_so_far = confidence_product(state)
        state.is_complete = all(result.status == GateStatus.COMPLETED for result in results)
        state.terminal_verdict = derive_terminal_verdict(state)
        states.append(state)

    tournament_rankable = all(is_idea_rankable(state) for state in states) if states else False
    winner: IdeaState | None = None
    if tournament_rankable:
        winner_pool = [state for state in states if state.terminal_verdict in {TerminalVerdict.PURSUE_SPIKE, TerminalVerdict.SHORTLIST}]
        if winner_pool:
            winner = sorted(winner_pool, key=lambda item: item.confidence_score_so_far, reverse=True)[0]

    memo = build_decision_memo(
        tournament_id=tournament_id,
        player_id=player.id,
        states=states,
        winner=winner,
    )
    return TournamentResult(
        tournament_id=tournament_id,
        player_id=player.id,
        gate_profile=gate_profile or (ideas[0].gate_profile if ideas else "consumer_app"),
        started_at=started_at,
        finished_at=_utc_now(),
        ideas=states,
        memo=memo,
        total_llm_cost_usd=round(total_llm_cost_usd, 4),
        stopped_reason="completed",
        is_rankable=tournament_rankable,
        parent_tournament_id=parent_tournament_id,
        reentry_depth=reentry_depth,
    )
