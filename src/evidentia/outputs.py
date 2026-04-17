from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
import warnings

from evidentia.models import Anchor, DemandSignal, Slice, SliceVerdict


SCHEMA_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _check_mark(value: bool) -> str:
    return "✓" if value else "✗"


def _summary_markdown(anchor: Anchor, slices: list[Slice], verdicts: list[SliceVerdict], run_ts: str) -> str:
    verdict_by_slice = {verdict.slice_id: verdict for verdict in verdicts}
    pursue_count = sum(1 for verdict in verdicts if verdict.verdict == "PURSUE")
    refine_count = sum(1 for verdict in verdicts if verdict.verdict == "REFINE")
    kill_count = sum(1 for verdict in verdicts if verdict.verdict == "KILL")
    lines = [
        f"# {anchor.market_name} - {run_ts}",
        "",
        f"**Proof:** \"{anchor.proof_of_market.verbatim_quote}\" ({anchor.proof_of_market.proof_level})",
        f"**Slices:** {len(slices)} | **PURSUE:** {pursue_count} | **REFINE:** {refine_count} | **KILL:** {kill_count}",
        "",
    ]

    for slice_obj in slices:
        verdict = verdict_by_slice.get(slice_obj.slice_id)
        if verdict is None:
            continue
        gates = verdict.gates
        lines.append(f"## {verdict.verdict} - \"{slice_obj.label}\"")
        lines.append(f"- {slice_obj.author_count} distinct authors")
        lines.append(
            "- Gates: "
            f"market {_check_mark(gates.get('market_exists', False))} "
            f"voices {_check_mark(gates.get('slice_has_voices', False))} "
            f"underserved {_check_mark(gates.get('slice_underserved', False))} "
            f"reachable {_check_mark(gates.get('reachable', False))} "
            f"buildable {_check_mark(gates.get('buildable', False))}"
        )
        if verdict.refine_reason:
            lines.append(f"- Why: {verdict.refine_reason}")
        if verdict.next_test:
            lines.append(f"- Next test: {verdict.next_test}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_run(
    run_dir: Path,
    anchor: Anchor,
    signals: list[DemandSignal],
    slices: list[Slice],
    verdicts: list[SliceVerdict],
    discards: list[dict],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    run_ts = run_dir.name
    _write_json(run_dir / "anchor.json", {"schema_version": SCHEMA_VERSION, "anchor": _to_jsonable(anchor)})
    _write_json(run_dir / "signals.json", {"schema_version": SCHEMA_VERSION, "signals": _to_jsonable(signals)})
    _write_json(run_dir / "slices.json", {"schema_version": SCHEMA_VERSION, "slices": _to_jsonable(slices)})
    _write_json(run_dir / "verdicts.json", {"schema_version": SCHEMA_VERSION, "verdicts": _to_jsonable(verdicts)})
    _write_json(run_dir / "discard_log.json", {"schema_version": SCHEMA_VERSION, "discards": _to_jsonable(discards)})
    (run_dir / "summary.md").write_text(_summary_markdown(anchor, slices, verdicts, run_ts), encoding="utf-8")


def _load_slice_metadata(run_dir: Path) -> dict[str, dict[str, Any]]:
    path = run_dir / "slices.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    rows = payload.get("slices") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return {}
    metadata: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        slice_id = str(row.get("slice_id", "")).strip()
        if not slice_id:
            continue
        metadata[slice_id] = {
            "label": str(row.get("label", "")).strip(),
            "author_count": int(row.get("author_count", 0) or 0),
        }
    return metadata


def append_to_index(index_path: Path, verdicts: list[SliceVerdict], anchor: Anchor, run_dir: Path) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    slice_metadata = _load_slice_metadata(run_dir)
    for verdict in verdicts:
        details = slice_metadata.get(verdict.slice_id, {})
        payload = {
            "schema_version": SCHEMA_VERSION,
            "ts": _utc_now(),
            "anchor_slug": anchor.slug,
            "slice_id": verdict.slice_id,
            "label": details.get("label", ""),
            "verdict": verdict.verdict,
            "author_count": details.get("author_count", 0),
            "gates": verdict.gates,
            "next_test": verdict.next_test,
            "run_dir": str(run_dir).replace("\\", "/"),
        }
        with index_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_index(index_path: Path) -> list[dict]:
    if not index_path.exists():
        return []
    rows: list[dict] = []
    for line_number, raw_line in enumerate(index_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            parsed = json.loads(raw_line)
        except json.JSONDecodeError:
            warnings.warn(f"malformed index line skipped at {index_path}:{line_number}", RuntimeWarning)
            continue
        if not isinstance(parsed, dict):
            warnings.warn(f"non-object index line skipped at {index_path}:{line_number}", RuntimeWarning)
            continue
        rows.append(parsed)
    return rows


def _entry_sort_key(entry: dict) -> tuple[int, str]:
    author_count = int(entry.get("author_count", 0) or 0)
    ts = str(entry.get("ts", ""))
    return author_count, ts


def top_ideas(index_path: Path, verdict: str = "PURSUE", n: int = 20) -> list[dict]:
    entries = [row for row in read_index(index_path) if str(row.get("verdict")) == verdict]
    latest_by_slice: dict[str, dict] = {}
    for row in entries:
        slice_id = str(row.get("slice_id", "")).strip()
        if not slice_id:
            continue
        current = latest_by_slice.get(slice_id)
        if current is None or _entry_sort_key(row) >= _entry_sort_key(current):
            latest_by_slice[slice_id] = row
    ordered = sorted(latest_by_slice.values(), key=_entry_sort_key, reverse=True)
    return ordered[:n]
