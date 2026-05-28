from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidentia.providers import build_llm_provider_chain, choose_llm_provider, load_external_provider_env


REQUIRED_KEYS = {
    "willingness_to_pay",
    "distribution_channel",
    "data_feasibility",
    "competition_gap",
    "buildability",
    "reachability_strength",
}

_GATE_KEYS = ("willingness_to_pay", "distribution_channel", "data_feasibility")
_HEURISTIC_KEYS = ("competition_gap", "buildability", "reachability_strength")


class ClassifierError(RuntimeError):
    def __init__(self, message: str, last_raw_response: Any = None):
        super().__init__(message)
        self.last_raw_response = last_raw_response


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


def _derive_complaint_type(candidate: dict) -> tuple[str, str | None]:
    text = " ".join(str(candidate.get(key, "")).lower() for key in ("title", "verbatim_quote", "source_text"))
    mapping = [
        (("ad", "ads"), "ADS"),
        (("billing", "charged", "refund"), "BILLING_ABUSE"),
        (("not for women", "excluded", "cohort"), "NICHE_EXCLUSION"),
        (("privacy", "trust", "tracking"), "TRUST_PRIVACY"),
        (("friction", "slow", "manual"), "WORKFLOW_FRICTION"),
        (("bloated", "too many features"), "FEATURE_BLOAT"),
        (("support", "no response"), "SUPPORT_FAILURE"),
        (("localization", "language", "region"), "LOCALIZATION"),
        (("lock-in", "locked in", "export"), "PLATFORM_LOCK_IN"),
        (("missing", "wish it had", "should add"), "MISSING_FEATURE"),
        (("broken", "bug", "doesn't work"), "BROKEN_FEATURE"),
        (("expensive", "pricing", "paywall"), "PRICING"),
        (("confusing", "hard to use", "ux", "ui"), "UX"),
        (("alternative", "switching", "replace"), "SCOPE_MISMATCH"),
    ]
    for tokens, label in mapping:
        if any(token in text for token in tokens):
            return label, None
    return "UNKNOWN_WITH_REASON", "No complaint taxonomy match from deterministic text patterns."


def _derive_additional_tasks(candidate: dict, normalized: dict) -> dict:
    text = " ".join(str(candidate.get(key, "")).lower() for key in ("title", "verbatim_quote", "source_text"))
    complaint_type, complaint_reason = _derive_complaint_type(candidate)
    cohort_fit = "pass" if any(token in text for token in ("women", "teams", "developers", "agencies")) else "unknown"
    spend_signal = any(token in text for token in ("pay", "budget", "price", "subscription"))
    player_fit = "pass" if normalized["buildability"] >= 0.6 and normalized["reachability_strength"] >= 0.5 else "fail"
    return {
        "complaint_type": complaint_type,
        "complaint_type_reason": complaint_reason,
        "cohort_fit": cohort_fit,
        "spend_signal": spend_signal,
        "player_fit": player_fit,
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


def _validate_classification_shape(raw: dict) -> list[str]:
    violations: list[str] = []
    if not isinstance(raw, dict):
        return ["response must be a JSON object"]

    missing = sorted(REQUIRED_KEYS - set(raw.keys()))
    for key in missing:
        violations.append(f"missing key: {key}")

    for gate_key in _GATE_KEYS:
        if gate_key not in raw:
            continue
        if not isinstance(raw[gate_key], str):
            violations.append(f"{gate_key} must be a string")

    for score_key in _HEURISTIC_KEYS:
        if score_key not in raw:
            continue
        value = raw[score_key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            violations.append(f"{score_key} must be a number between 0 and 1")
            continue
        number = float(value)
        if number < 0.0 or number > 1.0:
            violations.append(f"{score_key} must be within [0, 1]")
    return violations


def _append_debug_log(
    debug_log_path: str | None,
    *,
    provider_name: str,
    model: str,
    prompt: str,
    raw_response: Any,
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
    log_path = Path(debug_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")


def _corrective_prompt(base_prompt: str, violations: list[str]) -> str:
    return (
        f"{base_prompt}\n\n"
        f"Your previous response was invalid: {', '.join(violations)}. "
        "Return ONLY the JSON object with exact keys and types specified."
    )


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
        candidates = [(provider, model or "default-model")]
    else:
        candidates = build_llm_provider_chain(runtime_env)

    base_prompt = _classification_prompt(candidate)
    last_raw_response: Any = None
    last_issue: Exception | str | None = None

    for resolved_provider, resolved_model in candidates:
        provider_name = getattr(resolved_provider, "name", resolved_provider.__class__.__name__)
        try:
            raw_response = resolved_provider.generate_json(
                prompt=base_prompt,
                model=resolved_model,
            )
            last_raw_response = raw_response
            violations = _validate_classification_shape(raw_response)
            prompt_used = base_prompt

            if violations:
                prompt_used = _corrective_prompt(base_prompt, violations)
                raw_response = resolved_provider.generate_json(
                    prompt=prompt_used,
                    model=resolved_model,
                )
                last_raw_response = raw_response
                violations = _validate_classification_shape(raw_response)

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

            normalized = _normalize_classification(raw_response)
            normalized = _apply_deterministic_gate_overrides(candidate, normalized)
            normalized.update(_derive_additional_tasks(candidate, normalized))
            _append_debug_log(
                debug_log_path,
                provider_name=provider_name,
                model=resolved_model,
                prompt=prompt_used,
                raw_response=raw_response,
                normalized=normalized,
            )
            return {**candidate, **normalized}
        except Exception as exc:  # noqa: BLE001
            last_issue = exc
            _append_debug_log(
                debug_log_path,
                provider_name=provider_name,
                model=resolved_model,
                prompt=base_prompt,
                raw_response={"error": str(exc)},
                normalized=None,
            )
            continue

    if provider is None and provider_chain is None:
        try:
            resolved_provider, resolved_model = choose_llm_provider(runtime_env)
            return classify_candidate(
                candidate,
                provider=resolved_provider,
                model=resolved_model,
                env=runtime_env,
                debug_log_path=debug_log_path,
            )
        except Exception as exc:  # noqa: BLE001
            last_issue = exc

    message = "classification failed after provider chain exhausted"
    if last_issue is not None:
        message = f"{message}: {last_issue}"
    raise ClassifierError(message, last_raw_response=last_raw_response)


# ---------------------------------------------------------------------------
# TASK 02: Public complaint taxonomy classifier (added per spec, existing
# _derive_complaint_type left intact per "DO NOT delete" rule)
# ---------------------------------------------------------------------------

def classify_complaint(text: str) -> tuple[str, str]:
    """Classify complaint text into ComplaintType using keyword/pattern matching.

    Returns (complaint_type_value, reason). Falls back to UNKNOWN_WITH_REASON.
    """
    if not text or not str(text).strip():
        return "UNKNOWN_WITH_REASON", "empty input text"

    t = " ".join(str(text).lower().split())

    mapping = [
        # Order matters: more specific / multi-word first
        (("not for women", "no option for", "excluded from", "only for men"), "NICHE_EXCLUSION"),
        (("too many ads", "ads everywhere", "sponsored content"), "ADS"),
        (("billing", "charged twice", "refund", "overcharged", "payment failed"), "BILLING_ABUSE"),
        (("privacy", "trust", "tracking my data", "data collection", "surveillance"), "TRUST_PRIVACY"),
        (("workflow friction", "too slow", "manual process", "time consuming"), "WORKFLOW_FRICTION"),
        (("bloated", "too many features", "feature bloat", "overwhelming ui"), "FEATURE_BLOAT"),
        (("support never", "no response from support", "customer service ignored"), "SUPPORT_FAILURE"),
        (("no support for", "language support", "non-english", "localization"), "LOCALIZATION"),
        (("locked in", "can't export", "vendor lock", "can't leave"), "PLATFORM_LOCK_IN"),
        (("wish it had", "should add", "missing feature", "needs", "lacks"), "MISSING_FEATURE"),
        (("broken", "bug", "crashes", "doesn't work", "not working"), "BROKEN_FEATURE"),
        (("too expensive", "paywall", "pricing", "overpriced", "subscription cost"), "PRICING"),
        (("confusing", "hard to use", "clunky", "unintuitive", "bad ux", "bad ui"), "UX"),
        (("looking for alternative", "switching", "replace this", "migrate from"), "SCOPE_MISMATCH"),
        # Single word fallbacks (lower priority, only if very specific context)
        (("ads", "advertising"), "ADS"),
    ]

    for tokens, label in mapping:
        if any(token in t for token in tokens):
            return label, ""

    return "UNKNOWN_WITH_REASON", "No complaint taxonomy match from deterministic text patterns."
