from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha1


class RoundOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class GateStatus(str, Enum):
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class TerminalVerdict(str, Enum):
    KILL = "KILL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    SHORTLIST = "SHORTLIST"
    PURSUE_SPIKE = "PURSUE_SPIKE"


# Retired for backward compat (pre-Phase 0 Verdict + scoring transition).
# New code uses TerminalVerdict; legacy paths may reference Verdict as nullable/optional.
class Verdict(str, Enum):
    KILL = "KILL"
    REFINE = "REFINE"
    PURSUE = "PURSUE"


class ComplaintType(str, Enum):
    ADS = "ADS"
    BILLING_ABUSE = "BILLING_ABUSE"
    NICHE_EXCLUSION = "NICHE_EXCLUSION"
    TRUST_PRIVACY = "TRUST_PRIVACY"
    WORKFLOW_FRICTION = "WORKFLOW_FRICTION"
    FEATURE_BLOAT = "FEATURE_BLOAT"
    SUPPORT_FAILURE = "SUPPORT_FAILURE"
    LOCALIZATION = "LOCALIZATION"
    PLATFORM_LOCK_IN = "PLATFORM_LOCK_IN"
    MISSING_FEATURE = "MISSING_FEATURE"
    BROKEN_FEATURE = "BROKEN_FEATURE"
    PRICING = "PRICING"
    UX = "UX"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    UNKNOWN_WITH_REASON = "UNKNOWN_WITH_REASON"


@dataclass
class DemandSignal:
    signal_id: str
    source_url: str
    verbatim_quote: str
    timestamp: str
    title: str | None = None
    source_text: str | None = None
    source_kind: str = "unknown"
    signal_subtype: str = "unknown"
    author: str | None = None
    verified: bool = False
    proof_level: str = "none"
    complaint_type: str | None = None
    complaint_type_reason: str | None = None

    @staticmethod
    def build_signal_id(source_url: str, verbatim_quote: str) -> str:
        payload = f"{source_url}{verbatim_quote}".encode("utf-8")
        return sha1(payload).hexdigest()[:16]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Anchor:
    slug: str
    market_name: str
    incumbents: list[str]
    proof_of_market: DemandSignal
    cohort_hints: list[str] = field(default_factory=list)
    primary_channel_queries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Slice:
    slice_id: str
    anchor_slug: str
    label: str
    signal_ids: list[str]
    author_count: int
    dominant_subtype: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SliceVerdict:
    slice_id: str
    anchor_slug: str
    verdict: str
    gates: dict[str, bool]
    heuristics: dict[str, float]
    refine_reason: str | None
    next_test: str | None
    evidence_ids: list[str]
    schema_version: int = 1

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PlayerProfile:
    id: str
    team: str
    skills: list[str]
    budget_validate_usd: int
    budget_build_usd: int
    budget_reach_usd: int
    weeks_to_ship: int
    risk: str
    max_llm_calls_per_tournament: int = 200
    max_paid_queries_per_tournament: int = 50
    max_reentry_rounds: int = 1

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("PlayerProfile.id must be non-empty")
        if not self.team.strip():
            raise ValueError("PlayerProfile.team must be non-empty")
        if self.risk not in {"low", "med", "high"}:
            raise ValueError("PlayerProfile.risk must be one of: low, med, high")
        if self.weeks_to_ship <= 0:
            raise ValueError("PlayerProfile.weeks_to_ship must be positive")
        if self.budget_validate_usd < 0 or self.budget_build_usd < 0 or self.budget_reach_usd < 0:
            raise ValueError("PlayerProfile budgets must be non-negative")
        if self.max_llm_calls_per_tournament <= 0:
            raise ValueError("PlayerProfile.max_llm_calls_per_tournament must be positive")
        if self.max_paid_queries_per_tournament <= 0:
            raise ValueError("PlayerProfile.max_paid_queries_per_tournament must be positive")
        if self.max_reentry_rounds < 0 or self.max_reentry_rounds > 3:
            raise ValueError("PlayerProfile.max_reentry_rounds must be in [0, 3]")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class KillCondition:
    description: str
    gate_name: str

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("KillCondition.description must be non-empty")
        if not self.gate_name.strip():
            raise ValueError("KillCondition.gate_name must be non-empty")

    def to_dict(self) -> dict:
        return asdict(self)


class Provenance(Enum):
    SYNTHETIC = "synthetic"
    SEED = "seed"
    REENTRY = "reentry"
    VERIFIED = "verified"
    CITED_EVIDENCE = "cited_evidence"
    LLM_INFERENCE = "llm_inference"
    LLM_EDUCATED_GUESS = "llm_educated_guess"
    UNKNOWN = "unknown"


@dataclass
class QualifiedEvidence:
    evidence_id: str
    provenance: Provenance
    verified: bool
    first_person: bool
    voice_key: str | None
    ineligibility_reason: str | None = None


@dataclass
class Idea:
    id: str
    label: str
    anchor_slug: str | None
    incumbent: str | None
    cohort: str
    pain_hypothesis: str
    kill_condition: KillCondition
    evidence_ids: list[str]
    search_queries: list[str]
    origin: str
    gate_profile: str
    gate_profile_source: str
    parent_idea_id: str | None = None
    evidence_provenance: dict[str, str] = field(default_factory=dict)
    # evidence_id -> verbatim quote; lets gates judge real user language
    # instead of the idea's own self-description.
    evidence_texts: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Idea.id must be non-empty")
        if not self.label.strip():
            raise ValueError("Idea.label must be non-empty")
        if not self.cohort.strip():
            raise ValueError("Idea.cohort must be non-empty")
        if not self.pain_hypothesis.strip():
            raise ValueError("Idea.pain_hypothesis must be non-empty")
        if not self.origin.strip():
            raise ValueError("Idea.origin must be non-empty")
        if not self.gate_profile.strip():
            raise ValueError("Idea.gate_profile must be non-empty")
        if not self.gate_profile_source.strip():
            raise ValueError("Idea.gate_profile_source must be non-empty")
        if not self.evidence_ids:
            raise ValueError("Idea.evidence_ids must be non-empty")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GateResult:
    gate_name: str
    status: GateStatus
    outcome: RoundOutcome | None
    evidence_ids: list[str]
    confidence: float | None
    killed_by: str | None
    llm_cost_usd: float
    error: str | None

    def __post_init__(self) -> None:
        if not self.gate_name.strip():
            raise ValueError("GateResult.gate_name must be non-empty")
        if self.confidence is not None and (self.confidence < 0.5 or self.confidence > 0.95):
            raise ValueError("GateResult.confidence must be within [0.5, 0.95]")
        if self.llm_cost_usd < 0:
            raise ValueError("GateResult.llm_cost_usd must be non-negative")
        if self.status != GateStatus.COMPLETED and self.outcome is not None:
            raise ValueError("GateResult.outcome must be None when status is not COMPLETED")
        if self.status == GateStatus.COMPLETED and self.outcome is None:
            raise ValueError("GateResult.outcome must be set when status is COMPLETED")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class IdeaState:
    idea: Idea
    gate_results: list[GateResult]
    confidence_score_so_far: float
    is_complete: bool
    terminal_verdict: TerminalVerdict | None

    def __post_init__(self) -> None:
        if self.confidence_score_so_far < 0:
            raise ValueError("IdeaState.confidence_score_so_far must be non-negative")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["idea"] = self.idea.to_dict()
        d["id"] = d["idea"]["id"]
        d["label"] = d["idea"]["label"]
        return d


@dataclass
class RealitySpike:
    idea_id: str
    target_customer_profile: str
    outreach_message: str
    landing_page_headline: str
    landing_page_subhead: str
    interview_questions: list[str]
    success_criteria: str
    fail_criteria: str
    weeks_to_run: int
    provenance: str = "LLM_GENERATED_TACTICAL_COPY"

    def __post_init__(self) -> None:
        if not self.idea_id.strip():
            raise ValueError("RealitySpike.idea_id must be non-empty")
        if len(self.interview_questions) != 5:
            raise ValueError("RealitySpike.interview_questions must contain exactly 5 questions")
        if self.weeks_to_run <= 0:
            raise ValueError("RealitySpike.weeks_to_run must be positive")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DecisionMemo:
    tournament_id: str
    player_id: str
    winner: IdeaState | None
    shortlist: list[IdeaState]
    insufficient_evidence: list[IdeaState]
    killed: list[IdeaState]
    why_winner_beat_alternatives: str
    strongest_argument_for: str
    strongest_argument_against: str
    missing_evidence_checklist: list[str]
    reality_spike: RealitySpike | None
    zero_winner_diagnosis: str | None
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.tournament_id.strip():
            raise ValueError("DecisionMemo.tournament_id must be non-empty")
        if not self.player_id.strip():
            raise ValueError("DecisionMemo.player_id must be non-empty")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["winner"] = self.winner.to_dict() if self.winner else None
        d["shortlist"] = [s.to_dict() for s in self.shortlist]
        d["insufficient_evidence"] = [s.to_dict() for s in self.insufficient_evidence]
        d["killed"] = [s.to_dict() for s in self.killed]
        return d


@dataclass
class TournamentResult:
    tournament_id: str
    player_id: str
    gate_profile: str
    started_at: str
    finished_at: str | None
    ideas: list[IdeaState]
    memo: DecisionMemo | None
    total_llm_cost_usd: float
    stopped_reason: str
    is_rankable: bool
    parent_tournament_id: str | None
    reentry_depth: int
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.tournament_id.strip():
            raise ValueError("TournamentResult.tournament_id must be non-empty")
        if not self.player_id.strip():
            raise ValueError("TournamentResult.player_id must be non-empty")
        if not self.gate_profile.strip():
            raise ValueError("TournamentResult.gate_profile must be non-empty")
        if self.total_llm_cost_usd < 0:
            raise ValueError("TournamentResult.total_llm_cost_usd must be non-negative")
        if self.reentry_depth < 0:
            raise ValueError("TournamentResult.reentry_depth must be non-negative")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ideas"] = [s.to_dict() for s in self.ideas]
        d["memo"] = self.memo.to_dict() if self.memo else None
        return d


@dataclass
class Review:
    """A single user review from any source (App Store, Reddit, GitHub)."""
    text: str
    rating: int
    source: str  # "app_store" | "reddit" | "github" | "search"
    version: str | None = None
    date: str | None = None
    country: str | None = None
    authenticity: str = "AUTHENTIC"  # AUTHENTIC | SUSPICIOUS | UNKNOWN


@dataclass
class ClassifiedComplaint:
    """A complaint extracted from a review, with type and severity."""
    review_text: str
    complaint_type: str  # BUG | UX | PRICING | MISSING_FEATURE | SUPPORT | PERFORMANCE | CONTENT_QUALITY | OTHER
    severity: int  # 1-10
    confidence: float  # 0.0-1.0


@dataclass
class BarrierHypothesis:
    """LLM-generated hypothesis about why a market gap hasn't been filled."""
    description: str
    barrier_type: str  # regulation | economics | network_effects | technical | market_size | other
    confidence: float
    provenance: str = "LLM_EDUCATED_GUESS"


@dataclass
class OpportunityGap:
    """A specific market opportunity identified from complaint analysis."""
    gap_description: str
    evidence_count: int
    severity: str  # HIGH | MEDIUM | LOW
    exploitability: str  # HIGH | MEDIUM | LOW


@dataclass
class ResearchReport:
    """Complete research report for a market query."""
    query: str
    competitors_analyzed: list[str]
    total_reviews: int
    complaints: list[ClassifiedComplaint]
    barrier_hypotheses: list[BarrierHypothesis]
    top_opportunities: list[OpportunityGap]
    provenance_summary: str
    evidence_data: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "competitors_analyzed": self.competitors_analyzed,
            "total_reviews": self.total_reviews,
            "complaints": [{"review_text": c.review_text, "complaint_type": c.complaint_type, "severity": c.severity, "confidence": c.confidence} for c in self.complaints],
            "barrier_hypotheses": [{"description": h.description, "barrier_type": h.barrier_type, "confidence": h.confidence, "provenance": h.provenance} for h in self.barrier_hypotheses],
            "top_opportunities": [{"gap_description": g.gap_description, "evidence_count": g.evidence_count, "severity": g.severity, "exploitability": g.exploitability} for g in self.top_opportunities],
            "provenance_summary": self.provenance_summary,
            "evidence_data": self.evidence_data,
        }
