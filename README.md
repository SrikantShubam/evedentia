# Evidentia

Evidentia is an **AI-powered idea tournament engine** that validates demand signals against structured player profiles, runs them through deterministic gates, and produces decision memos. It is built as a Python CLI with a strict fixture-backed testing discipline.

## Current Workflow

The pipeline follows four stages, each exposed as an `edge` subcommand:

```
edge player      — Load or initialize a PlayerProfile (budget, skills, risk tolerance)
edge generate    — Generate candidate ideas from demand signals
edge validate    — Run ideas through tournament gates (kill/refine/pursue)
edge memo        — Render a decision memo with mechanical evidence assembly
```

Additional standalone commands: `scan`, `hunt`, `hunt-all`, `loop`, `best`.

## Setup

### Prerequisites

- Python 3.12+
- `pip` (or `uv` for faster installs)

### Install

```sh
python -m pip install -e .
```

For development dependencies (pytest, httpx):

```sh
python -m pip install -e ".[dev]"
```

### Environment

Copy the example env file and fill in your API keys:

```sh
cp .env.example .env
```

Required keys: `OPENROUTER_API_KEY`, `TAVILY_API_KEY` (or others depending on provider chain). The system works with **free-tier providers** when available — see Data Source Compliance below.

### SearXNG (Recommended for Free Tier)

The search fallback chain uses SearXNG as a privacy-respecting meta-search engine. This avoids rate limits on public search APIs.

```sh
# Start SearXNG (requires Docker)
docker compose up -d

# Verify it's running
curl "http://localhost:8888/search?q=test&format=json"
```

Without SearXNG, the system falls back to DuckDuckGo which may rate-limit and return empty results.

## Data Source Compliance

All data sources used by Evidentia are documented with their rate limits and terms:

| Source | Method | Rate Limit | Auth Required | Notes |
|--------|--------|------------|---------------|-------|
| Apple RSS Feed | HTTP GET | Reasonable use | None | Returns **only 20 most recent reviews** per app. No star-rating filter server-side. |
| Reddit JSON API | HTTP GET + `.json` suffix | 60 req/min | User-Agent header required | Public data only. Respect robots.txt. |
| GitHub Issues API | REST API | 60 req/hr (unauth), 5000/hr (with token) | Token optional | Set `GITHUB_TOKEN` for higher limits. |
| DuckDuckGo | Instant Answer API | Unknown, may rate-limit | None | Returns sparse results. No official API — behavior may change. |
| SearXNG | Self-hosted meta-search | Depends on upstream engines | None (local) | Privacy-respecting. Requires Docker. |
| Auditor page fetcher | HTTP GET | Per-site | None | Fetches full page text for quote verification. Use only on public review/app store pages. |

## Running Tests

```sh
python -m pytest tests/ -v
```

Live tests (real network calls, not for CI):

```sh
python -m pytest tests/ -v -m live
```

## Documentation

- **`agentdocs/spec.md`** — Detailed system specification
- **`agentdocs/plan.md`** — Current phased implementation plan (Phases 0-4 complete)
- **`docs/archive/`** — Superseded or historical planning documents

## Project Status

- **Engine core (Phases 0-5): COMPLETE** — models, profiles, generators, tournament gates, verdicts, decision memos, research pipeline, interrogator, CI
- **API + Frontend**: Available — FastAPI backend (`scripts/start_api.py`) and Next.js frontend (`docs/frontend/`) are ready for use
- **Live Proof**: Engine gate PASSED — 2/3 test markets produce real competitive intelligence reports
- **CI**: GitHub Actions configured — runs on push/PR to main and feature branches

See `agentdocs/plan.md` for the full specification and `agentdocs/spec.md` for detailed system design.

## Quick Commands

```sh
# Research a market
python -m evidentia.cli edge research "meditation apps for beginners"

# Generate ideas from an anchor
python -m evidentia.cli generate --anchor smb-invoicing --count 5

# Run a tournament
python -m evidentia.cli edge tournament run --ideas ideas.jsonl --player profile.json

# Query results
python -m evidentia.cli edge interrogate tournament.json "why did idea #3 die?"

# Bridge research to validation
python -m evidentia.cli edge bridge research.json --output ideas.jsonl
```
