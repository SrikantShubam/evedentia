import json
import re
from pathlib import Path
from datetime import datetime, timezone

import click

from evidentia.anchor import AnchorVerificationError, anchors_root, load_all_anchors, load_anchor, verify_anchor
from evidentia.auditor import verify_quote
from evidentia.clusterer import cluster_signals
from evidentia.classifier import classify_candidate
from evidentia.critic import critique_slice
from evidentia.generator import generate_ideas_from_anchor, generate_ideas_from_pursue
from evidentia.models import Anchor, DemandSignal
from evidentia.outputs import append_to_index, top_ideas as top_index_ideas, write_run
from evidentia.providers import ProviderError, load_external_provider_env
from evidentia.scanners import FIXTURE_SCANNERS
from evidentia.scanners.github import scan_github_live
from evidentia.scanners.hn import scan_hn_fixture, scan_hn_live
from evidentia.scanners.reddit import scan_reddit_live
from evidentia.scanners.reviews import listen
from evidentia.scoring import (
    dedupe_by_cluster,
    dedupe_by_content_fingerprint,
    rank_opportunities,
    score_opportunity,
)


_REJECT_PATTERNS = (
    (re.compile(r"\bneed\s+\d+\s+testers?\b"), "reject_tester_recruitment"),
    (re.compile(r"\btest\s+back\b"), "reject_tester_recruitment"),
    (re.compile(r"\bwhat if\b.*\?"), "reject_speculative_discussion"),
    (re.compile(r"\b(any advice|tips on|how do i)\b"), "reject_personal_advice_thread"),
)

_INCUMBENT_FRICTION_PATTERNS = (
    re.compile(r"\bnone of (them|these)\b"),
    re.compile(r"\bgetting worse\b"),
    re.compile(r"\btime for a change\b"),
    re.compile(r"\bmaking it more difficult\b"),
    re.compile(r"\bless user focused\b"),
    re.compile(r"\bexpensive for what you get\b"),
    re.compile(r"\bwe ended up doing\b"),
    re.compile(r"\bbuilding something internally\b"),
    re.compile(r"\bby hand\b"),
    re.compile(r"\bmanual(?:ly)?\b"),
    re.compile(r"\bstill doing\b"),
)

_BUYER_EVIDENCE_PATTERNS = (
    re.compile(r"\bwould pay\b"),
    re.compile(r"\bpaying\b"),
    re.compile(r"\bbudget\b"),
    re.compile(r"\bsubscription price\b"),
    re.compile(r"\btime for a change\b"),
    re.compile(r"\bwe ended up doing\b"),
    re.compile(r"\bbuilding something internally\b"),
)

_PERSONAL_LIFE_MARKERS = (
    "wife and i",
    "husband and i",
    "kids",
    "housing",
    "retirement",
    "smart money",
    "start a family",
)

_SOLUTION_MARKETING_PATTERNS = (
    re.compile(r"\bapi for\b"),
    re.compile(r"\bhelps automate this process\b"),
    re.compile(r"\busing ocr technology\b"),
    re.compile(r"\bstructured data allows businesses\b"),
    re.compile(r"\bai-powered ocr\b"),
)

_SEMANTIC_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "they", "them", "their", "still", "doing", "into",
    "from", "have", "has", "had", "our", "your", "every", "week", "team", "tool", "workflow", "process",
    "need", "better", "keeps", "keep", "things", "would", "could", "should", "more", "less", "than",
}


@click.group()
def cli() -> None:
    """Evidentia — harsh critic for demand-signal ideas. Verdicts: KILL / REFINE / PURSUE."""


def _safe_run_timestamp(now: datetime | None = None) -> str:
    instant = now or datetime.now(timezone.utc)
    return instant.strftime("%Y-%m-%dT%H-%M-%SZ")


def _index_path() -> Path:
    return Path("outputs") / "best_ideas.jsonl"


def _run_dir(anchor_slug: str, now: datetime | None = None) -> Path:
    return Path("outputs") / "hunts" / anchor_slug / _safe_run_timestamp(now=now)


def _dry_run_signals(anchor: Anchor, limit: int) -> list[DemandSignal]:
    signals: list[DemandSignal] = []
    pain_templates = [
        ("missing_feature", "Wish it had better onboarding for this cohort"),
        ("pricing_complaint", "This is too expensive and locked behind a paywall"),
        ("switching_intent", "I am looking for an alternative and ready to switch"),
        ("cohort_exclusion", "This is not for women and feels excluded"),
        ("usability_complaint", "The UI is confusing and hard to use"),
    ]
    for index in range(1, min(limit, len(pain_templates)) + 1):
        subtype, pain = pain_templates[index - 1]
        quote = f"{anchor.market_name}: {pain}"
        source_url = f"https://www.reddit.com/r/{anchor.slug.replace('-', '')}/comments/dry{index}"
        signals.append(
            DemandSignal(
                signal_id=DemandSignal.build_signal_id(source_url, quote),
                source_url=source_url,
                verbatim_quote=quote,
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                title=f"{anchor.market_name} complaint {index}",
                source_text=quote,
                source_kind="dry_run",
                signal_subtype=subtype,
                author=f"dry_user_{index}",
                verified=True,
                proof_level="in_memory",
            )
        )
    return signals


def _anchor_files() -> list[Path]:
    root = anchors_root()
    return sorted(list(root.glob("*.yaml")) + list(root.glob("*.yml")))


def _load_anchor_by_slug(slug: str, *, should_verify: bool = True) -> Anchor:
    path = anchors_root() / f"{slug}.yaml"
    if not path.exists():
        raise click.ClickException(f"anchor not found: {slug}")
    anchor = load_anchor(path)
    if not should_verify:
        return anchor
    try:
        return verify_anchor(anchor)
    except AnchorVerificationError as exc:
        raise click.ClickException(str(exc)) from exc


def _run_hunt(anchor: Anchor, *, limit: int, dry_run: bool, env: dict[str, str] | None = None) -> dict:
    runtime_env = dict(env or {})
    if dry_run:
        runtime_env["EVIDENTIA_DRY_RUN"] = "1"
        signals = _dry_run_signals(anchor, limit=max(limit, 3))
    else:
        runtime_env.update(load_external_provider_env())
        signals = listen(anchor, limit=limit, env=runtime_env)

    slices = cluster_signals(anchor, signals)
    signals_by_id = {signal.signal_id: signal for signal in signals}
    verdicts = [critique_slice(slice_obj, signals_by_id, anchor, env=runtime_env) for slice_obj in slices]
    run_dir = _run_dir(anchor.slug)
    write_run(run_dir, anchor, signals, slices, verdicts, discards=[])
    append_to_index(_index_path(), verdicts, anchor, run_dir)
    return {
        "anchor_slug": anchor.slug,
        "run_dir": str(run_dir).replace("\\", "/"),
        "signal_count": len(signals),
        "slice_count": len(slices),
        "verdict_count": len(verdicts),
    }


def _ideas_from_source(anchor_slug: str | None, from_pursues: bool, count: int) -> list[dict]:
    if from_pursues:
        pursues = top_index_ideas(_index_path(), verdict="PURSUE", n=max(20, count * 2))
        return generate_ideas_from_pursue(pursues, count=count)
    if not anchor_slug:
        raise click.ClickException("--anchor is required unless --from-pursues is used")
    return generate_ideas_from_anchor(_load_anchor_by_slug(anchor_slug, should_verify=False), count=count)


def _print_best_table(rows: list[dict]) -> None:
    if not rows:
        click.echo("No ideas found.")
        return
    headers = ["verdict", "anchor", "author_count", "slice_id", "label"]
    widths = {header: len(header) for header in headers}
    normalized_rows: list[dict[str, str]] = []
    for row in rows:
        normalized = {
            "verdict": str(row.get("verdict", "")),
            "anchor": str(row.get("anchor_slug", "")),
            "author_count": str(row.get("author_count", "")),
            "slice_id": str(row.get("slice_id", "")),
            "label": str(row.get("label", "")),
        }
        normalized_rows.append(normalized)
        for header in headers:
            widths[header] = max(widths[header], len(normalized[header]))

    header_line = " | ".join(header.ljust(widths[header]) for header in headers)
    separator = "-+-".join("-" * widths[header] for header in headers)
    click.echo(header_line)
    click.echo(separator)
    for row in normalized_rows:
        click.echo(" | ".join(row[header].ljust(widths[header]) for header in headers))


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: str, payload: dict) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _pre_score_rejection_reason(candidate: dict) -> str | None:
    text_blob = " ".join(
        str(candidate.get(key, "")).lower()
        for key in ("title", "verbatim_quote", "source_text", "source_url")
    )
    if not text_blob.strip():
        return "reject_empty_signal"
    for pattern, reason in _REJECT_PATTERNS:
        if pattern.search(text_blob):
            return reason
    if sum(marker in text_blob for marker in _PERSONAL_LIFE_MARKERS) >= 2:
        return "reject_personal_life_planning"
    if "testerscommunity" in text_blob:
        return "reject_tester_recruitment"
    if str(candidate.get("source")) == "github" and len(str(candidate.get("source_text", "")).strip()) < 80:
        return "reject_low_context_issue"
    return None


def _infer_signal_type(candidate: dict) -> str:
    text_blob = " ".join(
        str(candidate.get(key, "")).lower()
        for key in ("title", "verbatim_quote", "source_text")
    )
    if "would pay" in text_blob or "budget" in text_blob:
        return "buyer_intent"
    if "feature request" in text_blob or "enhancement" in text_blob:
        return "feature_request"
    if "show hn" in text_blob or "launched" in text_blob:
        return "builder_announcement"
    return "pain_signal"


def _infer_actor_type(candidate: dict) -> str:
    text_blob = " ".join(
        str(candidate.get(key, "")).lower()
        for key in ("title", "verbatim_quote", "source_text")
    )
    if any(token in text_blob for token in ("team", "startup", "business", "company")):
        return "business_operator"
    if any(token in text_blob for token in ("developer", "engineer", "maintainer")):
        return "builder"
    if any(token in text_blob for token in ("freelancer", "creator", "founder")):
        return "individual_operator"
    return "unknown"


def _clean_title(title: str) -> str:
    cleaned = re.sub(r"^(show hn:|ask hn:)\s*", "", title, flags=re.IGNORECASE).strip()
    return cleaned or "Untitled signal"


def _parse_published_at(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _semantic_terms(*parts: str) -> set[str]:
    text = " ".join(part.lower() for part in parts if part)
    replacements = {
        "by hand": "manual",
        "manually": "manual",
        "follow-up": "followup",
        "follow up": "followup",
        "slipping": "slip",
        "slips": "slip",
        "collections": "collect",
        "collection": "collect",
        "payments": "payment",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    tokens = re.findall(r"[a-z0-9]{3,}", text)
    return {token for token in tokens if token not in _SEMANTIC_STOPWORDS}


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _generate_hypothesis(candidate: dict) -> dict:
    title = _clean_title(str(candidate.get("title", "")))
    text_blob = " ".join(
        str(candidate.get(key, "")).lower()
        for key in ("title", "verbatim_quote", "source_text")
    )
    actor_type = _infer_actor_type(candidate)
    actor_label = {
        "business_operator": "operators",
        "builder": "technical teams",
        "individual_operator": "independent operators",
        "unknown": "users",
    }[actor_type]

    if "agency" in text_blob:
        actor_label = "agencies"
    elif "developer" in text_blob or "engineer" in text_blob:
        actor_label = "engineering teams"

    if "show hn" in str(candidate.get("title", "")).lower() or "we built this" in text_blob:
        hypothesis_type = "builder_showcase"
        wedge_statement = f"Assess whether '{title}' reflects real buyer demand before treating it as an opportunity."
    elif any(pattern.search(text_blob) for pattern in _INCUMBENT_FRICTION_PATTERNS):
        hypothesis_type = "replacement_wedge"
        wedge_statement = f"Build a replacement wedge for {actor_label} around the workflow pain described in '{title}'."
    else:
        hypothesis_type = "workflow_tool"
        wedge_statement = f"Test whether {actor_label} have repeated workflow pain behind '{title}'."

    return {
        "hypothesis_type": hypothesis_type,
        "headline": title,
        "wedge_statement": wedge_statement,
        "actor_type": actor_type,
    }


def _prosecute_hypothesis(candidate: dict, hypothesis: dict) -> dict:
    text_blob = " ".join(
        str(candidate.get(key, "")).lower()
        for key in ("title", "verbatim_quote", "source_text", "source_url")
    )
    if _pre_score_rejection_reason(candidate):
        return {"status": "kill", "reason": "pre_score_rejectable_signal"}
    if ("show hn" in str(candidate.get("title", "")).lower() or "we built this" in text_blob) and not any(
        pattern.search(text_blob) for pattern in _BUYER_EVIDENCE_PATTERNS
    ):
        return {"status": "kill", "reason": "builder_showcase_without_buyer_evidence"}
    if any(pattern.search(text_blob) for pattern in _SOLUTION_MARKETING_PATTERNS) and not any(
        pattern.search(text_blob) for pattern in _BUYER_EVIDENCE_PATTERNS
    ):
        return {"status": "kill", "reason": "solution_marketing_without_buyer_evidence"}
    if hypothesis["hypothesis_type"] == "replacement_wedge":
        return {"status": "keep", "reason": "incumbent_friction_with_replacement_signal"}
    return {"status": "revise", "reason": "needs_more_clustered_evidence"}


def _cluster_candidate_view(opportunities: list[dict]) -> dict:
    representative = max(
        opportunities,
        key=lambda item: (float(item.get("score", 0.0)), _parse_published_at(item.get("published_at"))),
    )
    verified_signals: list[dict] = []
    seen_signals: set[tuple[str, str]] = set()
    text_parts: list[str] = []
    for item in opportunities:
        text_parts.append(str(item.get("title", "")))
        for signal in item.get("verified_signals", []):
            signal_key = (str(signal.get("source_url", "")), str(signal.get("verbatim_quote", "")))
            if signal_key in seen_signals:
                continue
            seen_signals.add(signal_key)
            verified_signals.append(signal)
            text_parts.append(str(signal.get("verbatim_quote", "")))

    return {
        "source": representative.get("observed_fields", {}).get("source", representative.get("source", "")),
        "source_url": representative.get("observed_fields", {}).get("source_url", representative.get("source_url", "")),
        "title": representative.get("title", ""),
        "verbatim_quote": " ".join(part for part in text_parts[1:4] if part),
        "source_text": " ".join(part for part in text_parts if part),
        "published_at": representative.get("published_at"),
        "verified_signals": verified_signals,
    }


def _semantic_cluster_groups(opportunities: list[dict]) -> list[list[dict]]:
    groups: list[dict] = []
    for opportunity in opportunities:
        terms = _semantic_terms(
            str(opportunity.get("title", "")),
            str(opportunity.get("source_text", "")),
            " ".join(str(signal.get("verbatim_quote", "")) for signal in opportunity.get("verified_signals", [])),
        )
        exact_cluster = str(opportunity.get("cluster_id", ""))
        matched_group = None
        best_score = 0.0
        for group in groups:
            if exact_cluster and exact_cluster in group["cluster_ids"]:
                matched_group = group
                break
            score = _jaccard_similarity(terms, group["terms"])
            if score > best_score:
                best_score = score
                matched_group = group
        if matched_group is None or best_score < 0.25 and exact_cluster not in matched_group["cluster_ids"]:
            groups.append({"items": [opportunity], "terms": set(terms), "cluster_ids": {exact_cluster}})
            continue
        matched_group["items"].append(opportunity)
        matched_group["terms"].update(terms)
        matched_group["cluster_ids"].add(exact_cluster)

    return [group["items"] for group in groups]


def _synthesize_clustered_opportunities(opportunities: list[dict]) -> tuple[list[dict], list[dict]]:
    if not opportunities:
        return [], []

    synthesized: list[dict] = []
    discard_log: list[dict] = []
    for items in _semantic_cluster_groups(opportunities):
        cluster_view = _cluster_candidate_view(items)
        representative = max(
            items,
            key=lambda item: (float(item.get("score", 0.0)), _parse_published_at(item.get("published_at"))),
        )
        cluster_id = "|".join(sorted({str(item.get("cluster_id", "")) for item in items if item.get("cluster_id")}))
        hypothesis = _generate_hypothesis(cluster_view)
        prosecution = _prosecute_hypothesis(cluster_view, hypothesis)
        if prosecution["status"] == "kill":
            discard_log.append(
                {
                    "source_url": cluster_view.get("source_url"),
                    "verbatim_quote": cluster_view.get("verbatim_quote"),
                    "reason": f"prosecutor:{prosecution['reason']}",
                }
            )
            continue

        merged = dict(representative)
        merged["cluster_id"] = cluster_id
        merged["title"] = hypothesis["headline"]
        merged["verified_signals"] = cluster_view["verified_signals"]
        merged["source_text"] = cluster_view["source_text"]
        merged["hypothesis"] = hypothesis
        merged["hypothesis_validation"] = prosecution
        merged["hypothesis_status"] = prosecution["status"]
        merged["hypothesis_reason"] = prosecution["reason"]
        merged["hypothesis_type"] = hypothesis["hypothesis_type"]
        merged["wedge_statement"] = hypothesis["wedge_statement"]
        synthesized.append(merged)

    return synthesized, discard_log


def _candidate_to_opportunity(
    index: int,
    candidate: dict,
    debug_log_path: str | None = None,
) -> tuple[dict | None, dict | None]:
    # Pre-score rejection is applied to live-scanned candidates before inference.
    if "willingness_to_pay" not in candidate:
        rejection_reason = _pre_score_rejection_reason(candidate)
        if rejection_reason:
            discard = {
                "source_url": candidate.get("source_url"),
                "verbatim_quote": candidate.get("verbatim_quote"),
                "reason": rejection_reason,
            }
            return None, discard

    verification = verify_quote(candidate)
    if not verification["verified"]:
        discard = {
            "source_url": candidate["source_url"],
            "verbatim_quote": candidate["verbatim_quote"],
            "reason": verification.get("discard_reason", verification.get("reason", "quote_not_verifiable")),
        }
        return None, discard

    verified_signal = {
        "source": candidate["source"],
        "source_url": candidate["source_url"],
        "verbatim_quote": candidate["verbatim_quote"],
        "published_at": candidate.get("published_at"),
    }
    enriched_candidate = candidate
    if "willingness_to_pay" not in candidate:
        enriched_candidate = classify_candidate(candidate, debug_log_path=debug_log_path)

    hypothesis = _generate_hypothesis(enriched_candidate)
    prosecution = _prosecute_hypothesis(enriched_candidate, hypothesis)
    if prosecution["status"] == "kill":
        discard = {
            "source_url": candidate.get("source_url"),
            "verbatim_quote": candidate.get("verbatim_quote"),
            "reason": f"prosecutor:{prosecution['reason']}",
        }
        return None, discard

    inferred_fields = {
        "signal_type": _infer_signal_type(enriched_candidate),
        "actor_type": _infer_actor_type(enriched_candidate),
        "willingness_to_pay": enriched_candidate["willingness_to_pay"],
        "distribution_channel": enriched_candidate["distribution_channel"],
        "data_feasibility": enriched_candidate["data_feasibility"],
        "competition_gap": enriched_candidate["competition_gap"],
        "buildability": enriched_candidate["buildability"],
        "reachability_strength": enriched_candidate["reachability_strength"],
    }
    opportunity = {
        "opportunity_id": f"opp_{index:03d}",
        "title": hypothesis["headline"],
        "cluster_id": enriched_candidate["cluster_id"],
        "verified_signals": [verified_signal],
        "willingness_to_pay": enriched_candidate["willingness_to_pay"],
        "distribution_channel": enriched_candidate["distribution_channel"],
        "data_feasibility": enriched_candidate["data_feasibility"],
        "competition_gap": enriched_candidate["competition_gap"],
        "buildability": enriched_candidate["buildability"],
        "reachability_strength": enriched_candidate["reachability_strength"],
        "published_at": enriched_candidate.get("published_at"),
        "hypothesis": hypothesis,
        "hypothesis_validation": prosecution,
        "observed_fields": {
            "source": enriched_candidate.get("source"),
            "source_url": enriched_candidate.get("source_url"),
            "verbatim_quote": enriched_candidate.get("verbatim_quote"),
            "published_at": enriched_candidate.get("published_at"),
        },
        "inferred_fields": inferred_fields,
    }
    opportunity.update(score_opportunity(opportunity))
    return opportunity, None


def _process_candidates(
    candidates: list[dict],
    debug_log_path: str | None = None,
) -> tuple[list[dict], list[dict]]:
    scored: list[dict] = []
    discard_log: list[dict] = []

    for index, candidate in enumerate(candidates, start=1):
        try:
            opportunity, discard = _candidate_to_opportunity(index, candidate, debug_log_path=debug_log_path)
        except KeyError as exc:
            discard_log.append(
                {
                    "source_url": candidate.get("source_url"),
                    "verbatim_quote": candidate.get("verbatim_quote"),
                    "reason": f"missing_candidate_field:{exc.args[0]}",
                }
            )
            continue
        if opportunity is not None:
            scored.append(opportunity)
        if discard is not None:
            discard_log.append(discard)

    return scored, discard_log


def run_fixture_scan(fixtures_by_source: dict[str, str], debug_log_path: str | None = None) -> dict:
    candidates = []
    for source, path in fixtures_by_source.items():
        candidates.extend(FIXTURE_SCANNERS[source](path))
    scored, discard_log = _process_candidates(candidates, debug_log_path=debug_log_path)
    synthesized, synthesis_discards = _synthesize_clustered_opportunities(scored)
    discard_log.extend(synthesis_discards)
    deduped = dedupe_by_cluster(synthesized)
    ranked = rank_opportunities(deduped)
    return {"opportunities": ranked, "discard_log": discard_log}


def _run_scan_fixture(fixture_path: str, debug_log_path: str | None = None) -> dict:
    return run_fixture_scan({"hn": fixture_path}, debug_log_path=debug_log_path)


def _run_live_source(source: str, domain: str, max_results: int) -> tuple[list[dict], dict]:
    if source == "hn":
        scanner = scan_hn_live
    elif source == "reddit":
        scanner = scan_reddit_live
    elif source == "github":
        scanner = scan_github_live
    else:
        raise click.ClickException(f"unsupported live source: {source}")

    try:
        candidates = scanner(domain, max_results=max_results)
    except ProviderError as exc:
        return [], {
            "source": source,
            "status": "transport_error",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "count": 0,
        }
    except (KeyError, TypeError, ValueError) as exc:
        return [], {
            "source": source,
            "status": "payload_error",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "count": 0,
        }

    return candidates, {"source": source, "status": "ok", "count": len(candidates)}


def run_live_scan(
    domain: str,
    sources: list[str] | None = None,
    max_results: int = 3,
    debug_log_path: str | None = None,
) -> dict:
    selected_sources = sources or ["hn"]
    candidates = []
    source_attempts = []
    for source in selected_sources:
        source_candidates, attempt = _run_live_source(source, domain, max_results)
        candidates.extend(source_candidates)
        source_attempts.append(attempt)
    if source_attempts and all(attempt["status"] != "ok" for attempt in source_attempts):
        raise click.ClickException("all live sources failed")
    scored, discard_log = _process_candidates(candidates, debug_log_path=debug_log_path)
    synthesized, synthesis_discards = _synthesize_clustered_opportunities(scored)
    discard_log.extend(synthesis_discards)
    deduped = dedupe_by_cluster(synthesized)
    deduped = dedupe_by_content_fingerprint(deduped)
    ranked = rank_opportunities(deduped)
    return {"opportunities": ranked, "discard_log": discard_log, "source_attempts": source_attempts}


@cli.command()
@click.option("--fixture", "fixture_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--live", "live_mode", is_flag=True, default=False)
@click.option("--domain", type=str)
@click.option("--sources", type=str, default="hn", show_default=True)
@click.option("--max-results", type=int, default=3, show_default=True)
@click.option("--debug-llm-log", type=click.Path(dir_okay=False))
@click.option("--output", "output_path", default="outputs/scan.json", show_default=True, type=click.Path(dir_okay=False))
def scan(
    fixture_path: str | None,
    live_mode: bool,
    domain: str | None,
    sources: str,
    max_results: int,
    debug_llm_log: str | None,
    output_path: str,
) -> None:
    """Run the scan stage."""
    should_run_live = live_mode or bool(domain)
    if should_run_live:
        if not domain:
            raise click.ClickException("--domain is required with --live")
        if debug_llm_log:
            payload = run_live_scan(
                domain,
                sources=[item.strip() for item in sources.split(",") if item.strip()],
                max_results=max_results,
                debug_log_path=debug_llm_log,
            )
        else:
            payload = run_live_scan(
                domain,
                sources=[item.strip() for item in sources.split(",") if item.strip()],
                max_results=max_results,
            )
    else:
        if not fixture_path:
            raise click.ClickException("--fixture is required unless --live is used")
        if debug_llm_log:
            payload = _run_scan_fixture(fixture_path, debug_log_path=debug_llm_log)
        else:
            payload = _run_scan_fixture(fixture_path)
    _write_json(output_path, payload)
    click.echo(output_path)


@cli.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False))
def audit(input_path: str, output_path: str) -> None:
    """Audit one candidate for quote verifiability."""
    candidate = _load_json(input_path)
    payload = verify_quote(candidate)
    _write_json(output_path, payload)
    click.echo(output_path)


@cli.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False))
@click.option("--debug-llm-log", type=click.Path(dir_okay=False))
def classify(input_path: str, output_path: str, debug_llm_log: str | None) -> None:
    """Classify one candidate with deterministic gate normalization."""
    candidate = _load_json(input_path)
    payload = classify_candidate(candidate, debug_log_path=debug_llm_log)
    _write_json(output_path, payload)
    click.echo(output_path)


@cli.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False))
def score(input_path: str, output_path: str) -> None:
    """Score one opportunity and return verdict metadata."""
    opportunity = _load_json(input_path)
    payload = score_opportunity(opportunity)
    _write_json(output_path, payload)
    click.echo(output_path)


@cli.group()
def anchor() -> None:
    """Manage market anchors."""


@anchor.command("list")
def anchor_list() -> None:
    """List all anchors from anchors/."""
    for path in _anchor_files():
        click.echo(path.stem)


@anchor.command("verify")
@click.argument("slug")
def anchor_verify(slug: str) -> None:
    """Verify one anchor by slug."""
    verified = _load_anchor_by_slug(slug)
    click.echo(json.dumps(verified.to_dict(), indent=2))


@cli.command("hunt")
@click.argument("slug")
@click.option("--limit", type=int, default=50, show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
def hunt_command(slug: str, limit: int, dry_run: bool) -> None:
    """Run one full validate pass for an anchor."""
    payload = _run_hunt(_load_anchor_by_slug(slug, should_verify=not dry_run), limit=limit, dry_run=dry_run)
    click.echo(json.dumps(payload, indent=2))


@cli.command("hunt-all")
@click.option("--limit", type=int, default=50, show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
def hunt_all_command(limit: int, dry_run: bool) -> None:
    """Run hunt for all verified anchors."""
    if dry_run:
        anchors = [load_anchor(path) for path in _anchor_files()]
    else:
        anchors = load_all_anchors()
    results = [_run_hunt(anchor, limit=limit, dry_run=dry_run) for anchor in anchors]
    click.echo(json.dumps(results, indent=2))


@cli.command("generate")
@click.option("--anchor", "anchor_slug", type=str)
@click.option("--from-pursues", is_flag=True, default=False)
@click.option("--count", type=int, default=10, show_default=True)
def generate_command(anchor_slug: str | None, from_pursues: bool, count: int) -> None:
    """Generate niche ideas from one anchor or prior PURSUE entries."""
    ideas = _ideas_from_source(anchor_slug=anchor_slug, from_pursues=from_pursues, count=count)
    click.echo(json.dumps({"ideas": ideas}, indent=2))


@cli.command("loop")
@click.option("--iterations", type=int, default=10, show_default=True)
@click.option("--ideas-per-iter", type=int, default=10, show_default=True)
@click.option("--anchors", "anchor_filter", type=str)
@click.option("--max-llm-calls", type=int)
@click.option("--stop-on-first-pursue", is_flag=True, default=False)
def loop_command(
    iterations: int,
    ideas_per_iter: int,
    anchor_filter: str | None,
    max_llm_calls: int | None,
    stop_on_first_pursue: bool,
) -> None:
    """Run the generate->hunt loop."""
    from evidentia.loop import run_loop

    all_anchors = load_all_anchors()
    selected_slugs = {slug.strip() for slug in (anchor_filter or "").split(",") if slug.strip()}
    selected = [anchor for anchor in all_anchors if not selected_slugs or anchor.slug in selected_slugs]
    if not selected:
        raise click.ClickException("no anchors selected")
    summary = run_loop(
        selected,
        iterations=iterations,
        ideas_per_iter=ideas_per_iter,
        max_llm_calls=max_llm_calls,
        stop_on_first_pursue=stop_on_first_pursue,
    )
    click.echo(json.dumps(summary, indent=2))


@cli.command("best")
@click.option("--verdict", type=str, default="PURSUE", show_default=True)
@click.option("--n", type=int, default=20, show_default=True)
def best_command(verdict: str, n: int) -> None:
    """Show top ideas from outputs/best_ideas.jsonl."""
    rows = top_index_ideas(_index_path(), verdict=verdict, n=n)
    _print_best_table(rows)


if __name__ == "__main__":
    cli()
