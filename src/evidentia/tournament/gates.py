from __future__ import annotations

import re
from dataclasses import dataclass

from evidentia.models import Idea, PlayerProfile
from evidentia.tournament.settings import FIRST_PERSON_PROVENANCES, gate_confidence_base


@dataclass
class GateEvaluation:
    passed: bool
    confidence: float
    evidence_ids: list[str]
    rationale: str


_WORD_BOUNDARY_CACHE: dict[str, re.Pattern] = {}


def _contains_any(text: str, needles: list[str]) -> bool:
    """Return True if *any* needle appears as a whole word in *text*.

    Uses word-boundary matching (``\\b``) so that ``"pay"`` matches
    ``"will pay"`` but not ``"payment"``.
    """
    if not needles:
        return False
    lowered = text.lower()
    key = "|".join(needles)
    if key not in _WORD_BOUNDARY_CACHE:
        pattern = r"\b(?:" + "|".join(re.escape(n) for n in needles) + r")\b"
        _WORD_BOUNDARY_CACHE[key] = re.compile(pattern)
    return bool(_WORD_BOUNDARY_CACHE[key].search(lowered))


def _idea_blob(idea: Idea) -> str:
    return " ".join(
        [
            idea.label,
            idea.cohort,
            idea.pain_hypothesis,
            " ".join(idea.search_queries),
        ]
    ).lower()


def evaluate_gate(gate_name: str, idea: Idea, player: PlayerProfile) -> GateEvaluation:
    text_blob = _idea_blob(idea)
    evidence_count = len(idea.evidence_ids)

    if gate_name == "parent_market_exists":
        passed = bool(idea.anchor_slug or idea.incumbent)
        return GateEvaluation(
            passed=passed,
            confidence=gate_confidence_base(gate_name, passed),
            evidence_ids=idea.evidence_ids[:1],
            rationale="anchor_or_incumbent",
        )
    if gate_name == "niche_not_already_owned":
        passed = not _contains_any(text_blob, ["market leader", "dominant incumbent", "already solved"])
        return GateEvaluation(
            passed=passed,
            confidence=gate_confidence_base(gate_name, passed),
            evidence_ids=idea.evidence_ids[:1],
            rationale="niche_competition_check",
        )
    if gate_name in {"complaint_signal_exists", "repeat_purchase_evidence", "procurement_path_exists"}:
        passed = evidence_count >= 1
        return GateEvaluation(
            passed=passed,
            confidence=gate_confidence_base(gate_name, passed),
            evidence_ids=idea.evidence_ids[:1],
            rationale="evidence_presence",
        )
    if gate_name == "three_first_person_voices":
        # Count any evidence whose provenance is in the allowlist
        matched_ids = [
            eid for eid in idea.evidence_ids
            if idea.evidence_provenance.get(eid) in FIRST_PERSON_PROVENANCES
        ]
        if len(matched_ids) >= 3:
            return GateEvaluation(
                passed=True,
                confidence=gate_confidence_base(gate_name, True),
                evidence_ids=matched_ids[:3],
                rationale="voice_count",
            )
        return GateEvaluation(
            passed=False,
            confidence=gate_confidence_base(gate_name, False),
            evidence_ids=matched_ids,
            rationale="synthetic_only",
        )
    if gate_name in {"reachable_channel", "pricing_anchor_exists"}:
        passed = len(idea.search_queries) >= 1
        return GateEvaluation(
            passed=passed,
            confidence=gate_confidence_base(gate_name, passed),
            evidence_ids=idea.evidence_ids[:1],
            rationale="query_presence",
        )
    if gate_name in {"retention_plausible", "switching_cost_defensible", "referral_dynamics"}:
        passed = _contains_any(text_blob, ["repeat", "monthly", "recurring", "switch", "referral", "retention"])
        return GateEvaluation(
            passed=passed,
            confidence=gate_confidence_base(gate_name, passed),
            evidence_ids=idea.evidence_ids[:2],
            rationale="retention_or_switching_signal",
        )
    if gate_name in {"budget_owner_identifiable", "monetization_path_plausible", "willingness_to_pay"}:
        passed = _contains_any(text_blob, ["pay", "price", "budget", "subscription", "invoice"])
        return GateEvaluation(
            passed=passed,
            confidence=gate_confidence_base(gate_name, passed),
            evidence_ids=idea.evidence_ids[:2],
            rationale="spend_signal",
        )
    if gate_name == "store_category_not_saturated":
        passed = not _contains_any(text_blob, ["saturated", "crowded", "commodity"])
        return GateEvaluation(
            passed=passed,
            confidence=gate_confidence_base(gate_name, passed),
            evidence_ids=idea.evidence_ids[:1],
            rationale="saturation_check",
        )
    if gate_name == "player_fit":
        passed = player.weeks_to_ship <= 12 and player.budget_build_usd >= 1000
        return GateEvaluation(
            passed=passed,
            confidence=gate_confidence_base(gate_name, passed),
            evidence_ids=idea.evidence_ids[:1],
            rationale="timeline_and_budget_fit",
        )

    return GateEvaluation(
        passed=False,
        confidence=gate_confidence_base(gate_name, False),
        evidence_ids=[],
        rationale="unknown_gate",
    )
