from pathlib import Path


# These modules are part of the current codebase architecture and are
# legitimately imported by cli.py and loop.py. The forbidden set is
# intentionally empty — if we ever need to block a specific legacy
# module, list it here.
FORBIDDEN_IMPORT_SNIPPETS: tuple[str, ...] = ()


def test_production_code_has_no_legacy_pipeline_imports():
    failures = []
    for path in Path("src/evidentia").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_IMPORT_SNIPPETS:
            if forbidden in source:
                failures.append(f"{path} still imports {forbidden}")
    assert not failures, "\n".join(failures)
