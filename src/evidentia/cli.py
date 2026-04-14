import json
from pathlib import Path

import click

from evidentia.auditor import verify_quote
from evidentia.builder import build_wedge_app
from evidentia.classifier import classify_candidate
from evidentia.deployer import build_deployment_metadata, can_deploy
from evidentia.scanners import FIXTURE_SCANNERS
from evidentia.scanners.hn import scan_hn_fixture, scan_hn_live
from evidentia.scoring import dedupe_by_cluster, rank_opportunities, score_opportunity
from evidentia.spec_writer import write_spec
from evidentia.tracker import load_metrics


@click.group()
def cli() -> None:
    """Evidentia command-line interface."""


def approve_spec(spec: dict) -> bool:
    return spec.get("approved") is True


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: str, payload: dict) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _candidate_to_opportunity(index: int, candidate: dict) -> tuple[dict | None, dict | None]:
    verification = verify_quote(
        source_text=candidate["source_text"],
        source_url=candidate["source_url"],
        verbatim_quote=candidate["verbatim_quote"],
    )
    if not verification["verified"]:
        discard = {
            "source_url": candidate["source_url"],
            "verbatim_quote": candidate["verbatim_quote"],
            "reason": verification["reason"],
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
        enriched_candidate = classify_candidate(candidate)

    opportunity = {
        "opportunity_id": f"opp_{index:03d}",
        "title": enriched_candidate["title"],
        "cluster_id": enriched_candidate["cluster_id"],
        "verified_signals": [verified_signal],
        "willingness_to_pay": enriched_candidate["willingness_to_pay"],
        "distribution_channel": enriched_candidate["distribution_channel"],
        "data_feasibility": enriched_candidate["data_feasibility"],
        "competition_gap": enriched_candidate["competition_gap"],
        "buildability": enriched_candidate["buildability"],
        "reachability_strength": enriched_candidate["reachability_strength"],
        "published_at": enriched_candidate.get("published_at"),
    }
    opportunity.update(score_opportunity(opportunity))
    return opportunity, None


def run_fixture_scan(fixtures_by_source: dict[str, str]) -> dict:
    candidates = []
    for source, path in fixtures_by_source.items():
        candidates.extend(FIXTURE_SCANNERS[source](path))

    scored: list[dict] = []
    discard_log: list[dict] = []

    for index, candidate in enumerate(candidates, start=1):
        opportunity, discard = _candidate_to_opportunity(index, candidate)
        if opportunity is not None:
            scored.append(opportunity)
        if discard is not None:
            discard_log.append(discard)

    deduped = dedupe_by_cluster(scored)
    ranked = rank_opportunities(deduped)
    return {"opportunities": ranked, "discard_log": discard_log}


def _run_scan_fixture(fixture_path: str) -> dict:
    return run_fixture_scan({"hn": fixture_path})


def run_live_scan(domain: str, max_results: int = 3) -> dict:
    candidates = scan_hn_live(domain, max_results=max_results)
    scored: list[dict] = []
    discard_log: list[dict] = []

    for index, candidate in enumerate(candidates, start=1):
        opportunity, discard = _candidate_to_opportunity(index, candidate)
        if opportunity is not None:
            scored.append(opportunity)
        if discard is not None:
            discard_log.append(discard)

    deduped = dedupe_by_cluster(scored)
    ranked = rank_opportunities(deduped)
    return {"opportunities": ranked, "discard_log": discard_log}


@cli.command()
@click.option("--fixture", "fixture_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--live", "live_mode", is_flag=True, default=False)
@click.option("--domain", type=str)
@click.option("--max-results", type=int, default=3, show_default=True)
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False))
def scan(fixture_path: str | None, live_mode: bool, domain: str | None, max_results: int, output_path: str) -> None:
    """Run the scan stage."""
    if live_mode:
        if not domain:
            raise click.ClickException("--domain is required with --live")
        payload = run_live_scan(domain, max_results=max_results)
    else:
        if not fixture_path:
            raise click.ClickException("--fixture is required unless --live is used")
        payload = _run_scan_fixture(fixture_path)
    _write_json(output_path, payload)
    click.echo(output_path)


@cli.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False))
def spec(input_path: str, output_path: str) -> None:
    """Run the spec stage."""
    opportunity = _load_json(input_path)
    spec_payload = write_spec(opportunity).model_dump(mode="json")
    _write_json(output_path, spec_payload)
    click.echo(output_path)


@cli.command()
@click.option("--spec", "spec_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output-dir", required=True, type=click.Path(file_okay=False))
def build(spec_path: str, output_dir: str) -> None:
    """Run the build stage."""
    spec_payload = _load_json(spec_path)
    if not approve_spec(spec_payload):
        raise click.ClickException("spec must be approved before build")
    build_wedge_app(spec_payload, Path(output_dir))
    click.echo(output_dir)


@cli.command()
@click.option("--spec", "spec_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False))
def ship(spec_path: str, output_path: str) -> None:
    """Run the ship stage."""
    spec_payload = _load_json(spec_path)
    if not can_deploy(spec_payload):
        raise click.ClickException("spec must be approved before deploy")
    deployment = build_deployment_metadata(spec_payload)
    _write_json(output_path, deployment)
    click.echo(output_path)


@cli.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, dir_okay=False))
def track(input_path: str) -> None:
    """Run the track stage."""
    click.echo(json.dumps(load_metrics(input_path)))


if __name__ == "__main__":
    cli()
