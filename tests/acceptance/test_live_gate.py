import pytest

from evidentia.deployer import ensure_live_tests_enabled


@pytest.mark.live
def test_live_retrieval_requires_explicit_env_flag(monkeypatch):
    monkeypatch.delenv("EVIDENTIA_RUN_LIVE_TESTS", raising=False)

    with pytest.raises(RuntimeError, match="live tests are disabled"):
        ensure_live_tests_enabled()


@pytest.mark.live
def test_live_retrieval_runs_only_when_enabled(monkeypatch):
    monkeypatch.setenv("EVIDENTIA_RUN_LIVE_TESTS", "1")

    ensure_live_tests_enabled()
