from pathlib import Path
import re


PATTERN = re.compile(r"\b(random\.|uuid4\()\b")


def test_no_random_or_uuid4_in_src():
    root = Path(__file__).resolve().parents[2] / "src" / "evidentia"
    violations: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if "# deterministic-ok" in line:
                continue
            if PATTERN.search(line):
                violations.append(f"{path}:{line_no}")
    assert not violations, "Found forbidden random/uuid4 usage:\n" + "\n".join(violations)
