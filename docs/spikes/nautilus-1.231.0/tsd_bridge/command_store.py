"""Durable TSD command identity map (Phase C foundation).

Persists: tsd_command_id -> deployment_id -> engine_client_order_id -> broker_order_id

File-backed for the first single-worker MVP. Swap the store for PostgreSQL without
changing callers.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CommandIdentity:
    tsd_command_id: str
    deployment_id: str
    engine_client_order_id: str | None = None
    broker_order_id: str | None = None
    status: str = "accepted"  # accepted | submitted | filled | rejected | duplicate


class CommandIdentityStore(Protocol):
    def get(self, tsd_command_id: str) -> CommandIdentity | None: ...
    def put_if_absent(self, identity: CommandIdentity) -> tuple[bool, CommandIdentity]:
        """Return (inserted, current). inserted=False means restart/idempotent hit."""
        ...

    def update(self, identity: CommandIdentity) -> None: ...


class JsonCommandIdentityStore:
    def __init__(self, path: Path):
        self._path = path
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self._path)

    def get(self, tsd_command_id: str) -> CommandIdentity | None:
        with self._lock:
            raw = self._load().get(tsd_command_id)
            return CommandIdentity(**raw) if raw else None

    def put_if_absent(self, identity: CommandIdentity) -> tuple[bool, CommandIdentity]:
        with self._lock:
            data = self._load()
            existing = data.get(identity.tsd_command_id)
            if existing is not None:
                return False, CommandIdentity(**existing)
            data[identity.tsd_command_id] = asdict(identity)
            self._save(data)
            return True, identity

    def update(self, identity: CommandIdentity) -> None:
        with self._lock:
            data = self._load()
            if identity.tsd_command_id not in data:
                raise KeyError(identity.tsd_command_id)
            data[identity.tsd_command_id] = asdict(identity)
            self._save(data)
