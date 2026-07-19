"""Bridge quality: profile inference from evidence kind, evidence text
carry-through, and idea-specific kill conditions. Written after the
2026-07-19 live proof (docs/LIVE_PROOF_FINDINGS.md) in which consumer
meditation apps were routed through b2b_workflow procurement gates."""

from evidentia.cli import _bridge_research_to_ideas


def _research(evidence_kind: str) -> dict:
    return {
        "query": "meditation apps",
        "competitors_analyzed": ["Headspace", "Calm"],
        "total_reviews": 3,
        "top_opportunities": [
            {
                "gap_description": "Multiple users report PRICING issues with existing Headspace, Calm apps",
                "evidence_count": 3,
                "severity": "HIGH",
                "exploitability": "MEDIUM",
            }
        ],
        "complaints": [],
        "barrier_hypotheses": [],
        "evidence_data": [
            {
                "source_url": "https://apps.apple.com/r/1",
                "verbatim_quote": "Pricing doubled and I was charged after cancelling.",
                "source_text": "Pricing doubled and I was charged after cancelling.",
                "source_kind": evidence_kind,
            },
            {
                "source_url": "https://apps.apple.com/r/2",
                "verbatim_quote": "Would pay for a cheaper pricing tier without sleep stories.",
                "source_text": "Would pay for a cheaper pricing tier without sleep stories.",
                "source_kind": evidence_kind,
            },
        ],
    }


def test_bridge_infers_consumer_app_when_evidence_is_app_store():
    ideas = _bridge_research_to_ideas(_research("app_store"), profile_override=None)
    assert ideas[0]["gate_profile"] == "consumer_app"


def test_bridge_carries_evidence_texts():
    ideas = _bridge_research_to_ideas(_research("app_store"), profile_override=None)
    texts = ideas[0]["evidence_texts"]
    assert texts, "bridge must carry verbatim quotes into ideas"
    assert any("charged after cancelling" in t for t in texts.values())


def test_bridge_marks_web_snippets_as_cited_not_verified():
    ideas = _bridge_research_to_ideas(_research("web_search"), profile_override=None)
    provs = set(ideas[0]["evidence_provenance"].values())
    assert "verified" not in provs
    assert "cited_evidence" in provs


def test_bridge_kill_condition_is_idea_specific():
    ideas = _bridge_research_to_ideas(_research("app_store"), profile_override=None)
    kc = ideas[0]["kill_condition"]
    assert kc["description"] != "No market evidence"
    assert "PRICING" in kc["description"]
