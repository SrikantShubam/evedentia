from evidentia.providers import build_scan_plan


def test_build_scan_plan_defaults_to_core_sources():
    plan = build_scan_plan(domain="fintech")

    assert plan["domain"] == "fintech"
    assert plan["mode"] == "dry-run"
    assert [item["source"] for item in plan["sources"]] == ["hn", "reddit", "github"]


def test_build_scan_plan_respects_requested_sources():
    plan = build_scan_plan(domain="fintech", requested_sources=["github"])

    assert [item["source"] for item in plan["sources"]] == ["github"]
