try:
    import tomllib as _toml
except ModuleNotFoundError:
    import tomli as _toml  # type: ignore[no-redef]

from pathlib import Path


SERVER_PACKAGES = ("fastapi", "uvicorn", "sse-starlette")
# pydantic is a core dep, not a server-only dep


def _find_dep(package: str, deps: list[str]) -> bool:
    """Check if a package is listed as a dependency.

    Handles 'package>=1.0' and 'package[extra]>=1.0' formats.
    """
    return any(
        dep == package
        or dep.startswith(f"{package}=")
        or dep.startswith(f"{package}>")
        or dep.startswith(f"{package} [")
        or dep.startswith(f"{package}[")
        for dep in deps
    )


def test_server_dependencies_are_in_core_deps():
    """Server deps are currently listed as core dependencies in pyproject.toml.

    This is the current state of the project. If server deps are later moved
    to optional-dependencies, update this test accordingly.
    """
    pyproject = _toml.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]

    for package in SERVER_PACKAGES:
        assert _find_dep(package, dependencies), (
            f"{package} should be in core dependencies"
        )


def test_optional_dependencies_have_dev_group():
    """At minimum, a 'dev' optional-dependencies group exists."""
    pyproject = _toml.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    opt_deps = pyproject["project"].get("optional-dependencies", {})
    assert "dev" in opt_deps, "optional-dependencies should have a 'dev' group"
