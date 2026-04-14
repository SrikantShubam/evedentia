import os
import subprocess
import sys


def test_python_module_entrypoint_runs_cli():
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"

    result = subprocess.run(
        [sys.executable, "-m", "evidentia.cli", "--help"],
        cwd=".",
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert "scan" in result.stdout
