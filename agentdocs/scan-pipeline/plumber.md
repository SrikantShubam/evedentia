# Agent Task: PLUMBER — SearXNG Provider + Web Search Scanner

## Role
You connect pipes. You don't redesign plumbing. You implement exactly what's specified. You verify with the tests provided. You commit when tests pass.

## Pre-Read Contract (MUST read these files before touching any code)

Read these files IN ORDER:

1. `src/evidentia/providers.py` — SearchProvider base class, existing implementations (DuckDuckGoInstantSearchProvider, TavilySearchProvider)
2. `src/evidentia/scanners/hn.py` — canonical scanner pattern (see `scan_hn_live` function)
3. `src/evidentia/scanners/__init__.py` — LIVE_SCANNERS dict registration pattern
4. `src/evidentia/cli.py` — `_run_live_source` dispatcher function
5. `docs/frontend/app/page.tsx` — dashboard source toggle pattern

## What to Build

### 1. Add `SearXNGSearchProvider` to `src/evidentia/providers.py`

Add this class after the existing `TavilySearchProvider`. The contract:

```python
class SearXNGSearchProvider(SearchProvider):
    name = "searxng"

    # Constructor params:
    #   base_url: str — SearXNG instance URL (default from SEARXNG_URL env var, fallback http://127.0.0.1:8888)
    #   timeout: int — HTTP timeout in seconds (default 15)

    # search(query: str, max_results: int) -> list[SearchHit]:
    #   GET {base_url}/search?q={query}&format=json&categories=general&pageno=1
    #   Parse response.results -> SearchHit(title=item.title, url=item.url, snippet=item.content)
    #   Return empty list for empty/whitespace query
    #   Raise ProviderError on HTTP failure or parse failure
```

### 2. Update `choose_search_provider()` in `src/evidentia/providers.py`

Make SearXNG the primary. WHEN SearXNG is unreachable, the caller catches ProviderError.

### 3. Create `src/evidentia/scanners/web_search.py`

Create this file. Follow the scanner pattern from `hn.py`. Contract:

```python
def scan_web_search_live(query: str, max_results: int = 5) -> list[dict]:
    """Scan the web using SearXNG for demand signals.
    
    Returns list of candidate dicts, each with:
        source: "web_search"
        title: str (never empty)
        source_url: str (starts with http)
        published_at: ISO 8601 timestamp
        verbatim_quote: str (from SearchHit.snippet)
        source_text: str (same as verbatim_quote)
        cluster_id: "web:{sha256(url)[:12]}"
    """
```

### 4. Register in `src/evidentia/scanners/__init__.py`

Add `web_search` key to `LIVE_SCANNERS` dict.

### 5. Add dispatch in `src/evidentia/cli.py`

In `_run_live_source()`, add `elif source == "web_search":` branch.

### 6. Add dashboard toggle in `docs/frontend/app/page.tsx`

- Add `web_search: true` to sources state
- Add `{ id: "web_search", label: "Web" }` to source toggle array

## Tests to Pass

Run these exact commands and ALL must pass:

```bash
cd C:\experiments\evidentia\main
PYTHONPATH=src pytest tests/unit/test_searxng_provider.py -v
PYTHONPATH=src pytest tests/unit/test_web_search_scanner.py -v
PYTHONPATH=src pytest tests/unit/test_scanner_registration.py -v
cd docs\frontend; npx next build
```

## Smoke Test

```bash
curl -X POST http://localhost:8000/scan -H "Content-Type: application/json" -d "{\"keyword\":\"plastic-free packaging\",\"sources\":[\"web_search\"],\"max_results\":3}"
```

Must return 200 with `opportunities` array.

## Commit

```bash
git add -A
git commit -m "feat: add SearXNG provider, web_search scanner, dashboard Web toggle"
```

## PR (create after commit)

```bash
gh pr create --base feat/edge-tournament-phase0 --head feat/edge-tournament-phase0 --title "feat: SearXNG provider + web search scanner" --body "Adds SearXNGSearchProvider, web_search scanner, dashboard Web source toggle. See tests/unit/test_searxng_provider.py for tests."
```

## Exit Gate (you're done when)

- [ ] All 17 unit tests pass (3 test files)
- [ ] `npx next build` compiles clean
- [ ] `curl POST /scan` returns 200 with opportunities from web_search source
- [ ] Dashboard shows "Web" toggle pill
- [ ] No hardcoded hex colors in any new file
