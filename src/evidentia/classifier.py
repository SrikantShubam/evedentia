from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from evidentia.providers import build_llm_provider_chain, choose_llm_provider, load_external_provider_env


def _classification_prompt(candidate: dict) -> str:
    source_text = str(candidate.get("source_text", ""))[:900]
    return (
        "You are a demand-signal classifier. Return ONLY a JSON object. No markdown, no notes, no additional keys.\n\n"
        "REQUIRED OUTPUT FORMAT - fill in your assessed values, do not copy these placeholders:\n"
        '{"willingness_to_pay": "<pass|fail>", "distribution_channel": "<pass|fail>", "data_feasibility": "<pass|fail>", '
        '"competition_gap": <0.0-1.0>, "buildability": <0.0-1.0>, "reachability_strength": <0.0-1.0>}\n\n'
        "RULES:\n"
        '- willingness_to_pay, distribution_channel, data_feasibility: MUST be the string "pass" or the string "fail". No other values.\n'
        "- competition_gap, buildability, reachability_strength: MUST be a number between 0.0 and 1.0.\n"
        "- Do NOT add additional keys, nested objects, or reasoning fields.\n\n"
        "CLASSIFY THIS SIGNAL:\n"
        f"Title: {candidate.get('title', '')}\n"
        f"Quote: {candidate.get('verbatim_quote', '')}\n"
        f"Source body: {source_text}\n"
    )


def _normalize_gate(value) -> str:
    normalized = str(value).strip().lower()
    pass_labels = {
        "pass",
        "true",
        "yes",
        "1",
        "1.0",
        "high",
        "medium",
        "moderate",
        "direct",
        "strong",
        "clear",
        "evident",
        "present",
        "confirmed",
        "explicit",
    }
    if normalized in pass_labels:
        return "pass"
    try:
        if float(normalized) >= 0.5:
            return "pass"
    except ValueError:
        pass
    return "fail"


def _normalize_score(value) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return max(0.0, min(1.0, float(value)))

    normalized = str(value).strip().lower()
    mapping = {
        "high": 1.0,
        "medium": 0.6,
        "moderate": 0.6,
        "low": 0.2,
        "pass": 1.0,
        "fail": 0.0,
    }
    if normalized in mapping:
        return mapping[normalized]
    try:
        return max(0.0, min(1.0, float(normalized)))
    except ValueError:
        return 0.0


def _normalize_classification(classification: dict) -> dict:
    return {
        "willingness_to_pay": _normalize_gate(classification.get("willingness_to_pay", "fail")),
        "distribution_channel": _normalize_gate(classification.get("distribution_channel", "fail")),
        "data_feasibility": _normalize_gate(classification.get("data_feasibility", "fail")),
        "competition_gap": _normalize_score(classification.get("competition_gap", 0.0)),
        "buildability": _normalize_score(classification.get("buildability", 0.0)),
        "reachability_strength": _normalize_score(classification.get("reachability_strength", 0.0)),
    }


_TESTER_RECRUITMENT_PATTERNS = (
    re.compile(r"\bneed\s+\d+\s+testers?\b"),
    re.compile(r"\bneed\s+testers?\b"),
    re.compile(r"\blooking\s+for\s+testers?\b"),
    re.compile(r"\bclosed[-\s]?testers?\b"),
    re.compile(r"\b(beta|alpha)\s+testers?\b"),
    re.compile(r"\btest\s+back\b"),
    re.compile(r"\btest\s+my\s+app\b"),
)


def _is_tester_recruitment_signal(candidate: dict) -> bool:
    text_blob = " ".join(
        str(candidate.get(key, "")).lower()
        for key in ("title", "verbatim_quote", "source_text", "source_url")
    )
    if "testerscommunity" in text_blob:
        return True
    return any(pattern.search(text_blob) for pattern in _TESTER_RECRUITMENT_PATTERNS)


def _apply_deterministic_gate_overrides(candidate: dict, classification: dict) -> dict:
    normalized = dict(classification)
    if _is_tester_recruitment_signal(candidate):
        normalized["willingness_to_pay"] = "fail"
    return normalized


def _append_debug_log(
    debug_log_path: str | None,
    *,
    provider_name: str,
    model: str,
    prompt: str,
    raw_response,
    normalized: dict | None,
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
        fh.write(json.dumps(payload) + "\n")


def classify_candidate(
    candidate: dict,
    provider=None,
    model: str | None = None,
    env: dict[str, str] | None = None,
    provider_chain: list[tuple[object, str]] | None = None,
    debug_log_path: str | None = None,
) -> dict:
    runtime_env = env or load_external_provider_env()
    if provider_chain is not None:
        candidates = provider_chain
    elif provider is not None and model is not None:
        candidates = [(provider, model)]
    elif provider is not None:
        resolved_provider, resolved_model = provider, model or "default-model"
        candidates = [(resolved_provider, resolved_model)]
    else:
        candidates = build_llm_provider_chain(runtime_env)

    prompt = _classification_prompt(candidate)
    last_error: Exception | None = None
    for resolved_provider, resolved_model in candidates:
        provider_name = getattr(resolved_provider, "name", resolved_provider.__class__.__name__)
        try:
            classification = resolved_provider.generate_json(prompt=prompt, model=resolved_model)
            normalized = _normalize_classification(classification)
            normalized = _apply_deterministic_gate_overrides(candidate, normalized)
            _append_debug_log(
                debug_log_path,
                provider_name=provider_name,
                model=resolved_model,
                prompt=prompt,
                raw_response=classification,
                normalized=normalized,
            )
            return {**candidate, **normalized}
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _append_debug_log(
                debug_log_path,
                provider_name=provider_name,
                model=resolved_model,
                prompt=prompt,
                raw_response={"error": str(exc)},
                normalized=None,
            )
            continue

    if last_error is not None:
        raise last_error

    resolved_provider, resolved_model = choose_llm_provider(runtime_env)
    classification = resolved_provider.generate_json(prompt=prompt, model=resolved_model)
    normalized = _normalize_classification(classification)
    normalized = _apply_deterministic_gate_overrides(candidate, normalized)
    _append_debug_log(
        debug_log_path,
        provider_name=getattr(resolved_provider, "name", resolved_provider.__class__.__name__),
        model=resolved_model,
        prompt=prompt,
        raw_response=classification,
        normalized=normalized,
    )
    return {**candidate, **normalized}
