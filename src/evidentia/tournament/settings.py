from __future__ import annotations

import os


SHORTLIST_CONFIDENCE_THRESHOLD = float(os.environ.get("EVIDENTIA_SHORTLIST_CONFIDENCE_THRESHOLD", "0.85"))
CONFIDENCE_FLOOR = float(os.environ.get("EVIDENTIA_CONFIDENCE_FLOOR", "0.5"))
CONFIDENCE_CEIL = float(os.environ.get("EVIDENTIA_CONFIDENCE_CEIL", "0.95"))
