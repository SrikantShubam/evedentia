from pathlib import Path


def empty_metrics() -> dict:
    return {"visits": 0, "signups": 0, "revenue_proxy": 0}


def load_metrics(path: str) -> dict:
    import json

    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_metrics(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")
