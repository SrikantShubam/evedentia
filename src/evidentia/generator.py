from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from evidentia.models import Anchor
from evidentia.providers import build_llm_provider_chain, choose_llm_provider, load_external_provider_env


IDEA_FIELDS = ("label", "cohort", "pain_hypothesis", "search_queries")


class GeneratorError(RuntimeError):
    def __init__(self, message: str, last_raw_response: Any = None):
        super().__init__(message)
        self.last_raw_response = last_raw_response


def _anchor_prompt(anchor: Anchor, count: int) -> str:
    return (
        "You are a niche hypothesis generator. Given a proven market and cohort hints, "
        f"propose {count} narrow product hypotheses that fit the pattern "
        '"[market] for [specific cohort with specific pain]". Each hypothesis must be a specific slice, '
        "not a generic variant.\n\n"
        f"Market: {anchor.market_name}\n"
        f"Incumbents: {', '.join(anchor.incumbents)}\n"
        f"Cohort hints: {', '.join(anchor.cohort_hints)}\n\n"
        'Return JSON: {"ideas": [{"label": "...", "cohort": "...", "pain_hypothesis": "...", '
        '"search_queries": ["...", "..."]}]}\n'
        "Constraints: label is a noun phrase <= 10 words. pain_hypothesis is one sentence. "
        "search_queries are 2-3 queries that would surface buyer voices for this slice.\n"
    )


def _pursue_prompt(pursue_entries: list[dict], count: int) -> str:
    examples = "\n".join(
        f"- {entry.get('label', '')} | anchor={entry.get('anchor_slug', '')} | next_test={entry.get('next_test', '')}"
        for entry in pursue_entries[:10]
    )
    return (
        "You are a niche hypothesis generator. Given previously successful PURSUE slices, "
        f"propose {count} adjacent hypotheses that preserve the successful pattern while targeting nearby cohorts or pains.\n\n"
        f"PURSUE seeds:\n{examples or '- (none)'}\n\n"
        'Return JSON: {"ideas": [{"label": "...", "cohort": "...", "pain_hypothesis": "...", '
        '"search_queries": ["...", "..."]}]}\n'
        "Constraints: label is a noun phrase <= 10 words. pain_hypothesis is one sentence. "
        "search_queries are 2-3 queries that would surface buyer voices for this slice.\n"
    )


def _validate_ideas_shape(raw: Any) -> list[str]:
    violations: list[str] = []
    if not isinstance(raw, dict):
        return ["response must be an object"]
    ideas = raw.get("ideas")
    if not isinstance(ideas, list):
        return ["ideas must be a list"]
    for index, item in enumerate(ideas):
        if not isinstance(item, dict):
            violations.append(f"ideas[{index}] must be an object")
            continue
        for field in IDEA_FIELDS:
            if field not in item:
                violations.append(f"ideas[{index}] missing key: {field}")
        if "search_queries" in item:
            queries = item.get("search_queries")
            if not isinstance(queries, list) or any(not isinstance(query, str) for query in queries):
                violations.append(f"ideas[{index}].search_queries must be list[str]")
    return violations


def _normalize_ideas(raw: dict, count: int) -> list[dict]:
    ideas = raw.get("ideas") if isinstance(raw, dict) else []
    normalized: list[dict] = []
    for item in ideas:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        cohort = str(item.get("cohort", "")).strip()
        pain_hypothesis = str(item.get("pain_hypothesis", "")).strip()
        queries = [str(query).strip() for query in item.get("search_queries", []) if str(query).strip()]
        if not label or not cohort or not pain_hypothesis:
            continue
        normalized.append(
            {
                "label": label,
                "cohort": cohort,
                "pain_hypothesis": pain_hypothesis,
                "search_queries": queries[:3],
            }
        )
        if len(normalized) >= count:
            break
    return normalized


def _infer_gate_profile(label: str, cohort: str, pain_hypothesis: str) -> tuple[str, float, str]:
    text = " ".join([label, cohort, pain_hypothesis]).lower()
    if any(token in text for token in ("extension", "chrome", "firefox", "browser")):
        return "browser_extension", 0.85, "store_category_not_saturated"
    if any(token in text for token in ("agency", "client work", "retainer")):
        return "agency_service", 0.86, "repeat_purchase_evidence"
    if any(token in text for token in ("workflow", "procurement", "finance team", "ops team", "b2b")):
        return "b2b_workflow", 0.82, "budget_owner_identifiable"
    return "consumer_app", 0.74, "complaint_signal_exists"


def _with_tournament_fields(
    ideas: list[dict],
    *,
    anchor: Anchor | None,
    origin: str,
    pursue_entries: list[dict] | None = None,
) -> list[dict]:
    enriched: list[dict] = []
    seed_anchor = None
    seed_parent = None
    seed_evidence: list[str] = []
    if pursue_entries:
        seed_anchor = pursue_entries[0].get("anchor_slug")
        seed_parent = pursue_entries[0].get("idea_id")
        seed_evidence = [str(item) for item in pursue_entries[0].get("evidence_ids", []) if str(item).strip()]
    for idea in ideas:
        profile, conf, kill_gate = _infer_gate_profile(idea["label"], idea["cohort"], idea["pain_hypothesis"])
        evidence_ids = seed_evidence or ([anchor.proof_of_market.signal_id] if anchor else [])
        if not evidence_ids:
            evidence_ids = [f"seed-{idea['label'].lower().replace(' ', '-')[:24]}"]
        enriched.append(
            {
                **idea,
                "kill_condition": {
                    "description": f"Fail if {kill_gate} does not pass.",
                    "gate_name": kill_gate,
                },
                "gate_profile": profile,
                "gate_profile_source": f"inferred:{conf:.2f}",
                "evidence_ids": evidence_ids,
                "origin": origin,
                "anchor_slug": anchor.slug if anchor else seed_anchor,
                "incumbent": anchor.incumbents[0] if anchor and anchor.incumbents else None,
                "parent_idea_id": seed_parent if origin == "reentry" else None,
            }
        )
    return enriched


def _append_debug_log(
    debug_log_path: str | None,
    *,
    provider_name: str,
    model: str,
    prompt: str,
    raw_response: Any,
    normalized: list[dict] | None,
) -> None:
    if not debug_log_path:
        return
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider_name,
        "model": model,
        "prompt": prompt,
        "raw_response": raw_response,
        "normalized": normalized,
    }
    path = Path(debug_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _corrective_prompt(base_prompt: str, violations: list[str]) -> str:
    return (
        f"{base_prompt}\n\nYour previous response was invalid: {', '.join(violations)}. "
        "Return ONLY the JSON object with exact keys and types specified."
    )


def _generate_ideas(
    prompt: str,
    *,
    count: int,
    env: dict[str, str] | None = None,
    provider=None,
    model: str | None = None,
    provider_chain: list[tuple[object, str]] | None = None,
    debug_log_path: str | None = None,
) -> list[dict]:
    runtime_env = env or load_external_provider_env()
    if provider_chain is not None:
        candidates = provider_chain
    elif provider is not None and model is not None:
        candidates = [(provider, model)]
    elif provider is not None:
        candidates = [(provider, model or "default-model")]
    else:
        candidates = build_llm_provider_chain(runtime_env)

    last_raw_response: Any = None
    last_issue: Exception | str | None = None
    for resolved_provider, resolved_model in candidates:
        provider_name = getattr(resolved_provider, "name", resolved_provider.__class__.__name__)
        prompt_used = prompt
        try:
            raw_response = resolved_provider.generate_json(prompt=prompt_used, model=resolved_model)
            last_raw_response = raw_response
            violations = _validate_ideas_shape(raw_response)
            if violations:
                prompt_used = _corrective_prompt(prompt, violations)
                raw_response = resolved_provider.generate_json(prompt=prompt_used, model=resolved_model)
                last_raw_response = raw_response
                violations = _validate_ideas_shape(raw_response)
            if violations:
                last_issue = "; ".join(violations)
                _append_debug_log(
                    debug_log_path,
                    provider_name=provider_name,
                    model=resolved_model,
                    prompt=prompt_used,
                    raw_response=raw_response,
                    normalized=None,
                )
                continue
            normalized = _normalize_ideas(raw_response, count=count)
            _append_debug_log(
                debug_log_path,
                provider_name=provider_name,
                model=resolved_model,
                prompt=prompt_used,
                raw_response=raw_response,
                normalized=normalized,
            )
            return normalized
        except Exception as exc:  # noqa: BLE001
            last_issue = exc
            _append_debug_log(
                debug_log_path,
                provider_name=provider_name,
                model=resolved_model,
                prompt=prompt_used,
                raw_response={"error": str(exc)},
                normalized=None,
            )
            continue

    if provider is None and provider_chain is None:
        try:
            fallback_provider, fallback_model = choose_llm_provider(runtime_env)
            return _generate_ideas(
                prompt,
                count=count,
                env=runtime_env,
                provider=fallback_provider,
                model=fallback_model,
                debug_log_path=debug_log_path,
            )
        except Exception as exc:  # noqa: BLE001
            last_issue = exc

    message = "idea generation failed after provider chain exhausted"
    if last_issue is not None:
        message = f"{message}: {last_issue}"
    raise GeneratorError(message, last_raw_response=last_raw_response)


def generate_ideas_from_anchor(
    anchor: Anchor,
    count: int = 10,
    env: dict[str, str] | None = None,
    debug_log_path: str | None = None,
    provider=None,
    model: str | None = None,
    provider_chain: list[tuple[object, str]] | None = None,
) -> list[dict]:
    prompt = _anchor_prompt(anchor, count=count)
    ideas = _generate_ideas(
        prompt,
        count=count,
        env=env,
        debug_log_path=debug_log_path,
        provider=provider,
        model=model,
        provider_chain=provider_chain,
    )
    return _with_tournament_fields(ideas, anchor=anchor, origin="generator")


def generate_ideas_from_pursue(
    pursue_entries: list[dict],
    count: int = 10,
    env: dict[str, str] | None = None,
    debug_log_path: str | None = None,
    provider=None,
    model: str | None = None,
    provider_chain: list[tuple[object, str]] | None = None,
) -> list[dict]:
    prompt = _pursue_prompt(pursue_entries, count=count)
    ideas = _generate_ideas(
        prompt,
        count=count,
        env=env,
        debug_log_path=debug_log_path,
        provider=provider,
        model=model,
        provider_chain=provider_chain,
    )
    return _with_tournament_fields(ideas, anchor=None, origin="reentry", pursue_entries=pursue_entries)
