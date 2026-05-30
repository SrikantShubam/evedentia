from pathlib import Path


FORBIDDEN_IMPORT_SNIPPETS = (
    "evidentia.scoring",
    "evidentia.critic",
    "evidentia.loop",
)


def test_production_code_has_no_legacy_pipeline_imports():
    for path in Path("src/evidentia").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_IMPORT_SNIPPETS:
            assert forbidden not in source, f"{path} still imports {forbidden}"
