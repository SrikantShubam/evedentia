from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from evidentia.models import PlayerProfile, TournamentResult


DEFAULT_DB_PATH = Path("outputs") / "evidentia.sqlite3"


def _connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    resolved = Path(db_path) if db_path else DEFAULT_DB_PATH
    resolved.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(resolved))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path | None = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_profiles (
                id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tournaments (
                tournament_id TEXT PRIMARY KEY,
                player_id TEXT NOT NULL,
                gate_profile TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                memo_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS idea_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id TEXT NOT NULL,
                idea_id TEXT NOT NULL,
                terminal_verdict TEXT,
                confidence_score REAL NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gate_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id TEXT NOT NULL,
                idea_id TEXT NOT NULL,
                gate_name TEXT NOT NULL,
                status TEXT NOT NULL,
                outcome TEXT,
                confidence REAL,
                llm_cost_usd REAL NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )


def upsert_player_profile(profile: PlayerProfile, *, db_path: str | Path | None = None, now_utc: str) -> None:
    payload = json.dumps(profile.to_dict(), sort_keys=True)
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO player_profiles (id, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (profile.id, payload, now_utc, now_utc),
        )


def get_player_profile(player_id: str, *, db_path: str | Path | None = None) -> PlayerProfile | None:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT payload_json FROM player_profiles WHERE id = ?", (player_id,)).fetchone()
    if row is None:
        return None
    return PlayerProfile(**json.loads(row["payload_json"]))


def save_tournament_result(result: TournamentResult, *, db_path: str | Path | None = None, now_utc: str) -> None:
    payload = result.to_dict()
    payload_json = json.dumps(payload, sort_keys=True)
    memo_json = json.dumps(payload.get("memo") or {}, sort_keys=True)
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO tournaments (tournament_id, player_id, gate_profile, payload_json, memo_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                result.tournament_id,
                result.player_id,
                result.gate_profile,
                payload_json,
                memo_json,
                now_utc,
            ),
        )
        conn.execute("DELETE FROM idea_states WHERE tournament_id = ?", (result.tournament_id,))
        conn.execute("DELETE FROM gate_results WHERE tournament_id = ?", (result.tournament_id,))
        for state in payload["ideas"]:
            idea = state["idea"]
            conn.execute(
                """
                INSERT INTO idea_states (tournament_id, idea_id, terminal_verdict, confidence_score, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    result.tournament_id,
                    idea["id"],
                    state.get("terminal_verdict"),
                    float(state.get("confidence_score_so_far") or 0.0),
                    json.dumps(state, sort_keys=True),
                ),
            )
            for gate in state.get("gate_results", []):
                conn.execute(
                    """
                    INSERT INTO gate_results (tournament_id, idea_id, gate_name, status, outcome, confidence, llm_cost_usd, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result.tournament_id,
                        idea["id"],
                        gate["gate_name"],
                        gate["status"],
                        gate.get("outcome"),
                        gate.get("confidence"),
                        float(gate.get("llm_cost_usd") or 0.0),
                        json.dumps(gate, sort_keys=True),
                    ),
                )


def get_tournament_payload(tournament_id: str, *, db_path: str | Path | None = None) -> dict | None:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT payload_json FROM tournaments WHERE tournament_id = ?", (tournament_id,)).fetchone()
    if row is None:
        return None
    return json.loads(row["payload_json"])


def get_tournament_memo(tournament_id: str, *, db_path: str | Path | None = None) -> dict | None:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT memo_json FROM tournaments WHERE tournament_id = ?", (tournament_id,)).fetchone()
    if row is None:
        return None
    return json.loads(row["memo_json"])


def list_tournament_gate_events(tournament_id: str, *, db_path: str | Path | None = None) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT idea_id, gate_name, status, outcome, confidence, llm_cost_usd, payload_json
            FROM gate_results
            WHERE tournament_id = ?
            ORDER BY id ASC
            """,
            (tournament_id,),
        ).fetchall()
    events: list[dict] = []
    for row in rows:
        payload = json.loads(row["payload_json"])
        payload["idea_id"] = row["idea_id"]
        events.append(payload)
    return events
