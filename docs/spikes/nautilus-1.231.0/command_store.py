"""SQLite-backed command identity store for restart / idempotency demos.

Maps:
  tsd_command_id <-> deployment_id <-> engine_client_order_id <-> broker_order_id
"""
from __future__ import annotations

import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CommandRecord:
    tsd_command_id: str
    deployment_id: str
    idempotency_key: str
    intent_fingerprint: str
    status: str
    engine_client_order_id: str | None = None
    broker_order_id: str | None = None
    created_at: float = 0.0
    updated_at: float = 0.0


class CommandStore:
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
            conn.execute(
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
                )
                """
            )

    def get_by_idempotency(self, key: str) -> CommandRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM commands WHERE idempotency_key = ?",
                (key,),
            ).fetchone()
        return self._row(row) if row else None

    def get(self, tsd_command_id: str) -> CommandRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM commands WHERE tsd_command_id = ?",
                (tsd_command_id,),
            ).fetchone()
        return self._row(row) if row else None

    def begin(
        self,
        *,
        deployment_id: str,
        idempotency_key: str,
        intent_fingerprint: str,
    ) -> tuple[CommandRecord, bool]:
        """Return (record, created). If key exists, return existing without creating."""
        existing = self.get_by_idempotency(idempotency_key)
        if existing:
            return existing, False

        now = time.time()
        record = CommandRecord(
            tsd_command_id=str(uuid.uuid4()),
            deployment_id=deployment_id,
            idempotency_key=idempotency_key,
            intent_fingerprint=intent_fingerprint,
            status="RECEIVED",
            created_at=now,
            updated_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO commands (
                    tsd_command_id, deployment_id, idempotency_key, intent_fingerprint,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.tsd_command_id,
                    record.deployment_id,
                    record.idempotency_key,
                    record.intent_fingerprint,
                    record.status,
                    record.created_at,
                    record.updated_at,
                ),
            )
        return record, True

    def mark_submitted(
        self,
        tsd_command_id: str,
        *,
        engine_client_order_id: str,
        broker_order_id: str | None = None,
    ) -> CommandRecord:
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE commands
                SET status = ?, engine_client_order_id = ?, broker_order_id = ?, updated_at = ?
                WHERE tsd_command_id = ?
                """,
                (
                    "SUBMITTED",
                    engine_client_order_id,
                    broker_order_id,
                    now,
                    tsd_command_id,
                ),
            )
        record = self.get(tsd_command_id)
        assert record is not None
        return record

    def resolve_after_restart(self, idempotency_key: str) -> CommandRecord | None:
        """Worker restart path: look up existing identity before any new submit."""
        return self.get_by_idempotency(idempotency_key)

    @staticmethod
    def _row(row: sqlite3.Row) -> CommandRecord:
        return CommandRecord(
            tsd_command_id=row["tsd_command_id"],
            deployment_id=row["deployment_id"],
            idempotency_key=row["idempotency_key"],
            intent_fingerprint=row["intent_fingerprint"],
            status=row["status"],
            engine_client_order_id=row["engine_client_order_id"],
            broker_order_id=row["broker_order_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
