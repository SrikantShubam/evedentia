from __future__ import annotations

import json

import pytest

from evidentia.anchor import load_all_anchors
from evidentia.cli import _run_hunt
from evidentia.providers import choose_llm_provider, load_external_provider_env


def _require_live_llm() -> dict[str, str]:
    env = load_external_provider_env()
    try:
        choose_llm_provider(env)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"live LLM provider not configured: {exc}")
    return env


@pytest.mark.live
def test_live_hunt_smoke(monkeypatch, tmp_path):
    env = _require_live_llm()
    monkeypatch.chdir(tmp_path)

    anchors = load_all_anchors()
    if not anchors:
        pytest.skip("no verifiable anchors available")
    anchor = next((item for item in anchors if item.slug == "bible-study-apps"), anchors[0])
    payload = _run_hunt(anchor, limit=5, dry_run=False, env=env)
    run_dir = tmp_path / payload["run_dir"]

    for filename in ("anchor.json", "signals.json", "slices.json", "verdicts.json", "discard_log.json", "summary.md"):
        assert (run_dir / filename).exists(), filename

    signals_payload = json.loads((run_dir / "signals.json").read_text(encoding="utf-8"))
    signals = signals_payload.get("signals") or []
    if not signals:
        pytest.skip("live hunt returned no signals")
    if not any(signal.get("proof_level") == "fetched" for signal in signals):
        pytest.skip("live hunt returned no fetched signals")
