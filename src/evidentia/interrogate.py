"""Tier 1 interrogator — deterministic queries against stored JSON artifacts.

Reads research reports, tournament payloads, and decision memos. Answers
factual questions by extracting matching data. No LLM calls. $0 cost.
"""

from __future__ import annotations

import json
from pathlib import Path


def _load_artifact(path: str) -> dict:
    raw = Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def interrogate(artifact_path: str, question: str) -> str:
    """Answer a factual question by querying stored JSON artifacts.

    Tier 1 only — deterministic, $0, no LLM. For synthesis questions
    (counterfactuals, cross-idea analysis), see Tier 2 (Phase 6+).
    """
    data = _load_artifact(artifact_path)
    q = question.lower()

    # --- Research report queries ---
    if "competitor" in q and ("most" in q or "list" in q or "many" in q):
        competitors = data.get("competitors_analyzed", [])
        return json.dumps({"competitors": competitors, "count": len(competitors)}, indent=2)

    if "review" in q and ("count" in q or "many" in q or "total" in q):
        return json.dumps({"total_reviews": data.get("total_reviews", 0)}, indent=2)

    if "complaint" in q or "opportunit" in q:
        complaints = data.get("complaints", [])
        opps = data.get("top_opportunities", [])
        return json.dumps({"complaints": complaints, "opportunities": opps}, indent=2)

    if "barrier" in q or "hypothesis" in q:
        return json.dumps({"barrier_hypotheses": data.get("barrier_hypotheses", [])}, indent=2)

    # --- Tournament queries ---
    ideas = data.get("ideas", [])
    memo = data.get("memo")

    if "winner" in q or ("who" in q and "won" in q):
        if memo and memo.get("winner"):
            return json.dumps({"winner": memo["winner"]}, indent=2)
        return "No winner found in tournament data."

    if "why" in q and ("die" in q or "kill" in q or "fail" in q):
        killed = []
        for state in ideas:
            if state.get("terminal_verdict") == "KILL":
                gate_results = state.get("gate_results", [])
                failed = [g for g in gate_results if g.get("outcome") == "FAIL"]
                killed.append({
                    "idea_id": state.get("id"),
                    "idea_label": state.get("label"),
                    "failed_gates": [{"gate": g["gate_name"], "reason": g.get("killed_by", "unknown")} for g in failed],
                })
        if killed:
            return json.dumps({"killed_ideas": killed}, indent=2)
        return "No killed ideas found."

    if "gate" in q and ("weak" in q or "worst" in q or "most" in q):
        gate_counts: dict[str, int] = {}
        for state in ideas:
            for g in state.get("gate_results", []):
                if g.get("outcome") == "FAIL":
                    gate_counts[g["gate_name"]] = gate_counts.get(g["gate_name"], 0) + 1
        sorted_gates = sorted(gate_counts.items(), key=lambda x: x[1], reverse=True)
        return json.dumps({"gate_failure_counts": [{"gate": k, "failures": v} for k, v in sorted_gates]}, indent=2)

    if "evidence" in q:
        evidence = []
        for state in ideas:
            for g in state.get("gate_results", []):
                if g.get("evidence_ids"):
                    evidence.append({
                        "idea_id": state.get("id"),
                        "gate": g["gate_name"],
                        "evidence_ids": g["evidence_ids"],
                    })
        return json.dumps({"evidence_by_idea": evidence}, indent=2)

    # Fallback: return summary
    summary = {
        "artifact_type": "tournament" if ideas else "research_report" if "competitors_analyzed" in data else "unknown",
        "keys_available": list(data.keys()),
    }
    return json.dumps(summary, indent=2)
