from pathlib import Path

REQUIRED_METRICS = ("visits", "signups", "revenue_proxy")


def empty_metrics() -> dict:
    return {"visits": 0, "signups": 0, "revenue_proxy": 0}


def _normalize_metrics_payload(payload: dict) -> dict:
    nested_report = "metrics" in payload
    metrics = payload.get("metrics", payload)
    if not isinstance(metrics, dict):
        raise ValueError("metrics payload must be an object")

    missing = [name for name in REQUIRED_METRICS if name not in metrics]
    if missing and not nested_report:
        raise ValueError(f"missing required metrics: {', '.join(missing)}")

    normalized_metrics: dict[str, int | float] = {}
    for name in REQUIRED_METRICS:
        if name in missing:
            continue
        value = metrics[name]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"metric {name} must be numeric")
        normalized_metrics[name] = value

    preserved_missing = payload.get("missing_fields", [])
    if not isinstance(preserved_missing, list):
        raise ValueError("missing_fields must be a list")

    return {
        "status": payload.get("status", "ok"),
        "proof_level": payload.get("proof_level", "unspecified"),
        "metrics": normalized_metrics,
        "missing_fields": preserved_missing or missing,
    }


def load_metrics(path: str) -> dict:
    import json

    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return _normalize_metrics_payload(payload)


def save_metrics(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")
