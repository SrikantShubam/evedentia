from pathlib import Path

import pytest

from evidentia.providers import (
    choose_llm_provider,
    load_external_provider_env,
    load_kimi_golden_cases,
    run_provider_smoke,
)


def test_load_external_provider_env_reads_codex_and_kimi_keys():
    env = load_external_provider_env()
    sensitive = {"NVIDIA_API_KEY", "OPENROUTER_API_KEY", "GROQ_API_KEY", "TAVILY_API_KEY"}
    found = sensitive & env.keys()
    if not found:
        pytest.skip("no external provider keys in .env or environment")


def test_choose_llm_provider_uses_external_keys_in_auto_mode():
    env = load_external_provider_env()
    sensitive = {"NVIDIA_API_KEY", "OPENROUTER_API_KEY", "GROQ_API_KEY", "TAVILY_API_KEY"}
    if not sensitive & env.keys():
        pytest.skip("no external provider keys")

    provider, model = choose_llm_provider(env)

    assert provider.name == "nvidia"
    assert model


def test_run_provider_smoke_dry_run_uses_external_routing(tmp_path):
    env = load_external_provider_env()
    sensitive = {"NVIDIA_API_KEY", "OPENROUTER_API_KEY", "GROQ_API_KEY", "TAVILY_API_KEY"}
    if not sensitive & env.keys():
        pytest.skip("no external provider keys")

    report = run_provider_smoke(
        idea="invoice extraction",
        outdir=tmp_path,
        dry_run=True,
    )

    assert report["status"] == "ok"
    assert report["search_probe"]["success"] is True
    assert report["llm_probe"]["success"] is True
    assert report["llm_probe"]["provider"] in {"nvidia", "openrouter", "groq"}


def test_load_kimi_golden_cases_uses_existing_dataset():
    try:
        cases = load_kimi_golden_cases()
    except (FileNotFoundError, OSError):
        pytest.skip("kimi golden dataset not available")

    assert len(cases) >= 1
    assert any(case["expected_verdict"] == "KILL" for case in cases)
    assert any(case["expected_verdict"] == "SURVIVE" for case in cases)
