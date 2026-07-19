from pathlib import Path
import re


BANNED_PHRASES: list[re.Pattern] = [
    re.compile(r"will succeed"),
    re.compile(r"guaranteed"),
    re.compile(r"definitely"),
    re.compile(r"100%"),
    re.compile(r"proven winner"),
    re.compile(r"Success Probability"),
    re.compile(r"Prediction"),
]


def test_no_overconfident_language_in_src():
    root = Path(__file__).resolve().parents[2] / "src" / "evidentia"
    violations: list[str] = []
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pattern in BANNED_PHRASES:
                if pattern.search(line):
                    violations.append(f"{path}:{line_no}: {pattern.pattern!r}")
    assert not violations, (
        "Found banned overconfident phrases (use evidence-based alternatives):\n"
        + "\n".join(violations)
    )
