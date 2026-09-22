"""SQLite command identity + proposal store for the paper bridge MVP."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class BridgeStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS commands (
                    tsd_command_id TEXT PRIMARY KEY,
                    deployment_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    intent_fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL,
                    engine_client_order_id TEXT,
                    broker_order_id TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS positions (
                    instrument_id TEXT PRIMARY KEY,
                    quantity TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                """
            )

    def upsert_proposal(self, proposal_id: str, payload: dict[str, Any]) -> None:
        now = time.time()
        blob = json.dumps(payload, default=str)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO proposals (proposal_id, payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(proposal_id) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (proposal_id, blob, now, now),
            )

    def get_proposal(self, proposal_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM proposals WHERE proposal_id = ?",
                (proposal_id,),
            ).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def list_proposals(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM proposals ORDER BY created_at DESC"
            ).fetchall()
        return [json.loads(r["payload_json"]) for r in rows]

    def begin_command(
        self,
        *,
        tsd_command_id: str,
        deployment_id: str,
        idempotency_key: str,
        intent_fingerprint: str,
    ) -> tuple[dict[str, Any], bool]:
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT * FROM commands WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing:
                return dict(existing), False
            now = time.time()
            conn.execute(
                """
                INSERT INTO commands (
                    tsd_command_id, deployment_id, idempotency_key, intent_fingerprint,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'RECEIVED', ?, ?)
                """,
                (
                    tsd_command_id,
                    deployment_id,
                    idempotency_key,
                    intent_fingerprint,
                    now,
                    now,
                ),
            )
            row = conn.execute(
                "SELECT * FROM commands WHERE tsd_command_id = ?",
                (tsd_command_id,),
            ).fetchone()
            return dict(row), True

    def mark_command_submitted(
        self,
        tsd_command_id: str,
        *,
        engine_client_order_id: str,
        broker_order_id: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE commands
                SET status = 'SUBMITTED',
                    engine_client_order_id = ?,
                    broker_order_id = ?,
                    updated_at = ?
                WHERE tsd_command_id = ?
                """,
                (engine_client_order_id, broker_order_id, time.time(), tsd_command_id),
            )

    def get_position(self, instrument_id: str) -> DecimalStr:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT quantity FROM positions WHERE instrument_id = ?",
                (instrument_id,),
            ).fetchone()
        return row["quantity"] if row else "0"

    def set_position(self, instrument_id: str, quantity: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO positions (instrument_id, quantity, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(instrument_id) DO UPDATE SET
                    quantity = excluded.quantity,
                    updated_at = excluded.updated_at
                """,
                (instrument_id, quantity, time.time()),
            )

    def list_positions(self) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT instrument_id, quantity FROM positions").fetchall()
        return [{"instrument_id": r["instrument_id"], "quantity": r["quantity"]} for r in rows]

    def append_event(self, event_type: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events (event_type, payload_json, created_at) VALUES (?, ?, ?)",
                (event_type, json.dumps(payload, default=str), time.time()),
            )

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT event_id, event_type, payload_json, created_at FROM events ORDER BY event_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "event_id": r["event_id"],
                "event_type": r["event_type"],
                "payload": json.loads(r["payload_json"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]


# typing alias for readability in get_position return
DecimalStr = str
