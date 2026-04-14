from pathlib import Path

from evidentia.providers import (
    choose_llm_provider,
    load_external_provider_env,
    load_kimi_golden_cases,
    run_provider_smoke,
)


def test_load_external_provider_env_reads_codex_and_kimi_keys():
    env = load_external_provider_env()

    assert "NVIDIA_API_KEY" in env
    assert "OPENROUTER_API_KEY" in env
    assert "GROQ_API_KEY" in env
    assert "TAVILY_API_KEY" in env


def test_choose_llm_provider_uses_external_keys_in_auto_mode():
    env = load_external_provider_env()

    provider, model = choose_llm_provider(env)

    assert provider.name == "nvidia"
    assert model


def test_run_provider_smoke_dry_run_uses_external_routing(tmp_path):
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
    cases = load_kimi_golden_cases()

    assert len(cases) >= 1
    assert any(case["expected_verdict"] == "KILL" for case in cases)
    assert any(case["expected_verdict"] == "SURVIVE" for case in cases)
