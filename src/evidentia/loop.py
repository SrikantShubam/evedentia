from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter

from evidentia.clusterer import cluster_signals
from evidentia.critic import critique_slice
from evidentia.generator import generate_ideas_from_anchor, generate_ideas_from_pursue
from evidentia.models import Anchor
from evidentia.outputs import append_to_index, top_ideas, write_run
from evidentia.scanners.reviews import listen_for_idea


class BudgetExhausted(RuntimeError):
    pass


def _safe_run_timestamp(now: datetime | None = None) -> str:
    instant = now or datetime.now(timezone.utc)
    return instant.strftime("%Y-%m-%dT%H-%M-%SZ")


def _index_path() -> Path:
    return Path("outputs") / "best_ideas.jsonl"


def _append_debug(debug_log_path: str | None, payload: dict) -> None:
    if not debug_log_path:
        return
    path = Path(debug_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _consume_budget(state: dict, max_llm_calls: int | None) -> None:
    if max_llm_calls is not None and state["llm_calls"] >= max_llm_calls:
        raise BudgetExhausted(f"max LLM calls reached: {max_llm_calls}")
    state["llm_calls"] += 1


def run_loop(
    anchors: list[Anchor],
    iterations: int = 10,
    ideas_per_iter: int = 10,
    env: dict[str, str] | None = None,
    *,
    max_llm_calls: int | None = None,
    stop_on_first_pursue: bool = False,
    debug_log_path: str | None = None,
) -> dict:
    """
    Returns a summary dict with counts per verdict and total runtime.
    Appends to outputs/best_ideas.jsonl and writes per-anchor run dirs.
    """
    runtime_env = dict(env or {})
    index_path = _index_path()
    verdict_counts = {"KILL": 0, "REFINE": 0, "PURSUE": 0}
    state = {"llm_calls": 0}
    seeded_ideas: list[dict] = []
    started_at = perf_counter()
    completed_iterations = 0
    stopped_reason = "max_iterations"
    stop_now = False

    try:
        for iteration in range(1, iterations + 1):
            for anchor in anchors:
                _consume_budget(state, max_llm_calls=max_llm_calls)
                ideas = generate_ideas_from_anchor(anchor, count=ideas_per_iter, env=runtime_env)
                if seeded_ideas:
                    ideas = ideas + seeded_ideas

                for idea_index, idea in enumerate(ideas, start=1):
                    signals = listen_for_idea(anchor, idea, limit=ideas_per_iter * 5, env=runtime_env)
                    if not signals:
                        continue
                    slices = cluster_signals(anchor, signals)
                    if not slices:
                        continue

                    signals_by_id = {signal.signal_id: signal for signal in signals}
                    verdicts = []
                    for slice_obj in slices:
                        verdict = critique_slice(slice_obj, signals_by_id, anchor, env=runtime_env)
                        verdicts.append(verdict)
                        verdict_counts[verdict.verdict] = verdict_counts.get(verdict.verdict, 0) + 1

                    run_dir = (
                        Path("outputs")
                        / "hunts"
                        / anchor.slug
                        / f"{_safe_run_timestamp()}-iter{iteration:02d}-idea{idea_index:02d}"
                    )
                    write_run(run_dir, anchor, signals, slices, verdicts, discards=[])
                    append_to_index(index_path, verdicts, anchor, run_dir)

                    if stop_on_first_pursue and any(verdict.verdict == "PURSUE" for verdict in verdicts):
                        stopped_reason = "stop_on_first_pursue"
                        stop_now = True
                        break
                if stop_now:
                    break
            completed_iterations = iteration
            if stop_now:
                break

            pursues = top_ideas(index_path, verdict="PURSUE", n=5)
            if pursues:
                _consume_budget(state, max_llm_calls=max_llm_calls)
                seeded_ideas = generate_ideas_from_pursue(pursues, count=ideas_per_iter, env=runtime_env)
            else:
                seeded_ideas = []

            _append_debug(
                debug_log_path,
                {
                    "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "iteration": iteration,
                    "llm_calls": state["llm_calls"],
                    "verdict_counts": verdict_counts,
                },
            )
    except KeyboardInterrupt:
        stopped_reason = "keyboard_interrupt"
    except BudgetExhausted:
        stopped_reason = "budget_exhausted"
        _append_debug(
            debug_log_path,
            {
                "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "event": "budget_exhausted",
                "llm_calls": state["llm_calls"],
                "max_llm_calls": max_llm_calls,
            },
        )
        raise

    elapsed = perf_counter() - started_at
    return {
        "iterations_completed": completed_iterations,
        "runtime_seconds": round(elapsed, 3),
        "verdict_counts": verdict_counts,
        "llm_calls": state["llm_calls"],
        "stopped_reason": stopped_reason,
        "index_path": str(index_path).replace("\\", "/"),
    }
