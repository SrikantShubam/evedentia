"""Live smoke test — run with: python -m pytest scripts/live_smoke.py -s -x"""
import json
from pathlib import Path
from evidentia.providers import load_external_provider_env
from evidentia.models import Anchor, DemandSignal, PlayerProfile
from evidentia.generator import generate_ideas_from_anchor
from evidentia.tournament.engine import run_tournament
from evidentia.outputs import write_player_profile


def test_live_keys():
    env = load_external_provider_env()
    assert env.get("OPENROUTER_API_KEY") or env.get("NVIDIA_API_KEY") or env.get("GROQ_API_KEY"), "No LLM keys found"
    print("API keys: OK")
    print("  OPENROUTER:", env.get("OPENROUTER_API_KEY", "")[:12] + "..." if env.get("OPENROUTER_API_KEY") else "MISSING")
    print("  NVIDIA:", env.get("NVIDIA_API_KEY", "")[:12] + "..." if env.get("NVIDIA_API_KEY") else "MISSING")
    print("  GROQ:", env.get("GROQ_API_KEY", "")[:12] + "..." if env.get("GROQ_API_KEY") else "MISSING")


def test_generate_from_anchor():
    env = load_external_provider_env()
    sig = DemandSignal(
        signal_id="live-proof",
        source_url="https://news.ycombinator.com/item?id=123",
        verbatim_quote="I wish there was a tool that automated my invoicing",
        timestamp="2026-05-01T00:00:00Z",
        verified=True,
        proof_level="fetched",
    )
    anchor = Anchor(
        slug="smb-invoicing",
        market_name="SMB Invoicing",
        incumbents=["FreshBooks", "QuickBooks", "Xero"],
        proof_of_market=sig,
        cohort_hints=["freelancers", "small agencies", "solopreneurs"],
    )
    ideas = generate_ideas_from_anchor(anchor, count=3, env=env)
    print(f"\nGenerated {len(ideas)} ideas:")
    for i, idea in enumerate(ideas):
        print(f"  {i+1}. [{idea['label']}]")
        print(f"     cohort: {idea['cohort']}")
        print(f"     pain: {idea['pain_hypothesis'][:80]}")
        print(f"     kill: {idea['kill_condition']}")
        print(f"     gate_profile: {idea['gate_profile']} (source: {idea['gate_profile_source']})")
        print(f"     evidence_ids: {len(idea['evidence_ids'])}")
    assert len(ideas) == 3
    assert all("kill_condition" in i for i in ideas)
    assert all("gate_profile" in i for i in ideas)


def test_run_tournament():
    env = load_external_provider_env()
    player = PlayerProfile(
        id="live-tester", team="SmokeTest", skills=["python"],
        budget_validate_usd=3000, budget_build_usd=15000, budget_reach_usd=2000,
        weeks_to_ship=8, risk="med", max_llm_calls_per_tournament=20,
    )
    write_player_profile(Path("outputs/smoke/live_profile.json"), player)

    from evidentia.models import Idea, KillCondition
    idea_objs = [
        Idea(
            id="live-1", label="Invoice automation for agencies",
            anchor_slug="smb-invoicing", incumbent="FreshBooks",
            cohort="small agencies with manual billing",
            pain_hypothesis="Agencies waste 10h/week on manual invoicing and are willing to pay $50/mo for automation.",
            kill_condition=KillCondition(description="No willingness to pay", gate_name="willingness_to_pay"),
            evidence_ids=["ev-1","ev-2","ev-3","ev-4"],
            evidence_provenance={"ev-1":"verified","ev-2":"verified","ev-3":"verified","ev-4":"verified"},
            search_queries=["agency invoicing pain", "monthly subscription billing", "freelancer invoice automation"],
            origin="manual", gate_profile="consumer_app", gate_profile_source="explicit",
        ),
        Idea(
            id="live-2", label="Time tracking integration",
            anchor_slug="smb-invoicing", incumbent="QuickBooks",
            cohort="consultants needing time-to-invoice",
            pain_hypothesis="Consultants lose billable hours due to poor time tracking integration with invoicing.",
            kill_condition=KillCondition(description="No retention signal", gate_name="retention_plausible"),
            evidence_ids=["ev-5","ev-6","ev-7"],
            evidence_provenance={"ev-5":"verified","ev-6":"verified","ev-7":"verified"},
            search_queries=["time tracking invoicing integration", "consultant billing pain", "hourly invoice"],
            origin="manual", gate_profile="consumer_app", gate_profile_source="explicit",
        ),
    ]
    result = run_tournament(ideas=idea_objs, player=player, tournament_id="live-smoke")
    out = result.to_dict()
    Path("outputs/smoke/live_tournament.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    print(f"\nTournament complete: {out.get('tournament_id')}")
    for s in out.get("ideas", []):
        iid = s["idea"]["id"]
        tv = s["terminal_verdict"]
        conf = round(s["confidence_score_so_far"], 3)
        print(f"  {iid}: {tv} (conf={conf})")
        for g in s.get("gate_results", []):
            if g["status"] != "COMPLETED":
                continue
            print(f"    {g['gate_name']}: {g['outcome']} (conf={g['confidence']})")

    winner = out.get("memo", {}).get("winner") or out.get("memo", {}).get("zero_winner_diagnosis")
    print(f"\nWinner/diagnosis: {winner}")
    print(f"\nFull output: outputs/smoke/live_tournament.json")
