"""Schema validation tests for research-related models."""
from evidentia.models import Review, ClassifiedComplaint, BarrierHypothesis, OpportunityGap, ResearchReport


def test_review_defaults():
    r = Review(text="bad app", rating=1, source="app_store")
    assert r.authenticity == "AUTHENTIC"
    assert r.version is None


def test_classified_complaint():
    c = ClassifiedComplaint(review_text="too expensive", complaint_type="PRICING", severity=8, confidence=0.9)
    assert c.review_text == "too expensive"
    assert c.complaint_type == "PRICING"


def test_barrier_hypothesis_default_provenance():
    h = BarrierHypothesis(description="High regulatory barrier", barrier_type="regulation", confidence=0.7)
    assert h.provenance == "LLM_EDUCATED_GUESS"


def test_opportunity_gap():
    g = OpportunityGap(gap_description="No offline mode", evidence_count=12, severity="HIGH", exploitability="MEDIUM")
    assert g.evidence_count == 12


def test_research_report_to_dict():
    report = ResearchReport(
        query="test query",
        competitors_analyzed=["AppA", "AppB"],
        total_reviews=10,
        complaints=[ClassifiedComplaint(review_text="bad", complaint_type="UX", severity=5, confidence=0.8)],
        barrier_hypotheses=[BarrierHypothesis(description="Hard to solve", barrier_type="technical", confidence=0.5)],
        top_opportunities=[OpportunityGap(gap_description="Missing feature X", evidence_count=5, severity="HIGH", exploitability="HIGH")],
        provenance_summary="all evidence cited",
    )
    d = report.to_dict()
    assert d["query"] == "test query"
    assert len(d["complaints"]) == 1
    assert len(d["barrier_hypotheses"]) == 1
    assert d["top_opportunities"][0]["severity"] == "HIGH"
