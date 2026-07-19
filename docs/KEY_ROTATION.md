# API Key Rotation Checklist

Why: API keys exist in plaintext in `main/.env` (gitignored, OK) but ALSO in the
abandoned trees `../kimi/.env`, `../kimi/GIVEMEKEYS.md`, `../codex/.env`,
`../codex/GIVEMEKEYS.md`. Any key that ever sat in those files should be treated
as exposed. Rotate first, then delete the abandoned trees.

## Order of operations

1. Rotate every key below at its provider dashboard (revoke old, create new).
2. Update `main/.env` with the new values.
3. Verify: `uv run pytest tests/live -m live -q` (or a single `evidentia edge` run).
4. Delete `../kimi/` and `../codex/` entirely (after archiving anything wanted).
5. Confirm nothing else holds keys: search the outer folder for `API_KEY=` with a value.

## Probe results (2026-07-19, real API calls)

| Key | Status |
| --- | --- |
| GROQ_API_KEY | WORKS (primary LLM, `openai/gpt-oss-20b`) |
| OPENROUTER_API_KEY | WORKS (fallback; model updated to `poolside/laguna-xs-2.1:free` — old `llama-3.3-70b-instruct:free` was delisted, caused 404) |
| TAVILY_API_KEY | WORKS (search fallback behind keyless DuckDuckGo) |
| NVIDIA_API_KEY | DEAD (request timeout on two models; removed from LLM_FALLBACK_CHAIN) |
| All other keys in .env | EMPTY placeholders |

Routing in `.env` now pins the working set: `LLM_PROVIDER=groq`,
`LLM_FALLBACK_CHAIN=groq,openrouter`, `SEARCH_FALLBACK_CHAIN=duckduckgo,tavily`.
Working keys are still exposed-by-copy — rotation below remains necessary.

## GOTCHA before deleting kimi/ and codex/

`providers.py::load_external_provider_env()` reads `../codex/.env` and
`../kimi/.env` as fallback key sources (and `load_kimi_golden_cases()` reads
`../kimi/tests/golden_dataset.json`). Before deleting those trees, confirm
`main/.env` is complete and remove those fallback paths from `providers.py`
(copy the golden dataset into `main/tests/fixtures/` if still wanted).

## Keys to rotate (from .env.example)

| Env var | Rotate at |
| --- | --- |
| OPENROUTER_API_KEY | https://openrouter.ai/settings/keys |
| NVIDIA_API_KEY | https://build.nvidia.com (API keys) |
| GROQ_API_KEY | https://console.groq.com/keys |
| GEMINI_API_KEY | https://aistudio.google.com/apikey |
| TAVILY_API_KEY | https://app.tavily.com (API keys) |
| BRAVE_SEARCH_API_KEY | https://api-dashboard.search.brave.com |
| SERPAPI_API_KEY | https://serpapi.com/manage-api-key |

`main/.env` contains ~11 entries vs 7 in `.env.example` — while rotating, check
`main/.env`, `../kimi/.env`, `../kimi/GIVEMEKEYS.md`, `../codex/.env`, and
`../codex/GIVEMEKEYS.md` for any additional provider keys (e.g. Reddit/GitHub
tokens, Grok/xAI) and rotate those too.

## After rotation

- [ ] Old keys revoked (not just replaced) at each dashboard
- [ ] `../kimi/` and `../codex/` deleted
- [ ] Root debris keys check: `.grok/`, `tools/grok-mcp-server/`
- [ ] Extra hits from repo scan: `../kimi/config.py` (+ its `__pycache__/*.pyc`)
      may hardcode keys in Python; `../codex/journey.md` and `../codex/README.md`
      reference the key files — check before deleting
