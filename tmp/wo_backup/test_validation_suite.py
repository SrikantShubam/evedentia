"""
Evidentia Validation Suite — Week 1 critic-reset contract
=========================================================
Verdicts are now KILL / REFINE / PURSUE.
Exit condition: pytest tests/validation/ -v must be fully green.
"""

import pytest

from evidentia.auditor import verify_quote
from evidentia.scoring import dedupe_by_cluster, score_opportunity


def _opportunity(
    *,
    willingness_to_pay="pass",
    distribution_channel="pass",
    data_feasibility="pass",
    competition_gap=0.8,
    buildability=0.9,
    reachability_strength=0.7,
    cluster_id="cluster-1",
    opportunity_id="opp-1",
    published_at="2025-06-01T00:00:00Z",
):
    return {
        "opportunity_id": opportunity_id,
        "cluster_id": cluster_id,
        "title": "Automated invoice matching",
        "verbatim_quote": "users said they would pay",
        "source_url": "https://example.com/thread/1",
        "source_text": "users said they would pay for this tool",
        "willingness_to_pay": willingness_to_pay,
        "distribution_channel": distribution_channel,
        "data_feasibility": data_feasibility,
        "competition_gap": competition_gap,
        "buildability": buildability,
        "reachability_strength": reachability_strength,
        "published_at": published_at,
    }


def test_val01_hard_gate_all_pass_yields_pursue():
    opp = _opportunity()
    result = score_opportunity(opp)
    assert result["verdict"] == "PURSUE"
    assert result["score"] > 0.0


@pytest.mark.parametrize("failing_gate", ["willingness_to_pay", "distribution_channel", "data_feasibility"])
def test_val02_single_gate_failure_yields_refine(failing_gate):
    kwargs = {failing_gate: "fail"}
    opp = _opportunity(**kwargs)
    result = score_opportunity(opp)
    assert result["verdict"] == "REFINE"
    assert result["score"] == 0.0


def test_val03_dedup_keeps_best_per_cluster():
    strong = _opportunity(
        cluster_id="inv",
        opportunity_id="opp-strong",
        competition_gap=0.9,
        buildability=0.9,
        reachability_strength=0.9,
    )
    weak = _opportunity(
        cluster_id="inv",
        opportunity_id="opp-weak",
        competition_gap=0.1,
        buildability=0.1,
        reachability_strength=0.1,
    )
    strong_scored = {**strong, **score_opportunity(strong)}
    weak_scored = {**weak, **score_opportunity(weak)}
    result = dedupe_by_cluster([strong_scored, weak_scored])
    assert len(result) == 1
    assert result[0]["opportunity_id"] == "opp-strong"


def test_val04_auditor_verified_when_quote_present(monkeypatch):
    from evidentia import auditor

    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url, **kw: None)
    result = verify_quote(
        {
            "source_text": "We would absolutely pay $200/month for automated invoice matching.",
            "source_url": "https://news.ycombinator.com/item?id=99999",
            "verbatim_quote": "pay $200/month for automated invoice matching",
        }
    )
    assert result["verified"] is True
    assert result["source_url"] == "https://news.ycombinator.com/item?id=99999"


def test_val05_auditor_not_verified_when_quote_absent(monkeypatch):
    from evidentia import auditor

    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url, **kw: None)
    result = verify_quote(
        {
            "source_text": "This article talks about cloud storage costs.",
            "source_url": "https://reddit.com/r/accounting/comments/xyz",
            "verbatim_quote": "pay $200/month for automated invoice matching",
        }
    )
    assert result["verified"] is False
    assert result["discard_reason"] == "quote_not_verifiable"


def test_val11_auditor_proof_level_contract(monkeypatch):
    from evidentia import auditor

    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url, **kw: "contains quoted fragment")
    fetched = verify_quote(
        {
            "source_url": "https://example.com/fetched",
            "verbatim_quote": "quoted fragment",
            "source_text": "irrelevant",
        }
    )

    monkeypatch.setattr(auditor, "_fetch_page_text", lambda url, **kw: None)
    in_memory = verify_quote(
        {
            "source_url": "https://example.com/in-memory",
            "verbatim_quote": "memory fragment",
            "source_text": "memory fragment",
        }
    )
    none = verify_quote(
        {
            "source_url": "https://example.com/none",
            "verbatim_quote": "missing fragment",
            "source_text": "something else",
        }
    )
    assert {fetched["proof_level"], in_memory["proof_level"], none["proof_level"]} <= {"fetched", "in_memory", "none"}


def test_val12_score_verdict_enum_has_no_hold_or_skip():
    outputs = [
        score_opportunity(_opportunity()),
        score_opportunity(_opportunity(willingness_to_pay="fail")),
        score_opportunity(
            _opportunity(
                willingness_to_pay="fail",
                distribution_channel="fail",
                data_feasibility="fail",
                competition_gap=0.0,
                buildability=0.0,
                reachability_strength=0.0,
            )
        ),
    ]
    verdicts = {item["verdict"] for item in outputs}
    assert "HOLD" not in verdicts
    assert "SKIP" not in verdicts
    assert verdicts <= {"KILL", "REFINE", "PURSUE"}
