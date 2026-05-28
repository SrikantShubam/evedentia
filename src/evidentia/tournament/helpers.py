from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from evidentia.models import DemandSignal, Idea, PlayerProfile
from evidentia.outputs import read_player_profile, write_player_profile


def safe_run_timestamp(now: datetime | None = None) -> str:
    instant = now or datetime.now(timezone.utc)
    return instant.strftime("%Y-%m-%dT%H-%M-%SZ")


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, payload: dict) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_player_profile_from_path(path: str) -> PlayerProfile:
    payload = load_json(path)
    return PlayerProfile(**payload)


def load_player_profile_any(path: str) -> PlayerProfile:
    try:
        return load_player_profile_from_path(path)
    except Exception:
        return read_player_profile(Path(path))


def load_ideas_jsonl_raw(path: str) -> list[tuple[int, dict]]:
    rows: list[tuple[int, dict]] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"ideas jsonl parse error at line {line_number}: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"invalid idea at line {line_number}: expected object")
        rows.append((line_number, payload))
    return rows


def discover_evidence_ids(raw_idea: dict) -> list[str]:
    existing = [str(item) for item in raw_idea.get("evidence_ids", []) if str(item).strip()]
    if existing:
        return existing
    queries = [str(item).strip() for item in raw_idea.get("search_queries", []) if str(item).strip()]
    if not queries:
        return []
    idea_id = str(raw_idea.get("id", "idea"))
    return [
        DemandSignal.build_signal_id(
            source_url=f"https://discover.local/{idea_id}/{idx}",
            verbatim_quote=query,
        )
        for idx, query in enumerate(queries[:3], start=1)
    ]


def enrich_idea_evidence(
    idea: Idea,
    player: PlayerProfile | None = None,
    max_composite_evidence: int = 5,
) -> tuple[list[str], int]:
    evidence_ids = list(idea.evidence_ids)

    if len(evidence_ids) >= 3:
        return evidence_ids, 0

    queries = [q.strip() for q in idea.search_queries if q.strip()]
    if not queries:
        return evidence_ids, 0

    existing_set = set(evidence_ids)
    new_ids: list[str] = []
    enrichment_calls = 0

    for idx, query in enumerate(queries):
        if len(evidence_ids) + len(new_ids) >= max_composite_evidence:
            break
        signal_id = DemandSignal.build_signal_id(
            source_url=f"https://enrich.local/{idea.id}/{idx}",
            verbatim_quote=query,
        )
        if signal_id not in existing_set:
            new_ids.append(signal_id)
            existing_set.add(signal_id)
            enrichment_calls += 1
            idea.evidence_provenance[signal_id] = "synthetic"

    return evidence_ids + new_ids, enrichment_calls


def materialize_ideas(raw_rows: list[tuple[int, dict]], *, discover_evidence: bool) -> tuple[list[Idea], list[dict]]:
    ideas: list[Idea] = []
    discards: list[dict] = []
    for line_number, raw_idea in raw_rows:
        local = dict(raw_idea)
        evidence_ids = [str(item) for item in local.get("evidence_ids", []) if str(item).strip()]
        discovered = False
        if not evidence_ids:
            if discover_evidence:
                evidence_ids = discover_evidence_ids(local)
                discovered = True
            if not evidence_ids:
                discards.append(
                    {
                        "idea_id": str(local.get("id", "")),
                        "line_number": line_number,
                        "reason": "MANUAL_IDEA_NO_EVIDENCE_FOUND",
                    }
                )
                continue
        local["evidence_ids"] = evidence_ids
        try:
            idea = Idea(**local)
        except Exception as exc:
            raise ValueError(f"invalid idea at line {line_number}: {exc}") from exc
        if discovered:
            for eid in idea.evidence_ids:
                if idea.evidence_provenance.get(eid) is None:
                    idea.evidence_provenance[eid] = "synthetic"
        else:
            provenance_label = "reentry" if local.get("origin") == "reentry" else "seed"
            for eid in idea.evidence_ids:
                if idea.evidence_provenance.get(eid) is None:
                    idea.evidence_provenance[eid] = provenance_label
        ideas.append(idea)
    return ideas, discards


def load_tournament_payload(path: str) -> dict:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("invalid seed tournament payload")
    return payload


def _cohort_tokens(value: str) -> set[str]:
    stopwords = {
        "the", "and", "for", "with", "that", "this", "from", "into",
        "very", "small", "medium", "large", "urgent", "budget", "constraints",
    }
    tokens = re.findall(r"[a-z0-9]{3,}", value.lower())
    return {token for token in tokens if token not in stopwords}


def is_narrower_cohort(parent_cohort: str, child_cohort: str) -> bool:
    if not parent_cohort.strip() or not child_cohort.strip():
        return False
    parent = _cohort_tokens(parent_cohort)
    child = _cohort_tokens(child_cohort)
    if not parent or not child:
        return False
    if not parent.issubset(child):
        return False
    extra = child - parent
    return len(extra) >= 1


def derive_reentry_rows_from_parent(parent_payload: dict, *, require_narrow: bool) -> list[tuple[int, dict]]:
    if not require_narrow:
        raise ValueError("--seed-from requires --narrow")
    rows: list[tuple[int, dict]] = []
    parent_tournament_id = str(parent_payload.get("tournament_id", "")).strip()
    for index, state in enumerate(parent_payload.get("ideas", []), start=1):
        if not isinstance(state, dict):
            continue
        if state.get("terminal_verdict") != "INSUFFICIENT_EVIDENCE":
            continue
        parent_idea = state.get("idea") or {}
        parent_id = str(parent_idea.get("id", "")).strip()
        if not parent_id:
            continue
        parent_cohort = str(parent_idea.get("cohort", "")).strip()
        parent_evidence = [str(item) for item in parent_idea.get("evidence_ids", []) if str(item).strip()]
        parent_provenance: dict[str, str] = dict(parent_idea.get("evidence_provenance") or {})
        new_evidence = DemandSignal.build_signal_id(
            source_url=f"https://reentry.local/{parent_tournament_id}/{parent_id}",
            verbatim_quote=f"reentry evidence for {parent_id}",
        )
        rows.append(
            (
                index,
                {
                    "id": f"{parent_id}-reentry-{index}",
                    "label": str(parent_idea.get("label", "reentry idea")),
                    "anchor_slug": parent_idea.get("anchor_slug"),
                    "incumbent": parent_idea.get("incumbent"),
                    "cohort": f"{parent_cohort} with compliance constraints".strip(),
                    "pain_hypothesis": str(parent_idea.get("pain_hypothesis", "Need sharper evidence")),
                    "kill_condition": parent_idea.get("kill_condition"),
                    "evidence_ids": parent_evidence + [new_evidence],
                    "evidence_provenance": parent_provenance,
                    "search_queries": parent_idea.get("search_queries", []),
                    "origin": "reentry",
                    "gate_profile": parent_idea.get("gate_profile", parent_payload.get("gate_profile", "consumer_app")),
                    "gate_profile_source": "explicit",
                    "parent_idea_id": parent_id,
                },
            )
        )
    if not rows:
        raise ValueError("seed tournament has no INSUFFICIENT_EVIDENCE ideas to re-enter")
    return rows


def validate_reentry_rules(ideas: list[Idea], parent_payload: dict, *, player: PlayerProfile) -> None:
    parent_depth = int(parent_payload.get("reentry_depth", 0) or 0)
    if parent_depth >= player.max_reentry_rounds:
        raise ValueError("max_reentry_rounds reached for this player profile")

    parent_by_id: dict[str, dict] = {}
    for state in parent_payload.get("ideas", []):
        if not isinstance(state, dict):
            continue
        if state.get("terminal_verdict") != "INSUFFICIENT_EVIDENCE":
            continue
        idea = state.get("idea") or {}
        idea_id = str(idea.get("id", "")).strip()
        if idea_id:
            parent_by_id[idea_id] = idea

    for idea in ideas:
        if not idea.parent_idea_id:
            raise ValueError("reentry idea missing parent_idea_id")
        parent = parent_by_id.get(idea.parent_idea_id)
        if parent is None:
            raise ValueError("reentry parent_idea_id must reference an INSUFFICIENT_EVIDENCE parent")
        parent_cohort = str(parent.get("cohort", "")).strip()
        child_cohort = idea.cohort.strip()
        if not is_narrower_cohort(parent_cohort, child_cohort):
            raise ValueError("reentry cohort must be narrower than parent cohort")
        parent_evidence = {str(item) for item in parent.get("evidence_ids", [])}
        child_evidence = set(idea.evidence_ids)
        if not (child_evidence - parent_evidence):
            raise ValueError("reentry idea must include at least one new evidence_id")


def profile_confidence(gate_profile_source: str) -> float | None:
    raw = gate_profile_source.strip()
    if not raw.startswith("inferred:"):
        return None
    try:
        return float(raw.split(":", 1)[1])
    except ValueError:
        return None


def memo_to_markdown(memo: dict) -> str:
    lines = [
        "# Decision Memo",
        "",
        f"- tournament_id: {memo.get('tournament_id', '')}",
        f"- player_id: {memo.get('player_id', '')}",
        "",
        "## Winner",
    ]
    winner = memo.get("winner")
    if isinstance(winner, dict):
        idea = winner.get("idea", {})
        lines.append(f"- idea_id: {idea.get('id', '')}")
        lines.append(f"- label: {idea.get('label', '')}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Arguments",
            f"- for: {memo.get('strongest_argument_for', '')}",
            f"- against: {memo.get('strongest_argument_against', '')}",
            "",
            "## Missing Evidence",
        ]
    )
    for item in memo.get("missing_evidence_checklist", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Reality Spike")
    spike = memo.get("reality_spike")
    if isinstance(spike, dict):
        lines.append(f"- provenance: {spike.get('provenance', '')}")
        lines.append(f"- headline: {spike.get('landing_page_headline', '')}")
    else:
        lines.append("- none")
    if memo.get("zero_winner_diagnosis"):
        lines.extend(["", "## Zero Winner Diagnosis", str(memo["zero_winner_diagnosis"])])
    lines.append("")
    return "\n".join(lines)


def write_events_ndjson(path: Path, result_payload: dict) -> None:
    events = []
    for state in result_payload.get("ideas", []):
        idea = state.get("idea", {})
        for gate in state.get("gate_results", []):
            events.append({
                "schema_version": 1,
                "tournament_id": result_payload.get("tournament_id"),
                "idea_id": idea.get("id"),
                "gate_name": gate.get("gate_name"),
                "status": gate.get("status"),
                "outcome": gate.get("outcome"),
                "confidence": gate.get("confidence"),
                "llm_cost_usd": gate.get("llm_cost_usd"),
            })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
