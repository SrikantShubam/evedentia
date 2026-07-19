# Evidentia Implementation Plan

> **ARCHIVED** — This plan has diverged from actual implementation. See `agentdocs/plan.md` for the current plan.

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Evidentia as a deterministic demand-to-product pipeline that goes from evidence capture to scored opportunities, then to reviewed specs, then optionally to build, ship, and track.

**Architecture:** Start with a small Python CLI and a strict evidence model. Keep the core pipeline deterministic: fetch or fixture text, verify quotes, classify signals, apply hard gates, then rank survivors with explicit heuristics. Add spec generation only after the evidence core is proven, and postpone build/ship/track until the reviewed spec path is stable.

**Tech Stack:** Python 3.12, `click`, `rich`, `pydantic`, `pytest`, `httpx` or `urllib` for fetches, SQLite for local persistence, and fixture-backed tests for deterministic proof.

---

## Planning Contract

This repo currently contains only `README.md`, `final_pivot.md`, and untracked local files. The implementation should therefore create the project skeleton from scratch instead of trying to retrofit an existing codebase.

### Proof Levels

The plan must keep these proof levels separate:

- **Fixture proof:** deterministic tests against saved inputs and expected outputs.
- **Dry-run proof:** provider wiring, query planning, source selection, and pipeline orchestration with mocked or local stand-ins.
- **Live proof:** real external retrieval and one real shipped product path, used only after the fixture and dry-run gates are green.

Never label fixture proof as live proof. Never use live proof to justify code that has not already passed fixture and dry-run coverage.

### Hard Gates

The first scoring decision must be gate-first, not rank-first. The inherited hard gates are:

- `willingness_to_pay`
- `distribution_channel`
- `data_feasibility`

Rules:

- If any hard gate fails, the opportunity is `HOLD` or `SKIP` and must not proceed to automated build or ship stages.
- `PURSUE` requires all three hard gates to pass.
- Hard gates are deterministic booleans or tristate classifications derived from verified evidence only.

### Ranking Heuristics

Ranking happens only after hard gates pass. The initial heuristics are:

- `competition_gap`: stronger when users complain about incumbent friction or missing features.
- `buildability`: stronger when a small wedge can be built with limited surface area and clear API/data access.
- `reachability_strength`: stronger when the channel is cheap, direct, and plausibly reachable by the team.

Ranking rules:

- Deduplicate by source cluster before scoring.
- Apply freshness decay after deduplication.
- Keep heuristic weights explicit in code or config.
- Heuristics may reorder valid opportunities, but they may not change hard-gate semantics.

## Milestones and Deliverables

### Milestone 0: Repo bootstrap

Deliverables:

- Python package skeleton under `src/evidentia/`
- Test harness under `tests/`
- CLI entrypoint that imports cleanly
- First green fixture tests for import and configuration

Exit criteria:

- `pytest` runs locally
- package import works
- no live network access is required for the first tests

### Milestone 1: Evidence core

Deliverables:

- `DemandSignal`, `Opportunity`, and `ProductSpec` models
- deterministic verification of quotes against source text
- hard-gate scoring with explicit pass/fail behavior
- discard logging for unverifiable input

Exit criteria:

- a known good fixture produces a traceable signal and a scored opportunity
- a bad fixture is discarded with a reason code
- hard gates are enforced before any ranking

### Milestone 2: Multi-source ranking

Deliverables:

- source adapters for at least HN first, then Reddit and GitHub
- source-parallel scanning
- deduplication by source cluster
- ranking heuristics that do not alter gate semantics

Exit criteria:

- two valid opportunities can be reordered by heuristics without changing `PURSUE` vs `HOLD`
- source selection is testable in dry-run mode

### Milestone 3: Spec writer

Deliverables:

- structured product spec generation from verified opportunities
- explicit human-review boundary before build
- spec persistence in a machine-readable file

Exit criteria:

- a reviewed opportunity becomes a valid `ProductSpec`
- the spec only cites verified source material

### Milestone 4: Builder, shipper, tracker

Deliverables:

- wedge app generation from a reviewed spec
- local build/lint verification
- deployment adapter for Vercel with Railway fallback
- basic traction tracker for visits/signups/proxy metrics

Exit criteria:

- the generated app builds locally
- deployment is blocked unless explicit approval exists
- tracking returns stored metrics for at least one project

### Milestone 5: Live proof

Deliverables:

- one real end-to-end run on a real domain
- one real shipped product
- a short results record with what worked, what failed, and what was measured

Exit criteria:

- evidence core and spec path are validated on live inputs
- at least one product is shipped through the workflow

---

## File Structure

The code should be organized around small, testable units:

- `pyproject.toml` - project metadata, dependencies, pytest config, CLI entrypoint.
- `src/evidentia/__init__.py` - package version and top-level exports.
- `src/evidentia/cli.py` - Click commands for `scan`, `spec`, `build`, `ship`, and `track`.
- `src/evidentia/models.py` - Pydantic models for evidence, opportunity, and spec payloads.
- `src/evidentia/scoring.py` - hard gates, ranking heuristics, and deterministic scoring.
- `src/evidentia/auditor.py` - source verification, quote matching, and discard logging.
- `src/evidentia/providers.py` - search/fetch provider adapters and fallback selection.
- `src/evidentia/scanners/` - source-specific scanning modules.
- `src/evidentia/classifier.py` - structured classification of verified evidence.
- `src/evidentia/spec_writer.py` - opportunity to spec conversion.
- `src/evidentia/builder.py` - wedge app generation and local build checks.
- `src/evidentia/deployer.py` - Vercel/Railway deployment adapter.
- `src/evidentia/tracker.py` - post-ship metric collection.
- `tests/unit/` - deterministic logic tests.
- `tests/integration/` - adapter and pipeline wiring tests.
- `tests/acceptance/` - end-to-end fixture and dry-run tests.
- `tests/fixtures/` - saved pages, search results, source excerpts, and expected outputs.

---

## Phase 0: Bootstrap the Project

### Task 0.1: Create the package and test harness

**Files:**
- Create: `pyproject.toml`
- Create: `src/evidentia/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/unit/test_imports.py`

- [ ] **Step 1: Write the failing test**

```python
def test_package_imports():
    import evidentia

    assert hasattr(evidentia, "__version__")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/test_imports.py -v`

Expected: import failure because the package does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/test_imports.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/evidentia/__init__.py tests/conftest.py tests/unit/test_imports.py
git commit -m "feat: bootstrap evidentia package"
```

### Task 0.2: Add CLI smoke tests

**Files:**
- Create: `src/evidentia/cli.py`
- Create: `tests/unit/test_cli_smoke.py`

- [ ] **Step 1: Write the failing test**

```python
from click.testing import CliRunner
from evidentia.cli import cli


def test_cli_help_renders():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "scan" in result.output
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/test_cli_smoke.py -v`

Expected: import failure or missing command failure.

- [ ] **Step 3: Write the minimal implementation**

```python
import click


@click.group()
def cli() -> None:
    pass


@cli.command()
def scan() -> None:
    click.echo("scan")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/test_cli_smoke.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/cli.py tests/unit/test_cli_smoke.py
git commit -m "feat: add cli smoke path"
```

---

## Phase 1: Evidence Core

### Task 1.1: Define the evidence models

**Files:**
- Create: `src/evidentia/models.py`
- Create: `tests/unit/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
from evidentia.models import DemandSignal, Opportunity, ProductSpec


def test_signal_requires_source_and_quote():
    signal = DemandSignal(
        source_url="https://example.com/post",
        verbatim_quote="I need this now",
        signal_type="pain",
        source_strength="strong",
    )

    assert signal.source_url.startswith("https://")
    assert signal.verbatim_quote == "I need this now"


def test_opportunity_contains_gate_fields():
    opp = Opportunity(
        opportunity_id="opp_001",
        title="Reduce invoice chase time",
        willingness_to_pay="pass",
        distribution_channel="pass",
        data_feasibility="pass",
    )

    assert opp.willingness_to_pay == "pass"


def test_product_spec_requires_review_and_sources():
    spec = ProductSpec(
        opportunity_id="opp_001",
        title="Invoice chase automation",
        approved=False,
        sources=[{"source_url": "https://example.com/post", "verbatim_quote": "I need this"}],
    )

    assert spec.approved is False
    assert len(spec.sources) == 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/test_models.py -v`

Expected: module import failure because models do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
from pydantic import BaseModel


class DemandSignal(BaseModel):
    source_url: str
    verbatim_quote: str
    signal_type: str
    source_strength: str


class Opportunity(BaseModel):
    opportunity_id: str
    title: str
    willingness_to_pay: str
    distribution_channel: str
    data_feasibility: str


class ProductSpec(BaseModel):
    opportunity_id: str
    title: str
    approved: bool
    sources: list[dict]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/test_models.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/models.py tests/unit/test_models.py
git commit -m "feat: define evidence models"
```

### Task 1.2: Implement deterministic gating and scoring

**Files:**
- Create: `src/evidentia/scoring.py`
- Create: `tests/unit/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
from evidentia.scoring import score_opportunity


def test_hard_gate_failure_blocks_score():
    opportunity = {
        "willingness_to_pay": "fail",
        "distribution_channel": "pass",
        "data_feasibility": "pass",
    }

    result = score_opportunity(opportunity)

    assert result["verdict"] == "HOLD"
    assert result["score"] == 0


def test_pursue_requires_all_three_gates():
    opportunity = {
        "willingness_to_pay": "pass",
        "distribution_channel": "pass",
        "data_feasibility": "pass",
        "competition_gap": 0.8,
        "buildability": 0.6,
        "reachability_strength": 0.7,
    }

    result = score_opportunity(opportunity)

    assert result["verdict"] == "PURSUE"
    assert result["score"] > 0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/test_scoring.py -v`

Expected: import failure because scoring does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
def score_opportunity(opportunity: dict) -> dict:
    gates = [
        opportunity["willingness_to_pay"],
        opportunity["distribution_channel"],
        opportunity["data_feasibility"],
    ]
    if any(gate != "pass" for gate in gates):
        return {"verdict": "HOLD", "score": 0}

    score = (
        opportunity.get("competition_gap", 0) * 0.4
        + opportunity.get("buildability", 0) * 0.3
        + opportunity.get("reachability_strength", 0) * 0.3
    )
    return {"verdict": "PURSUE", "score": round(score, 3)}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/test_scoring.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/scoring.py tests/unit/test_scoring.py
git commit -m "feat: add deterministic scoring"
```

### Task 1.3: Add quote verification and discard logging

**Files:**
- Create: `src/evidentia/auditor.py`
- Create: `tests/unit/test_auditor.py`
- Create: `tests/fixtures/sample_source.txt`

- [ ] **Step 1: Write the failing test**

```python
from evidentia.auditor import verify_quote


def test_verify_quote_accepts_exact_match(tmp_path):
    source_text = "I need invoice chasing automation."
    result = verify_quote(
        source_text=source_text,
        source_url="https://example.com/post",
        verbatim_quote="invoice chasing automation",
    )

    assert result["verified"] is True


def test_verify_quote_rejects_missing_quote():
    result = verify_quote(
        source_text="Hello world",
        source_url="https://example.com/post",
        verbatim_quote="missing fragment",
    )

    assert result["verified"] is False
    assert result["reason"] == "quote_not_found"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/test_auditor.py -v`

Expected: import failure because auditor does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
def verify_quote(source_text: str, source_url: str, verbatim_quote: str) -> dict:
    if verbatim_quote in source_text:
        return {"verified": True, "source_url": source_url}
    return {"verified": False, "source_url": source_url, "reason": "quote_not_found"}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/test_auditor.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/auditor.py tests/unit/test_auditor.py tests/fixtures/sample_source.txt
git commit -m "feat: add evidence verification"
```

---

## Phase 2: Scanner and Multi-Source Ranking

### Task 2.1: Implement the first source adapter

**Files:**
- Create: `src/evidentia/providers.py`
- Create: `src/evidentia/scanners/hn.py`
- Create: `tests/integration/test_hn_scanner.py`

- [ ] **Step 1: Write the failing test**

```python
from evidentia.scanners.hn import scan_hn_fixture


def test_hn_fixture_returns_verified_candidates():
    results = scan_hn_fixture("tests/fixtures/hn_sample.json")

    assert len(results) >= 1
    assert results[0]["source"] == "hn"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/integration/test_hn_scanner.py -v`

Expected: import failure because scanner does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
import json


def scan_hn_fixture(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return [{"source": "hn", "title": item["title"]} for item in payload["items"]]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/integration/test_hn_scanner.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/providers.py src/evidentia/scanners/hn.py tests/integration/test_hn_scanner.py
git commit -m "feat: add hn scanner fixture path"
```

### Task 2.2: Add deduplication and heuristic ranking

**Files:**
- Modify: `src/evidentia/scoring.py`
- Create: `tests/unit/test_ranking.py`

- [ ] **Step 1: Write the failing test**

```python
from evidentia.scoring import rank_opportunities


def test_rank_uses_heuristics_only_after_gates():
    opportunities = [
        {
            "opportunity_id": "opp_a",
            "willingness_to_pay": "pass",
            "distribution_channel": "pass",
            "data_feasibility": "pass",
            "competition_gap": 0.2,
            "buildability": 0.9,
            "reachability_strength": 0.4,
        },
        {
            "opportunity_id": "opp_b",
            "willingness_to_pay": "pass",
            "distribution_channel": "pass",
            "data_feasibility": "pass",
            "competition_gap": 0.9,
            "buildability": 0.3,
            "reachability_strength": 0.8,
        },
    ]

    ranked = rank_opportunities(opportunities)

    assert ranked[0]["opportunity_id"] in {"opp_a", "opp_b"}
    assert ranked[0]["verdict"] == "PURSUE"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/test_ranking.py -v`

Expected: missing function failure.

- [ ] **Step 3: Write the minimal implementation**

```python
def rank_opportunities(opportunities: list[dict]) -> list[dict]:
    scored = [dict(item, **score_opportunity(item)) for item in opportunities]
    return sorted(scored, key=lambda item: item["score"], reverse=True)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/test_ranking.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/scoring.py tests/unit/test_ranking.py
git commit -m "feat: rank opportunities after gating"
```

### Task 2.3: Add source-cluster deduplication

**Files:**
- Modify: `src/evidentia/scoring.py`
- Create: `tests/unit/test_dedup.py`

- [ ] **Step 1: Write the failing test**

```python
from evidentia.scoring import dedupe_by_cluster


def test_dedup_keeps_best_signal_per_cluster():
    inputs = [
        {"opportunity_id": "opp_1", "cluster_id": "c1", "score": 0.3},
        {"opportunity_id": "opp_2", "cluster_id": "c1", "score": 0.7},
    ]

    results = dedupe_by_cluster(inputs)

    assert len(results) == 1
    assert results[0]["opportunity_id"] == "opp_2"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/test_dedup.py -v`

Expected: missing function failure.

- [ ] **Step 3: Write the minimal implementation**

```python
def dedupe_by_cluster(items: list[dict]) -> list[dict]:
    best_by_cluster: dict[str, dict] = {}
    for item in items:
        cluster_id = item["cluster_id"]
        current = best_by_cluster.get(cluster_id)
        if current is None or item["score"] > current["score"]:
            best_by_cluster[cluster_id] = item
    return list(best_by_cluster.values())
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/test_dedup.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/scoring.py tests/unit/test_dedup.py
git commit -m "feat: deduplicate opportunities by cluster"
```

---

## Phase 3: Spec Writer

### Task 3.1: Convert verified opportunities into structured specs

**Files:**
- Create: `src/evidentia/spec_writer.py`
- Create: `tests/unit/test_spec_writer.py`

- [ ] **Step 1: Write the failing test**

```python
from evidentia.models import ProductSpec
from evidentia.spec_writer import write_spec


def test_spec_includes_verified_sources_only():
    opportunity = {
        "opportunity_id": "opp_001",
        "title": "Invoice chase automation",
        "verified_sources": [
            {"source_url": "https://example.com/post", "verbatim_quote": "I need this"},
        ],
    }

    spec = write_spec(opportunity)

    assert isinstance(spec, ProductSpec)
    assert spec.opportunity_id == "opp_001"
    assert spec.sources[0]["source_url"] == "https://example.com/post"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/test_spec_writer.py -v`

Expected: import failure because spec writer does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
from evidentia.models import ProductSpec


def write_spec(opportunity: dict) -> ProductSpec:
    return ProductSpec(
        opportunity_id=opportunity["opportunity_id"],
        title=opportunity["title"],
        approved=False,
        sources=opportunity.get("verified_sources", []),
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/test_spec_writer.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/spec_writer.py tests/unit/test_spec_writer.py
git commit -m "feat: add spec writer"
```

### Task 3.2: Add the human review gate before build

**Files:**
- Modify: `src/evidentia/cli.py`
- Create: `tests/unit/test_review_gate.py`

- [ ] **Step 1: Write the failing test**

```python
from evidentia.cli import approve_spec


def test_build_is_blocked_without_approval():
    assert approve_spec({"approved": False}) is False
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/test_review_gate.py -v`

Expected: missing function failure.

- [ ] **Step 3: Write the minimal implementation**

```python
def approve_spec(spec: dict) -> bool:
    return bool(spec.get("approved", False))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/test_review_gate.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/cli.py tests/unit/test_review_gate.py
git commit -m "feat: add spec approval gate"
```

---

## Phase 4: Builder, Ship, and Track

### Task 4.1: Generate a wedge app from a reviewed spec

**Files:**
- Create: `src/evidentia/builder.py`
- Create: `tests/integration/test_builder.py`

- [ ] **Step 1: Write the failing test**

```python
from evidentia.builder import build_wedge_app


def test_build_creates_app_manifest(tmp_path):
    spec = {"opportunity_id": "opp_001", "title": "Invoice chase automation", "approved": True}

    output_dir = build_wedge_app(spec, tmp_path)

    assert (output_dir / "package.json").exists()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/integration/test_builder.py -v`

Expected: import failure because builder does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
from pathlib import Path


def build_wedge_app(spec: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "package.json").write_text("{}", encoding="utf-8")
    return output_dir
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/integration/test_builder.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/builder.py tests/integration/test_builder.py
git commit -m "feat: scaffold wedge app builder"
```

### Task 4.2: Add deployment and tracking adapters

**Files:**
- Create: `src/evidentia/deployer.py`
- Create: `src/evidentia/tracker.py`
- Create: `tests/unit/test_deployer.py`
- Create: `tests/unit/test_tracker.py`

- [ ] **Step 1: Write the failing tests**

```python
from evidentia.deployer import can_deploy
from evidentia.tracker import empty_metrics


def test_deploy_requires_approval():
    assert can_deploy({"approved": False}) is False


def test_metrics_shape():
    metrics = empty_metrics()
    assert metrics["visits"] == 0
    assert metrics["signups"] == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/unit/test_deployer.py tests/unit/test_tracker.py -v`

Expected: missing module failures.

- [ ] **Step 3: Write the minimal implementation**

```python
def can_deploy(spec: dict) -> bool:
    return bool(spec.get("approved", False))


def empty_metrics() -> dict:
    return {"visits": 0, "signups": 0, "revenue_proxy": 0}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/unit/test_deployer.py tests/unit/test_tracker.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/deployer.py src/evidentia/tracker.py tests/unit/test_deployer.py tests/unit/test_tracker.py
git commit -m "feat: add ship and track adapters"
```

---

## Phase 5: End-to-End CLI and Live Proof

### Task 5.1: Wire the CLI flow across scan, spec, build, ship, and track

**Files:**
- Modify: `src/evidentia/cli.py`
- Create: `tests/acceptance/test_cli_flow.py`

- [ ] **Step 1: Write the failing test**

```python
from click.testing import CliRunner
from evidentia.cli import cli


def test_cli_exposes_scan_spec_build_ship_track():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    for command in ["scan", "spec", "build", "ship", "track"]:
        assert command in result.output
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/acceptance/test_cli_flow.py -v`

Expected: missing commands or import failure.

- [ ] **Step 3: Write the minimal implementation**

```python
import click


@click.group()
def cli() -> None:
    pass


@cli.command()
def scan() -> None:
    click.echo("scan")


@cli.command()
def spec() -> None:
    click.echo("spec")


@cli.command()
def build() -> None:
    click.echo("build")


@cli.command()
def ship() -> None:
    click.echo("ship")


@cli.command()
def track() -> None:
    click.echo("track")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/acceptance/test_cli_flow.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/cli.py tests/acceptance/test_cli_flow.py
git commit -m "feat: wire end-to-end cli"
```

### Task 5.2: Prove live retrieval and one shipped product

**Files:**
- Create: `tests/acceptance/test_live_gate.py`
- Modify: `src/evidentia/providers.py`
- Modify: `src/evidentia/deployer.py`

- [ ] **Step 1: Write the live-proof test gate**

```python
import os
import pytest


@pytest.mark.live
def test_live_retrieval_requires_explicit_env_flag():
    assert os.getenv("EVIDENTIA_RUN_LIVE_TESTS") == "1"
```

- [ ] **Step 2: Run the gate test to verify it blocks by default**

Run: `pytest tests/acceptance/test_live_gate.py -v`

Expected: PASS when the flag is absent because the test asserts the guard, not the live call.

- [ ] **Step 3: Implement the live path behind the guard**

```python
if os.getenv("EVIDENTIA_RUN_LIVE_TESTS") != "1":
    raise RuntimeError("live tests are disabled")
```

- [ ] **Step 4: Run the live path only after approval**

Run: `pytest -m live -v`

Expected: executes only when the environment and approval gates are intentionally enabled.

- [ ] **Step 5: Commit**

```bash
git add src/evidentia/providers.py src/evidentia/deployer.py tests/acceptance/test_live_gate.py
git commit -m "feat: add live-proof guardrails"
```

---

## Execution Rules

- Write the failing test before implementation in every task.
- Keep each commit small and aligned to one task.
- Do not merge spec, build, ship, and live-proof work into one untestable change.
- Do not bypass the human-review gate before build or deploy.
- Do not let heuristic ranking change hard-gate behavior.
- Keep fixture-based tests green before any live integrations are attempted.

## Final Acceptance Checklist

The implementation is complete when all of the following are true:

- `scan` produces ranked opportunities from at least one source with verified quotes.
- Every surviving signal traces back to a source URL and a verbatim quote.
- `willingness_to_pay`, `distribution_channel`, and `data_feasibility` are enforced deterministically.
- Ranking heuristics can reorder valid opportunities without changing gate outcomes.
- `spec` produces a structured `ProductSpec` only from verified evidence.
- `build` only runs after explicit review approval.
- `ship` is blocked unless approval exists.
- `track` returns persisted metrics for shipped work.
- Fixture and dry-run tests pass without paid APIs.
- At least one live run is completed and documented separately from fixture proof.
