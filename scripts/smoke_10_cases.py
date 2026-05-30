"""10 tournament smoke test cases — exercise the engine API end-to-end."""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidentia.models import Idea, KillCondition, PlayerProfile, TerminalVerdict, RoundOutcome, GateStatus
from evidentia.tournament.engine import run_tournament
from evidentia.outputs import write_player_profile


def profile(pid: str, risk: str = "med", budget: int = 15000, llm_calls: int = 200, reentry: int = 1) -> PlayerProfile:
    return PlayerProfile(
        id=pid, team="SmokeTest", skills=["python"],
        budget_validate_usd=3000, budget_build_usd=budget, budget_reach_usd=2000,
        weeks_to_ship=8, risk=risk, max_llm_calls_per_tournament=llm_calls,
        max_reentry_rounds=reentry,
    )

def kill(gate: str = "parent_market_exists", desc: str = "No market signal") -> KillCondition:
    return KillCondition(description=desc, gate_name=gate)

def idea(iid: str, evidence: list[str] = None, provenance: dict = None, **kw) -> Idea:
    return Idea(
        id=iid, label=kw.get("label", "Test idea"), anchor_slug=kw.get("anchor", "test-anchor"),
        incumbent=kw.get("incumbent", "IncumbentX"), cohort=kw.get("cohort", "test cohort"),
        pain_hypothesis=kw.get("pain", "Users need a better solution."),
        kill_condition=kill(kw.get("kill_gate", "parent_market_exists")),
        evidence_ids=evidence or ["sig-a", "sig-b", "sig-c"],
        evidence_provenance=provenance or {},
        search_queries=kw.get("queries", ["pain point"]), origin="manual",
        gate_profile=kw.get("profile", "consumer_app"), gate_profile_source="explicit",
    )


cases = []

# ── CASE 1: All structural + evidence gates pass → PURSUE_SPIKE ──
cases.append({
    "name": "01_pursue_spike",
    "player": profile("p1"),
    "ideas": [
        idea("i1", evidence=["sig-1", "sig-2", "sig-3", "sig-4"],
             provenance={"sig-1":"verified","sig-2":"verified","sig-3":"verified","sig-4":"verified"},
             queries=["agency workflow pain", "budget for automation", "monthly subscription"],
             pain="Agencies pay $500/mo for manual reconciliation; automated alternative would save 10h/week.")
    ],
})

# ── CASE 2: Structural gate fails → KILL ──
cases.append({
    "name": "02_structural_kill",
    "player": profile("p2"),
    "ideas": [
        idea("i2", pain="This solves nothing.", anchor=None, incumbent=None,
             evidence=["sig-1"], queries=[])
    ],
})

# ── CASE 3: Evidence gate fails → INSUFFICIENT_EVIDENCE ──
cases.append({
    "name": "03_insufficient_evidence",
    "player": profile("p3"),
    "ideas": [
        idea("i3", evidence=["sig-1"], queries=["maybe something"],
             pain="Seems like a decent idea but need more proof.")
    ],
})

# ── CASE 4: All ideas fail with different causes → zero winner diagnosis ──
cases.append({
    "name": "04_zero_winner_diagnosis",
    "player": profile("p4"),
    "ideas": [
        idea("i4a", evidence=["sig-x"], queries=[], anchor=None,
             pain="No real market."),
        idea("i4b", evidence=["sig-y"], queries=["test"],
             pain="Shallow evidence only."),
    ],
})

# ── CASE 5: Mixed — one passes, one fails → one PURSUE/one KILL ──
cases.append({
    "name": "05_mixed_outcomes",
    "player": profile("p5"),
    "ideas": [
        idea("i5a", evidence=["v1","v2","v3","v4"],
             provenance={"v1":"verified","v2":"verified","v3":"verified","v4":"verified"},
             queries=["monthly spend", "switching cost", "referral incentive"],
             pain="Agencies churn due to manual billing; automated billing tool saves 15h/week."),
        idea("i5b", evidence=["w1"], queries=[], anchor=None,
             pain="No clear market signal."),
    ],
})

# ── CASE 6: Low confidence → SHORTLIST ──
cases.append({
    "name": "06_shortlist",
    "player": profile("p6"),
    "ideas": [
        idea("i6", evidence=["e1","e2","e3"],
             provenance={"e1":"verified","e2":"synthetic","e3":"synthetic"},
             pain="Plausible but uncertain. Only one verified voice.")
    ],
})

# ── CASE 7: Budget exhausted mid-tournament ──
cases.append({
    "name": "07_budget_exhausted",
    "player": profile("p7", budget=500, llm_calls=1),
    "ideas": [
        idea("i7", evidence=["s1","s2","s3","s4"],
             provenance={"s1":"verified","s2":"verified","s3":"verified","s4":"verified"},
             queries=["expensive LLM gate test", "another query"],
             pain="Strong idea but very limited budget."),
    ],
})

# ── CASE 8: Re-entry candidate (INSUFFICIENT_EVIDENCE) ──
cases.append({
    "name": "08_reentry_candidate",
    "player": profile("p8", reentry=2),
    "ideas": [
        idea("i8", evidence=["e1","e2"], queries=["budget pain"],
             pain="only two pieces of evidence, needs more", kill_gate="complaint_signal_exists"),
    ],
})

# ── CASE 9: Synthetic-only evidence → 3FV gate fails ──
cases.append({
    "name": "09_synthetic_only",
    "player": profile("p9"),
    "ideas": [
        idea("i9", evidence=["syn-a","syn-b","syn-c","syn-d"],
             provenance={"syn-a":"synthetic","syn-b":"synthetic","syn-c":"synthetic","syn-d":"synthetic"},
             queries=["LLM generated query"],
             pain="All evidence is synthetic — no real user voices."),
    ],
})

# ── CASE 10: b2b_workflow profile with procurement path ──
cases.append({
    "name": "10_b2b_procurement",
    "player": profile("p10"),
    "ideas": [
        idea("i10", evidence=["p1","p2","p3","p4"],
             provenance={"p1":"verified","p2":"verified","p3":"verified","p4":"verified"},
             queries=["procurement process", "budget owner", "approval workflow", "invoice"],
             pain="Ops managers waste 20h/mo on vendor procurement; CIO has budget approved.",
             profile="b2b_workflow"),
    ],
})


# ──────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────
results = []
for c in cases:
    outdir = Path("outputs") / "smoke" / c["name"]
    outdir.mkdir(parents=True, exist_ok=True)

    p = c["player"]
    write_player_profile(outdir / "profile.json", p)

    try:
        result = run_tournament(
            ideas=c["ideas"],
            player=p,
            tournament_id=f"smoke-{c['name']}",
            gate_profile=c["ideas"][0].gate_profile,
        )
    except Exception as exc:
        r = {"case": c["name"], "status": "ERROR", "error": str(exc)}
    else:
        r = result.to_dict()
        r["case"] = c["name"]
        r["status"] = "OK"
        # Summarise verdicts per idea
        r["verdicts"] = []
        for state in r.get("ideas", []):
            idea_id = state.get("idea", {}).get("id", "?")
            tv = state.get("terminal_verdict", "?")
            conf = state.get("confidence_score_so_far", 0)
            r["verdicts"].append({"idea": idea_id, "verdict": tv, "confidence": round(conf, 3)})

    (outdir / "result.json").write_text(json.dumps(r, indent=2, default=str), encoding="utf-8")
    results.append(r)
    verdict_str = ", ".join(f"{v['idea']}={v['verdict']}" for v in r.get("verdicts", []))
    print(f"{c['name']:30s} {r['status']:6s}  {verdict_str}")


# Write consolidated report
report = {"smoke_test_results": []}
for r in results:
    report["smoke_test_results"].append({
        "case": r["case"],
        "status": r["status"],
        "error": r.get("error"),
        "verdicts": r.get("verdicts", []),
        "winner": r.get("memo", {}).get("winner"),
        "zero_winner_diagnosis": r.get("memo", {}).get("zero_winner_diagnosis"),
    })
report_path = Path("outputs") / "smoke" / "consolidated_report.json"
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
print(f"\nConsolidated report: {report_path}")
