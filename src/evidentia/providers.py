from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_SOURCES = ("hn", "reddit", "github")
SENSITIVE_KEYS = (
    "OPENROUTER_API_KEY",
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "NVIDIA_API_KEY",
    "TAVILY_API_KEY",
    "BRAVE_SEARCH_API_KEY",
    "SERPAPI_API_KEY",
)
DEFAULT_USER_AGENT = "Evidentia/1.0 (+https://example.local/provider-smoke)"


class ProviderError(RuntimeError):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _parse_dotenv_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_external_provider_env() -> dict[str, str]:
    env = dict(os.environ)
    repo_root = _repo_root()
    dotenv_paths = [
        repo_root / ".env",
        repo_root.parent / "codex" / ".env",
        repo_root.parent / "kimi" / ".env",
    ]
    for dotenv_path in dotenv_paths:
        for key, value in _parse_dotenv_file(dotenv_path).items():
            env.setdefault(key, value)
    return env


def load_kimi_golden_cases() -> list[dict[str, Any]]:
    dataset_path = _repo_root().parent / "kimi" / "tests" / "golden_dataset.json"
    return json.loads(dataset_path.read_text(encoding="utf-8"))


def build_scan_plan(domain: str, requested_sources: list[str] | None = None) -> dict:
    sources = requested_sources or list(DEFAULT_SOURCES)
    return {
        "domain": domain,
        "mode": "dry-run",
        "sources": [{"source": source, "query": f"{domain} demand signals"} for source in sources],
    }


def _http_json(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    timeout_sec: int = 30,
) -> Any:
    req_headers = dict(headers or {})
    req_headers.setdefault("User-Agent", DEFAULT_USER_AGENT)
    body_bytes: bytes | None = None
    if payload is not None:
        body_bytes = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url=url, method=method, headers=req_headers, data=body_bytes)
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            content = response.read().decode("utf-8")
            return json.loads(content) if content else {}
    except Exception as exc:  # noqa: BLE001
        raise ProviderError(f"HTTP request failed for {url}: {exc}") from exc


def _parse_chain(raw: str | None, default_value: str) -> list[str]:
    source = (raw or "").strip() or default_value
    chain: list[str] = []
    for token in source.split(","):
        item = token.strip().lower()
        if item and item not in chain:
            chain.append(item)
    return chain


def _sanitize_message(message: str, env: dict[str, str]) -> str:
    redacted = message
    for key in SENSITIVE_KEYS:
        value = str(env.get(key) or "")
        if value:
            redacted = redacted.replace(value, "***")
    return redacted


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    snippet: str


class SearchProvider:
    name: str = "unknown"

    def search(self, query: str, max_results: int = 5) -> list[SearchHit]:
        raise NotImplementedError


class DuckDuckGoInstantSearchProvider(SearchProvider):
    name = "duckduckgo"

    def search(self, query: str, max_results: int = 5) -> list[SearchHit]:
        encoded = urllib.parse.urlencode({"q": query, "format": "json", "no_html": 1, "skip_disambig": 1})
        data = _http_json(url=f"https://api.duckduckgo.com/?{encoded}", method="GET")
        hits: list[SearchHit] = []

        def add_hit(title: str, url: str, snippet: str) -> None:
            if url and all(existing.url != url for existing in hits):
                hits.append(SearchHit(title=title, url=url, snippet=snippet))

        abstract_url = str(data.get("AbstractURL") or "")
        abstract_text = str(data.get("AbstractText") or "")
        heading = str(data.get("Heading") or query)
        if abstract_url:
            add_hit(heading, abstract_url, abstract_text or heading)

        for item in data.get("Results") or []:
            if len(hits) >= max_results:
                break
            if isinstance(item, dict):
                add_hit(str(item.get("Text") or heading), str(item.get("FirstURL") or ""), str(item.get("Text") or heading))
        return hits[:max_results]


class TavilySearchProvider(SearchProvider):
    name = "tavily"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, query: str, max_results: int = 5) -> list[SearchHit]:
        payload = {"api_key": self.api_key, "query": query, "max_results": max_results, "search_depth": "basic"}
        data = _http_json("https://api.tavily.com/search", method="POST", payload=payload)
        return [
            SearchHit(
                title=str(item.get("title") or ""),
                url=str(item.get("url") or ""),
                snippet=str(item.get("content") or ""),
            )
            for item in data.get("results") or []
        ]


class SearXNGSearchProvider(SearchProvider):
    name = "searxng"

    def __init__(self, base_url: str | None = None, timeout: int = 15):
        import os
        self._base_url = (base_url or os.environ.get("SEARXNG_URL", "http://127.0.0.1:8888")).rstrip("/")
        self._timeout = timeout

    def search(self, query: str, max_results: int = 5) -> list[SearchHit]:
        if not query or not query.strip():
            return []
        from urllib.parse import quote
        import urllib.request
        import json as _json

        url = f"{self._base_url}/search?q={quote(query)}&format=json&categories=general&pageno=1"
        req = urllib.request.Request(url, headers={"User-Agent": "evidentia/0.2"})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                payload = _json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise ProviderError(f"SearXNG search failed for query='{query}': {exc}") from exc

        results = payload.get("results") or []
        hits = []
        for item in results[:max_results]:
            title = str(item.get("title") or "")
            url = str(item.get("url") or "")
            content = str(item.get("content") or "")
            if not url:
                continue
            hits.append(SearchHit(title=title, url=url, snippet=content))
        return hits


class LLMProvider:
    name: str = "unknown"

    def generate_json(self, prompt: str, model: str) -> dict[str, Any]:
        raise NotImplementedError


class NvidiaNIMProvider(LLMProvider):
    name = "nvidia"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_json(self, prompt: str, model: str) -> dict[str, Any]:
        payload = {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        }
        data = _http_json(
            url="https://integrate.api.nvidia.com/v1/chat/completions",
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}"},
            payload=payload,
        )
        return json.loads(data["choices"][0]["message"]["content"])


class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_json(self, prompt: str, model: str) -> dict[str, Any]:
        payload = {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        }
        data = _http_json(
            url="https://openrouter.ai/api/v1/chat/completions",
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}"},
            payload=payload,
        )
        return json.loads(data["choices"][0]["message"]["content"])


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_json(self, prompt: str, model: str) -> dict[str, Any]:
        payload = {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        }
        data = _http_json(
            url="https://api.groq.com/openai/v1/chat/completions",
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}"},
            payload=payload,
        )
        return json.loads(data["choices"][0]["message"]["content"])


class DuckDuckGoWebSearchProvider(SearchProvider):
    """Web search provider using DuckDuckGo's search results.
    
    Uses the duckduckgo_search library (DDGS). No API key needed.
    Falls back to SearXNG if DDGS fails.
    """
    name = "duckduckgo_web"

    def search(self, query: str, max_results: int = 5) -> list[SearchHit]:
        if not query or not query.strip():
            return []
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=max_results))
        except Exception as exc:
            raise ProviderError(f"DuckDuckGo search failed for query='{query}': {exc}") from exc

        hits = []
        for item in raw[:max_results]:
            title = str(item.get("title") or "")
            url = str(item.get("href") or "")
            snippet = str(item.get("body") or "")
            if not url:
                continue
            hits.append(SearchHit(title=title, url=url, snippet=snippet))
        return hits


class FallbackSearchProvider(SearchProvider):
    """Composite provider: SearXNG → Tavily → DuckDuckGo.

    Primary: SearXNG (localhost:8888, override via SEARXNG_URL).
    Secondary: Tavily (if TAVILY_API_KEY is set in env).
    Tertiary: DuckDuckGo Web Search.
    """
    name = "fallback"

    def __init__(self, searxng_url: str | None = None, timeout: int = 15):
        import os
        self._providers: list[SearchProvider] = []
        self._providers.append(
            SearXNGSearchProvider(
                base_url=searxng_url or os.environ.get("SEARXNG_URL", "http://127.0.0.1:8888"),
                timeout=timeout,
            )
        )
        if os.environ.get("TAVILY_API_KEY"):
            self._providers.append(TavilySearchProvider(os.environ["TAVILY_API_KEY"]))
        self._providers.append(DuckDuckGoWebSearchProvider())

    def search(self, query: str, max_results: int = 5) -> list[SearchHit]:
        errors: list[str] = []
        for provider in self._providers:
            try:
                results = provider.search(query, max_results=max_results)
                if results:
                    return results
                errors.append(f"{provider.name}: empty results")
            except ProviderError as e:
                errors.append(f"{provider.name}: {e}")
        raise ProviderError(
            f"All search providers failed for query='{query}': {'; '.join(errors)}"
        )


def choose_search_provider(env: dict[str, str] | None = None) -> SearchProvider:
    """Select search provider with automatic fallback.
    
    Always tries SearXNG first (localhost:8888 by default, override via SEARXNG_URL).
    Falls back to DuckDuckGo Web Search if SearXNG is down or rate-limited.
    """
    import os
    return FallbackSearchProvider(searxng_url=os.environ.get("SEARXNG_URL"))


def choose_llm_provider(env: dict[str, str]) -> tuple[LLMProvider, str]:
    explicit = str(env.get("LLM_PROVIDER") or "auto").strip().lower()
    if explicit == "auto":
        if env.get("NVIDIA_API_KEY"):
            return NvidiaNIMProvider(env["NVIDIA_API_KEY"]), env.get(
                "NVIDIA_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1.5"
            )
        if env.get("OPENROUTER_API_KEY"):
            return OpenRouterProvider(env["OPENROUTER_API_KEY"]), env.get(
                "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
            )
        if env.get("GROQ_API_KEY"):
            return GroqProvider(env["GROQ_API_KEY"]), env.get("GROQ_MODEL", "openai/gpt-oss-20b")
        raise ProviderError("No configured LLM provider found.")
    if explicit == "nvidia":
        return NvidiaNIMProvider(env["NVIDIA_API_KEY"]), env.get(
            "NVIDIA_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1.5"
        )
    if explicit == "openrouter":
        return OpenRouterProvider(env["OPENROUTER_API_KEY"]), env.get(
            "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
        )
    if explicit == "groq":
        return GroqProvider(env["GROQ_API_KEY"]), env.get("GROQ_MODEL", "openai/gpt-oss-20b")
    raise ProviderError(f"Unknown LLM_PROVIDER='{explicit}'.")


def build_llm_provider_chain(env: dict[str, str], fallback_chain: str | None = None) -> list[tuple[LLMProvider, str]]:
    chain_names = _parse_chain(fallback_chain or env.get("LLM_FALLBACK_CHAIN"), "nvidia,openrouter,groq")
    providers: list[tuple[LLMProvider, str]] = []
    for name in chain_names:
        local_env = dict(env)
        local_env["LLM_PROVIDER"] = name
        try:
            providers.append(choose_llm_provider(local_env))
        except ProviderError:
            continue
    if not providers:
        providers.append(choose_llm_provider(env))
    return providers


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _probe_search(env: dict[str, str], query: str, search_chain: list[str], dry_run: bool) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for candidate in search_chain:
        local_env = dict(env)
        local_env["SEARCH_PROVIDER"] = candidate
        attempt: dict[str, Any] = {"candidate": candidate, "started_at_utc": _utc_iso()}
        try:
            provider = choose_search_provider(local_env)
            attempt["resolved_provider"] = provider.name
            attempt["success"] = True
            attempt["stage"] = "select_only" if dry_run else "search"
            attempts.append(attempt)
            return {
                "success": True,
                "provider": provider.name,
                "query": query,
                "results": [],
                "attempts": attempts,
                "dry_run": dry_run,
            }
        except Exception as exc:  # noqa: BLE001
            attempt["success"] = False
            attempt["error"] = _sanitize_message(str(exc), env)
            attempts.append(attempt)
    return {"success": False, "provider": None, "query": query, "results": [], "attempts": attempts, "dry_run": dry_run}


def _probe_llm(env: dict[str, str], prompt: str, llm_chain: list[str], dry_run: bool) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for candidate in llm_chain:
        local_env = dict(env)
        local_env["LLM_PROVIDER"] = candidate
        attempt: dict[str, Any] = {"candidate": candidate, "started_at_utc": _utc_iso()}
        try:
            provider, model = choose_llm_provider(local_env)
            attempt["resolved_provider"] = provider.name
            attempt["model"] = model
            attempt["success"] = True
            attempt["stage"] = "select_only" if dry_run else "generate_json"
            attempts.append(attempt)
            return {
                "success": True,
                "provider": provider.name,
                "model": model,
                "response_json": None,
                "attempts": attempts,
                "dry_run": dry_run,
            }
        except Exception as exc:  # noqa: BLE001
            attempt["success"] = False
            attempt["error"] = _sanitize_message(str(exc), env)
            attempts.append(attempt)
    return {
        "success": False,
        "provider": None,
        "model": None,
        "response_json": None,
        "attempts": attempts,
        "dry_run": dry_run,
    }


def run_provider_smoke(
    idea: str,
    outdir: str | Path,
    dry_run: bool = False,
    llm_fallback_chain: str | None = None,
    search_fallback_chain: str | None = None,
) -> dict[str, Any]:
    env = load_external_provider_env()
    llm_chain = _parse_chain(llm_fallback_chain or env.get("LLM_FALLBACK_CHAIN"), "nvidia,openrouter,groq")
    search_chain = _parse_chain(search_fallback_chain or env.get("SEARCH_FALLBACK_CHAIN"), "duckduckgo,tavily")
    query = f"{idea} monthly spend budget currently paying"
    prompt = (
        "Return valid JSON with keys: ok (boolean), provider_hint (string), summary (string), timestamp_utc (string). "
        f'Context idea: "{idea}".'
    )

    outdir_path = Path(outdir)
    outdir_path.mkdir(parents=True, exist_ok=True)

    search_probe = _probe_search(env=env, query=query, search_chain=search_chain, dry_run=dry_run)
    llm_probe = _probe_llm(env=env, prompt=prompt, llm_chain=llm_chain, dry_run=dry_run)
    status = "ok" if search_probe["success"] and llm_probe["success"] else "partial"

    report = {
        "status": status,
        "timestamp_utc": _utc_iso(),
        "dry_run": dry_run,
        "routing": {
            "LLM_FALLBACK_CHAIN": llm_chain,
            "SEARCH_FALLBACK_CHAIN": search_chain,
        },
        "search_probe": search_probe,
        "llm_probe": llm_probe,
    }
    (outdir_path / "provider_smoke_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
