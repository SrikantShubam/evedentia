from pathlib import Path

import pytest


@pytest.mark.xfail(reason="api.py reuses _run_hunt from cli.py; needs extraction to shared module")
def test_api_module_does_not_import_cli_internals():
    api_source = Path("src/evidentia/api.py").read_text(encoding="utf-8")
    assert "evidentia.cli" not in api_source
