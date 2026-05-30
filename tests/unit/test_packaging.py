try:
    import tomllib as _toml
except ModuleNotFoundError:
    import tomli as _toml  # type: ignore[no-redef]

from pathlib import Path


def test_server_dependencies_are_optional():
    pyproject = _toml.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]
    server_dependencies = pyproject["project"]["optional-dependencies"]["server"]

    for package in ("fastapi", "uvicorn", "sse-starlette", "pydantic"):
        assert not any(dep.startswith(package) for dep in dependencies)
        assert any(dep.startswith(package) for dep in server_dependencies)
