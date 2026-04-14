from __future__ import annotations

from evidentia.providers import build_llm_provider_chain, choose_llm_provider, load_external_provider_env


def _classification_prompt(candidate: dict) -> str:
    return (
        "Classify this demand signal into deterministic gate and heuristic fields. "
        "Return JSON only with keys: willingness_to_pay, distribution_channel, "
        "data_feasibility, competition_gap, buildability, reachability_strength.\n"
        f"Title: {candidate['title']}\n"
        f"Quote: {candidate['verbatim_quote']}\n"
        f"Source text: {candidate['source_text']}\n"
        "For gates, use only 'pass' or 'fail'. "
        "For heuristics, use numeric values between 0.0 and 1.0.\n"
    )


def _normalize_gate(value) -> str:
    normalized = str(value).strip().lower()
    if normalized in {"pass", "true", "yes", "high", "medium", "moderate", "direct"}:
        return "pass"
    return "fail"


def _normalize_score(value) -> float:
    if isinstance(value, (int, float)):
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


def classify_candidate(
    candidate: dict,
    provider=None,
    model: str | None = None,
    env: dict[str, str] | None = None,
    provider_chain: list[tuple[object, str]] | None = None,
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

    last_error: Exception | None = None
    for resolved_provider, resolved_model in candidates:
        try:
            classification = resolved_provider.generate_json(
                prompt=_classification_prompt(candidate),
                model=resolved_model,
            )
            return {**candidate, **_normalize_classification(classification)}
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue

    if last_error is not None:
        raise last_error
    resolved_provider, resolved_model = choose_llm_provider(runtime_env)
    classification = resolved_provider.generate_json(
        prompt=_classification_prompt(candidate),
        model=resolved_model,
    )
    return {**candidate, **_normalize_classification(classification)}
