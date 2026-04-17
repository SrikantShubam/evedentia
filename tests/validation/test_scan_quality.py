from evidentia.classifier import _classification_prompt
from evidentia.classifier import classify_candidate
from evidentia.cli import (
    _generate_hypothesis,
    _pre_score_rejection_reason,
    _prosecute_hypothesis,
    run_fixture_scan,
)
from evidentia.scanners.github import scan_github_live
from evidentia.scanners.hn import scan_hn_live
from evidentia.scanners.reddit import scan_reddit_live
from evidentia.scoring import dedupe_by_content_fingerprint, score_opportunity


def test_prompt_no_example_numeric_defaults():
    candidate = {"title": "test", "verbatim_quote": "test", "source_text": "test"}
    prompt = _classification_prompt(candidate)
    assert "0.8," not in prompt
    assert "0.7," not in prompt
    assert "0.6}" not in prompt


def test_hn_html_entities_decoded():
    def _mock_fetch(_url):
        return {
            "hits": [
                {
                    "objectID": "12345",
                    "title": "Test story",
                    "story_text": "I&#x27;m building a tool &amp; it&#x27;s great",
                    "created_at": "2025-01-01T00:00:00.000Z",
                }
            ]
        }

    results = scan_hn_live("test", max_results=1, fetch_json=_mock_fetch)
    assert len(results) == 1
    assert "&#x27;" not in results[0]["verbatim_quote"]
    assert "I'm building a tool & it's great" == results[0]["source_text"]


def test_github_filters_short_body_issues():
    def _mock_fetch(_url, headers=None):
        return {
            "items": [
                {
                    "html_url": "https://github.com/a/b/issues/1",
                    "title": "Expense Tracking",
                    "body": "Expense Tracking",
                    "id": 1,
                    "updated_at": "2025-01-01T00:00:00Z",
                },
                {
                    "html_url": "https://github.com/a/b/issues/2",
                    "title": "Feature: expense tracking",
                    "body": "We need expense tracking because we currently spend hours in spreadsheets and need a better solution for our 50-person team.",
                    "id": 2,
                    "updated_at": "2025-01-01T00:00:00Z",
                },
            ]
        }

    results = scan_github_live("expense tracking", max_results=3, fetch_json=_mock_fetch)
    assert len(results) == 1
    assert "github:2" == results[0]["cluster_id"]


def test_github_query_targets_feature_requests():
    captured = {}

    def _mock_fetch(url, headers=None):
        captured["url"] = url
        return {"items": []}

    scan_github_live("invoicing", max_results=3, fetch_json=_mock_fetch)
    assert "feature-request" in captured["url"] or "enhancement" in captured["url"]


def test_content_dedup_removes_cross_platform_duplicates():
    body = "We need better expense tracking for our team. " * 5
    item_a = {
        "cluster_id": "reddit:a",
        "source_text": body,
        "score": 0.5,
        "published_at": None,
        "opportunity_id": "opp_001",
    }
    item_b = {
        "cluster_id": "reddit:b",
        "source_text": body,
        "score": 0.4,
        "published_at": None,
        "opportunity_id": "opp_002",
    }
    result = dedupe_by_content_fingerprint([item_a, item_b])
    assert len(result) == 1
    assert result[0]["cluster_id"] == "reddit:a"


def test_hold_exposes_gate_failures():
    opportunity = {
        "willingness_to_pay": "fail",
        "distribution_channel": "pass",
        "data_feasibility": "pass",
        "competition_gap": 0.8,
        "buildability": 0.7,
        "reachability_strength": 0.6,
    }
    result = score_opportunity(opportunity)
    assert result["verdict"] == "REFINE"
    assert "gate_failures" in result
    assert result["gate_failures"] == ["willingness_to_pay"]


def test_pursue_has_no_gate_failures():
    opportunity = {
        "willingness_to_pay": "pass",
        "distribution_channel": "pass",
        "data_feasibility": "pass",
        "competition_gap": 0.8,
        "buildability": 0.7,
        "reachability_strength": 0.6,
    }
    result = score_opportunity(opportunity)
    assert result["verdict"] == "PURSUE"
    assert result.get("gate_failures") is None or result.get("gate_failures") == []


def test_reddit_filters_low_score_posts():
    def _mock_fetch(_url, headers=None):
        return {
            "data": {
                "children": [
                    {
                        "data": {
                            "permalink": "/r/test/comments/abc/",
                            "title": "Good signal",
                            "selftext": "We need expense tracking for our 20-person startup and would pay monthly.",
                            "created_utc": 1700000000,
                            "score": 50,
                            "subreddit": "startups",
                        }
                    },
                    {
                        "data": {
                            "permalink": "/r/deals/comments/xyz/",
                            "title": "Promo",
                            "selftext": "Buy now",
                            "created_utc": 1700000000,
                            "score": 1,
                            "subreddit": "LooteraShopper",
                        }
                    },
                ]
            }
        }

    results = scan_reddit_live("expense tracking", max_results=5, fetch_json=_mock_fetch)
    assert len(results) == 1
    assert results[0]["title"] == "Good signal"


def test_tester_recruitment_signal_forces_gate_fail():
    class _AllPassProvider:
        def generate_json(self, prompt: str, model: str) -> dict:
            return {
                "willingness_to_pay": "pass",
                "distribution_channel": "pass",
                "data_feasibility": "pass",
                "competition_gap": 0.8,
                "buildability": 0.7,
                "reachability_strength": 0.6,
            }

    candidate = {
        "title": "Need 20 testers for Money Master",
        "source_text": "I will test your app back immediately if you test mine.",
        "verbatim_quote": "Need 20 testers. I will test back immediately.",
        "source_url": "https://www.reddit.com/r/TestersCommunity/comments/1abcxyz/",
    }
    classified = classify_candidate(candidate, provider=_AllPassProvider(), model="all-pass")
    assert classified["willingness_to_pay"] == "fail"


def test_pre_score_rejects_tester_recruitment_candidate():
    candidate = {
        "source": "reddit",
        "title": "Need 20 testers for Money Master",
        "source_text": "I will test back immediately.",
        "verbatim_quote": "Need 20 testers",
        "source_url": "https://www.reddit.com/r/TestersCommunity/comments/1abcxyz/",
    }
    assert _pre_score_rejection_reason(candidate) == "reject_tester_recruitment"


def test_generator_creates_replacement_hypothesis_from_incumbent_pain():
    candidate = {
        "title": "Started a Linkedin Agency -> Best tools?",
        "source": "reddit",
        "source_text": (
            "Taplio, Buffer, and Hootsuite are fine for posting, but none show who engaged, "
            "whether those people fit our ICP, or which companies they came from. We started "
            "building something internally for multi-account agency use."
        ),
        "verbatim_quote": (
            "None of them really help you answer who engaged, are they relevant, "
            "did this reach the right companies."
        ),
        "source_url": "https://www.reddit.com/r/DigitalMarketing/comments/1smbsr3/",
    }

    hypothesis = _generate_hypothesis(candidate)

    assert hypothesis["hypothesis_type"] == "replacement_wedge"
    assert "replace" in hypothesis["wedge_statement"].lower() or "agency" in hypothesis["wedge_statement"].lower()


def test_prosecutor_kills_builder_announcement_without_buyer_signal():
    candidate = {
        "title": "Show HN: Bitterbot – A local-first P2P agent mesh with skill trading",
        "source": "hn",
        "source_text": (
            "We built this because we were tired of centralized agent frameworks. "
            "We are looking for deep technical feedback on the mesh stability."
        ),
        "verbatim_quote": "We are looking for deep technical feedback on the mesh stability.",
        "source_url": "https://news.ycombinator.com/item?id=47766676",
    }

    hypothesis = _generate_hypothesis(candidate)
    prosecution = _prosecute_hypothesis(candidate, hypothesis)

    assert prosecution["status"] == "kill"
    assert prosecution["reason"] == "builder_showcase_without_buyer_evidence"


def test_pre_score_rejects_personal_life_planning_thread():
    candidate = {
        "source": "reddit",
        "title": "Decision paralysis on warchest allocation",
        "source_text": (
            "Wife and I are stuck on deciding allocation for kids, housing, and retirement. "
            "Would love advice on managing smart money."
        ),
        "verbatim_quote": "Would love advice on managing smart money.",
        "source_url": "https://www.reddit.com/r/singaporefi/comments/1smbmmb/",
    }

    assert _pre_score_rejection_reason(candidate) == "reject_personal_life_planning"


def test_prosecutor_kills_solution_marketing_without_buyer_pain():
    candidate = {
        "title": "Invoice OCR API for Logistics Expense Tracking Automation",
        "source": "hn",
        "source_text": (
            "An Invoice OCR API helps automate this process by extracting information from invoice images "
            "or PDFs. This structured data allows businesses to monitor expenses more efficiently."
        ),
        "verbatim_quote": "An Invoice OCR API helps automate this process by extracting important information.",
        "source_url": "https://news.ycombinator.com/item?id=47362152",
    }

    hypothesis = _generate_hypothesis(candidate)
    prosecution = _prosecute_hypothesis(candidate, hypothesis)

    assert prosecution["status"] == "kill"
    assert prosecution["reason"] == "solution_marketing_without_buyer_evidence"


def test_fixture_scan_synthesizes_cluster_into_single_opportunity():
    payload = run_fixture_scan({"hn": "tests/fixtures/hn_sample.json"})

    assert len(payload["opportunities"]) == 1
    opportunity = payload["opportunities"][0]
    assert len(opportunity["verified_signals"]) == 2
    assert opportunity["hypothesis_validation"]["status"] == "keep"
    assert opportunity["hypothesis"]["hypothesis_type"] == "replacement_wedge"
    assert opportunity["hypothesis_validation"]["reason"]


def test_fixture_scan_persists_hypothesis_validation_metadata():
    payload = run_fixture_scan({"hn": "tests/fixtures/hn_sample.json"})

    opportunity = payload["opportunities"][0]
    assert opportunity["hypothesis_validation"]["status"] in {"keep", "revise", "kill"}
    assert "reason" in opportunity["hypothesis_validation"]
    assert opportunity["hypothesis"]["wedge_statement"]
