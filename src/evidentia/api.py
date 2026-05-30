from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from evidentia.anchor import load_all_anchors
from evidentia.cli import _run_hunt, run_live_scan
from evidentia.db import (
    get_player_profile,
    get_tournament_memo,
    get_tournament_payload,
    init_db,
    list_tournament_gate_events,
    save_tournament_result,
    upsert_player_profile,
)
from evidentia.generator import generate_ideas_from_anchor, generate_ideas_from_pursue
from evidentia.models import Idea, PlayerProfile, TournamentResult
from evidentia.tournament.engine import run_tournament


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class HarvestRequest(BaseModel):
    anchor_slug: str
    limit: int = 20
    dry_run: bool = False


class GenerateRequest(BaseModel):
    anchor_slug: str | None = None
    from_pursues: bool = False
    count: int = 10
    pursue_entries: list[dict] = Field(default_factory=list)


class TournamentRequest(BaseModel):
    tournament_id: str
    player_id: str
    ideas: list[dict]
    gate_profile: str | None = None


class ScanRequest(BaseModel):
    keyword: str
    sources: list[str] = Field(default_factory=lambda: ["hn"])
    max_results: int = 3


def create_app(*, db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Evidentia API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.1.4:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_db(db_path)

    # Seed default player (used by dashboard's hardcoded player_id: "default")
    try:
        default_player = PlayerProfile(
            id="default",
            team="default",
            skills=["research"],
            budget_validate_usd=500,
            budget_build_usd=2000,
            budget_reach_usd=300,
            weeks_to_ship=8,
            risk="low",
        )
        upsert_player_profile(default_player, db_path=db_path, now_utc=_utc_now())
    except Exception:
        pass  # already exists or race

    @app.post("/player")
    def post_player(payload: dict) -> dict:
        profile = PlayerProfile(**payload)
        upsert_player_profile(profile, db_path=db_path, now_utc=_utc_now())
        return {"id": profile.id}

    @app.get("/player/{player_id}")
    def get_player(player_id: str) -> dict:
        profile = get_player_profile(player_id, db_path=db_path)
        if profile is None:
            raise HTTPException(status_code=404, detail="player not found")
        return profile.to_dict()

    @app.post("/harvest")
    def post_harvest(request: HarvestRequest) -> dict:
        anchors = load_all_anchors()
        anchor = next((item for item in anchors if item.slug == request.anchor_slug), None)
        if anchor is None:
            raise HTTPException(status_code=404, detail="anchor not found")
        return _run_hunt(anchor, limit=request.limit, dry_run=request.dry_run)

    @app.post("/generate")
    def post_generate(request: GenerateRequest) -> dict:
        if request.from_pursues:
            ideas = generate_ideas_from_pursue(request.pursue_entries, count=request.count)
            return {"ideas": ideas}
        anchors = load_all_anchors()
        if request.anchor_slug is None:
            raise HTTPException(status_code=400, detail="anchor_slug is required unless from_pursues=true")
        anchor = next((item for item in anchors if item.slug == request.anchor_slug), None)
        if anchor is None:
            raise HTTPException(status_code=404, detail="anchor not found")
        ideas = generate_ideas_from_anchor(anchor, count=request.count)
        return {"ideas": ideas}

    @app.post("/tournament")
    def post_tournament(request: TournamentRequest) -> dict:
        profile = get_player_profile(request.player_id, db_path=db_path)
        if profile is None:
            raise HTTPException(status_code=404, detail="player not found")
        ideas = [Idea(**payload) for payload in request.ideas]
        result: TournamentResult = run_tournament(
            ideas=ideas,
            player=profile,
            tournament_id=request.tournament_id,
            gate_profile=request.gate_profile,
        )
        save_tournament_result(result, db_path=db_path, now_utc=_utc_now())
        return result.to_dict()

    @app.get("/tournament/{tournament_id}")
    def get_tournament(tournament_id: str) -> dict:
        payload = get_tournament_payload(tournament_id, db_path=db_path)
        if payload is None:
            raise HTTPException(status_code=404, detail="tournament not found")
        return payload

    @app.get("/tournament/{tournament_id}/idea/{idea_id}")
    def get_tournament_idea(tournament_id: str, idea_id: str) -> dict:
        payload = get_tournament_payload(tournament_id, db_path=db_path)
        if payload is None:
            raise HTTPException(status_code=404, detail="tournament not found")
        for state in payload.get("ideas", []):
            idea = state.get("idea") or {}
            if idea.get("id") == idea_id:
                return state
        raise HTTPException(status_code=404, detail="idea not found")

    @app.get("/tournament/{tournament_id}/memo")
    def get_tournament_memo_route(tournament_id: str) -> dict:
        memo = get_tournament_memo(tournament_id, db_path=db_path)
        if memo is None:
            raise HTTPException(status_code=404, detail="tournament not found")
        return memo

    @app.get("/tournament/{tournament_id}/sse")
    async def tournament_sse(tournament_id: str):
        payload = get_tournament_payload(tournament_id, db_path=db_path)
        if payload is None:
            raise HTTPException(status_code=404, detail="tournament not found")
        events = list_tournament_gate_events(tournament_id, db_path=db_path)

        async def generator():
            for event in events:
                yield {"event": "gate", "data": event}
            yield {"event": "done", "data": {"tournament_id": tournament_id}}

        return EventSourceResponse(generator())

    @app.post("/scan")
    def post_scan(request: ScanRequest) -> dict:
        if not request.keyword.strip():
            raise HTTPException(status_code=400, detail="keyword is required")
        valid_sources = [s for s in request.sources if s in {"hn", "reddit", "github"}]
        if not valid_sources:
            raise HTTPException(status_code=400, detail="at least one valid source is required (hn, reddit, github)")
        try:
            return run_live_scan(
                domain=request.keyword.strip(),
                sources=valid_sources,
                max_results=request.max_results,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()
