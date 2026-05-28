from __future__ import annotations

import json
from pathlib import Path

import click

from evidentia.anchor import anchors_root, load_anchor
from evidentia.generator import GeneratorError, generate_ideas_from_anchor
from evidentia.models import Idea, PlayerProfile
from evidentia.outputs import read_player_profile, write_player_profile
from evidentia.tournament.engine import run_tournament
from evidentia.tournament.helpers import (
    derive_reentry_rows_from_parent,
    enrich_idea_evidence,
    load_ideas_jsonl_raw,
    load_json,
    load_player_profile_any,
    load_player_profile_from_path,
    load_tournament_payload,
    materialize_ideas,
    memo_to_markdown,
    profile_confidence,
    safe_run_timestamp,
    validate_reentry_rules,
    write_events_ndjson,
    write_json,
)


@click.group()
def cli() -> None:
    """Evidentia — generate ideas, then validate them.

    Workflow: edge player → edge generate → edge validate → edge memo
    """


@click.group("edge")
def edge_group() -> None:
    """Edge commands."""


@edge_group.group("player")
def edge_player_group() -> None:
    """Manage edge player profiles."""


@edge_player_group.command("init-from-file")
@click.argument("profile_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output", "output_path",
    default="outputs/profile.json",
    show_default=True,
    type=click.Path(dir_okay=False),
)
def edge_player_init_from_file(profile_path: str, output_path: str) -> None:
    """Load a profile JSON file and persist it to outputs/profile.json."""
    profile = load_player_profile_from_path(profile_path)
    destination = Path(output_path)
    write_player_profile(destination, profile)
    click.echo(str(destination).replace("\\", "/"))


@edge_player_group.command("show")
@click.option(
    "--profile", "profile_path",
    default="outputs/profile.json",
    show_default=True,
    type=click.Path(exists=True, dir_okay=False),
)
def edge_player_show(profile_path: str) -> None:
    """Show the persisted player profile."""
    profile = read_player_profile(Path(profile_path))
    click.echo(json.dumps(profile.to_dict(), indent=2))


# ---------------------------------------------------------------------------
# Validate group (canonical)
# ---------------------------------------------------------------------------

@edge_group.group("validate")
def edge_validate_group() -> None:
    """Run validation tournaments."""


@edge_validate_group.command("run")
@click.option("--ideas", "ideas_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--player", "player_path",
    default="outputs/profile.json",
    show_default=True,
    type=click.Path(exists=True, dir_okay=False),
)
@click.option("--seed-from", "seed_from_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--narrow", is_flag=True, default=False)
@click.option("--profile", "profile_override", type=str)
@click.option("--discover-evidence", is_flag=True, default=False)
@click.option("--tournament-id", type=str)
@click.option("--output", "output_path", type=click.Path(dir_okay=False))
def edge_validate_run(
    ideas_path: str | None,
    player_path: str,
    seed_from_path: str | None,
    narrow: bool,
    profile_override: str | None,
    discover_evidence: bool,
    tournament_id: str | None,
    output_path: str | None,
) -> None:
    """Run edge validation using JSONL ideas and a player profile."""
    if not ideas_path and not seed_from_path:
        raise click.ClickException("either --ideas or --seed-from is required")
    player = load_player_profile_any(player_path)

    parent_payload: dict | None = None
    raw_rows: list[tuple[int, dict]]
    if seed_from_path:
        parent_payload = load_tournament_payload(seed_from_path)
        try:
            raw_rows = derive_reentry_rows_from_parent(parent_payload, require_narrow=narrow)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
    else:
        raw_rows = load_ideas_jsonl_raw(ideas_path or "")

    ideas, discards = materialize_ideas(raw_rows, discover_evidence=discover_evidence)
    if not ideas:
        reason = discards[0]["reason"] if discards else "no ideas provided"
        raise click.ClickException(reason)
    if profile_override is None:
        for idea in ideas:
            confidence = profile_confidence(idea.gate_profile_source)
            if confidence is not None and confidence < 0.7:
                raise click.ClickException("low-confidence inferred gate_profile requires --profile <name>")
    else:
        ideas = [
            Idea(
                id=idea.id,
                label=idea.label,
                anchor_slug=idea.anchor_slug,
                incumbent=idea.incumbent,
                cohort=idea.cohort,
                pain_hypothesis=idea.pain_hypothesis,
                kill_condition=idea.kill_condition,
                evidence_ids=idea.evidence_ids,
                search_queries=idea.search_queries,
                origin=idea.origin,
                gate_profile=profile_override,
                gate_profile_source="explicit",
                parent_idea_id=idea.parent_idea_id,
                evidence_provenance=idea.evidence_provenance,
            )
            for idea in ideas
        ]

    if parent_payload is not None:
        try:
            validate_reentry_rules(ideas, parent_payload, player=player)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc

    total_synthetic = 0
    enriched_count = 0
    for idea in ideas:
        new_ids, added = enrich_idea_evidence(idea)
        if added > 0:
            idea.evidence_ids = new_ids
            enriched_count += 1
            total_synthetic += added
        if len(idea.evidence_ids) < 3:
            if not idea.origin.startswith("enrichment_failed"):
                idea.origin = f"enrichment_failed:{idea.origin}"

    if total_synthetic > 0:
        click.echo(
            f"Preflight enrichment: {enriched_count} ideas enriched, "
            f"{total_synthetic} synthetic evidence IDs generated from search queries",
            err=True,
        )

    resolved_tournament_id = tournament_id or f"tournament-{safe_run_timestamp()}"
    parent_tournament_id = str(parent_payload.get("tournament_id", "")) if parent_payload else None
    reentry_depth = int(parent_payload.get("reentry_depth", 0) or 0) + 1 if parent_payload else 0
    result = run_tournament(
        ideas=ideas,
        player=player,
        tournament_id=resolved_tournament_id,
        gate_profile=profile_override,
        parent_tournament_id=parent_tournament_id,
        reentry_depth=reentry_depth,
    )
    resolved_output = Path(output_path) if output_path else Path("outputs") / "tournaments" / resolved_tournament_id / "tournament.json"
    result_payload = result.to_dict()
    write_json(str(resolved_output), result_payload)
    write_events_ndjson(resolved_output.parent / "events.ndjson", result_payload)
    memo_path = resolved_output.parent / "memo.json"
    write_json(str(memo_path), result_payload.get("memo", {}))
    if isinstance(result_payload.get("memo"), dict):
        diagnosis = result_payload["memo"].get("zero_winner_diagnosis")
        if diagnosis:
            write_json(
                str(resolved_output.parent / "zero_winner_diagnosis.json"),
                {"schema_version": 1, "tournament_id": result_payload.get("tournament_id"), "zero_winner_diagnosis": diagnosis},
            )
    if discards:
        discard_path = resolved_output.parent / "discard_log.json"
        write_json(str(discard_path), {"schema_version": 1, "discards": discards})
        click.echo(str(discard_path).replace("\\", "/"))
    click.echo(str(resolved_output).replace("\\", "/"))


@edge_validate_group.command("export")
@click.argument("tournament_json", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False))
def edge_validate_export(tournament_json: str, output_path: str) -> None:
    """Export an existing tournament JSON payload."""
    payload = load_json(tournament_json)
    write_json(output_path, payload)
    click.echo(output_path)


# ---------------------------------------------------------------------------
# Tournament group — deprecated alias for `edge validate`
# ---------------------------------------------------------------------------

@edge_group.group("tournament")
def edge_tournament_group() -> None:
    """Run/export tournaments. [DEPRECATED: use 'edge validate']"""


@edge_tournament_group.command("run")
@click.option("--ideas", "ideas_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--player", "player_path",
    default="outputs/profile.json",
    show_default=True,
    type=click.Path(exists=True, dir_okay=False),
)
@click.option("--seed-from", "seed_from_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--narrow", is_flag=True, default=False)
@click.option("--profile", "profile_override", type=str)
@click.option("--discover-evidence", is_flag=True, default=False)
@click.option("--tournament-id", type=str)
@click.option("--output", "output_path", type=click.Path(dir_okay=False))
def edge_tournament_run(
    ideas_path: str | None,
    player_path: str,
    seed_from_path: str | None,
    narrow: bool,
    profile_override: str | None,
    discover_evidence: bool,
    tournament_id: str | None,
    output_path: str | None,
) -> None:
    """Run edge tournament using JSONL ideas and a player profile. [DEPRECATED: use edge validate run]"""
    click.echo(click.style("⚠️  'edge tournament run' is deprecated. Use 'edge validate run'.", fg="yellow"), err=True)
    ctx = click.get_current_context()
    ctx.invoke(edge_validate_run, **ctx.params)


@edge_tournament_group.command("export")
@click.argument("tournament_json", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False))
def edge_tournament_export(tournament_json: str, output_path: str) -> None:
    """Export an existing tournament JSON payload. [DEPRECATED: use 'edge validate export']"""
    click.echo(click.style("⚠️  'edge tournament export' is deprecated. Use 'edge validate export'.", fg="yellow"), err=True)
    payload = load_json(tournament_json)
    write_json(output_path, payload)
    click.echo(output_path)


# ---------------------------------------------------------------------------
# Generate group
# ---------------------------------------------------------------------------

@edge_group.group("generate")
def edge_generate_group() -> None:
    """Generate candidate ideas."""


@edge_generate_group.command("from-anchor")
@click.option("--anchor", "anchor_slug", required=True, type=str, help="Anchor slug from anchors/ directory (e.g. 'smb-invoicing')")
@click.option("--count", default=10, type=int, show_default=True, help="Number of ideas to generate")
@click.option("--dry-run", is_flag=True, default=False, help="Generate 2 stub ideas without calling LLM provider")
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False))
def edge_generate_from_anchor(anchor_slug: str, count: int, dry_run: bool, output_path: str) -> None:
    """Generate candidate ideas from an anchor.

    Use --dry-run to produce deterministic stub ideas (no LLM credentials needed).
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if dry_run:
        stub_kill = {"description": "Stub kill condition for dry-run", "gate_name": "willingness_to_pay"}
        stubs = [
            {
                "id": "dry-run-1",
                "label": f"Dry Run Idea 1 for {anchor_slug}",
                "anchor_slug": anchor_slug,
                "incumbent": None,
                "cohort": "dry-run-cohort",
                "pain_hypothesis": "Dry run pain hypothesis for testing.",
                "kill_condition": stub_kill,
                "evidence_ids": ["dry-evidence-1"],
                "search_queries": ["dry run query 1"],
                "origin": "manual",
                "gate_profile": "consumer_app",
                "gate_profile_source": "explicit",
                "parent_idea_id": None,
            },
            {
                "id": "dry-run-2",
                "label": f"Dry Run Idea 2 for {anchor_slug}",
                "anchor_slug": anchor_slug,
                "incumbent": None,
                "cohort": "dry-run-cohort",
                "pain_hypothesis": "Another dry run pain hypothesis for testing.",
                "kill_condition": stub_kill,
                "evidence_ids": ["dry-evidence-1"],
                "search_queries": ["dry run query 2"],
                "origin": "manual",
                "gate_profile": "consumer_app",
                "gate_profile_source": "explicit",
                "parent_idea_id": None,
            },
        ]
        with out_path.open("w", encoding="utf-8") as fh:
            for stub in stubs:
                fh.write(json.dumps(stub, ensure_ascii=False) + "\n")
        click.echo(str(out_path).replace("\\", "/"))
        return

    anchor_dir = anchors_root()
    anchor_file = anchor_dir / f"{anchor_slug}.yaml"
    if not anchor_file.exists():
        anchor_file = anchor_dir / f"{anchor_slug}.yml"
        if not anchor_file.exists():
            raise click.ClickException(f"anchor '{anchor_slug}' not found in {anchor_dir}")
    anchor = load_anchor(anchor_file)
    try:
        ideas = generate_ideas_from_anchor(anchor, count=count)
    except GeneratorError as exc:
        raise click.ClickException(str(exc)) from exc
    with out_path.open("w", encoding="utf-8") as fh:
        for idea in ideas:
            fh.write(json.dumps(idea, ensure_ascii=False) + "\n")
    click.echo(str(out_path).replace("\\", "/"))


@edge_generate_group.command("from-reentry")
@click.option("--seed-from", "seed_from_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--narrow", is_flag=True, default=False)
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False))
def edge_generate_from_reentry(seed_from_path: str, narrow: bool, output_path: str) -> None:
    """Generate reentry ideas from a parent tournament payload."""
    parent_payload = load_tournament_payload(seed_from_path)
    try:
        raw_rows = derive_reentry_rows_from_parent(parent_payload, require_narrow=narrow)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    ideas, _discards = materialize_ideas(raw_rows, discover_evidence=False)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for idea in ideas:
            fh.write(json.dumps(idea.to_dict(), ensure_ascii=False) + "\n")
    click.echo(str(out_path).replace("\\", "/"))


# ---------------------------------------------------------------------------
# Memo group
# ---------------------------------------------------------------------------

@edge_group.group("memo")
def edge_memo_group() -> None:
    """Render decision memo artifacts."""


@edge_memo_group.command("render")
@click.argument("tournament_json", type=click.Path(exists=True, dir_okay=False))
@click.option("--format", "output_format", type=click.Choice(["json", "md"]), default="json", show_default=True)
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False))
def edge_memo_render(tournament_json: str, output_format: str, output_path: str) -> None:
    """Render memo from a tournament payload."""
    payload = load_json(tournament_json)
    memo = payload.get("memo")
    if not isinstance(memo, dict):
        raise click.ClickException("tournament payload missing memo object")

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "json":
        write_json(output_path, memo)
    else:
        out_path.write_text(memo_to_markdown(memo), encoding="utf-8")
    click.echo(output_path)


cli.add_command(edge_group)

if __name__ == "__main__":
    cli()
