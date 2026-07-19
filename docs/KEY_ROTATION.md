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
