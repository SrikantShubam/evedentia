from __future__ import annotations

import pytest

from evidentia.anchor import load_all_anchors
from evidentia.loop import run_loop
from evidentia.providers import choose_llm_provider, load_external_provider_env


def _require_live_llm() -> dict[str, str]:
    env = load_external_provider_env()
    try:
        choose_llm_provider(env)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"live LLM provider not configured: {exc}")
    return env


@pytest.mark.live
def test_live_loop_smoke(monkeypatch, tmp_path):
    env = _require_live_llm()
    monkeypatch.chdir(tmp_path)

    anchors = load_all_anchors()
    selected = [anchor for anchor in anchors if anchor.slug in {"bible-study-apps", "smb-invoicing"}]
    if len(selected) < 2:
        pytest.skip("required live anchors unavailable")

    summary = run_loop(selected[:2], iterations=1, ideas_per_iter=2, env=env, max_llm_calls=8)
    index_path = tmp_path / summary["index_path"]
    if sum(summary["verdict_counts"].values()) == 0:
        pytest.skip("live loop produced no verdicts")

    assert index_path.exists()
    assert index_path.read_text(encoding="utf-8").strip()
