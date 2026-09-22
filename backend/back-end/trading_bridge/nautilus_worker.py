"""Nautilus paper worker — runs the spike paper_runner and emits JSONL engine events.

Replaces the pure-synthetic stub when the spike venv + paper_runner are available.
Falls back to planning-only synthetic events if Nautilus cannot be imported.

Usage:
  python -m trading_bridge.nautilus_worker \\
    --seed 0.18 --target 0.20 --command-id tsd-cmd-1 --out last_run.jsonl

Env:
  TSD_NAUTILUS_SPIKE  override path to docs/spikes/nautilus-1.231.0
  TSD_NAUTILUS_PYTHON override python for subprocess (spike .venv recommended)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SPIKE = REPO_ROOT / "docs" / "spikes" / "nautilus-1.231.0"


@dataclass
class EngineEvent:
    event_id: str
    event_type: str
    occurred_at: str
    payload: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _spike_root() -> Path:
    raw = os.getenv("TSD_NAUTILUS_SPIKE", "").strip()
    return Path(raw) if raw else DEFAULT_SPIKE


def _ensure_spike_on_path() -> Path:
    spike = _spike_root()
    if spike.exists() and str(spike) not in sys.path:
        sys.path.insert(0, str(spike))
    return spike


def plan_only_events(
    *,
    instrument_id: str,
    current_quantity: str,
    target_quantity: str,
    deployment_id: str,
    tsd_command_id: str,
) -> list[EngineEvent]:
    """Fallback when Nautilus is unavailable: still emit a coherent target→fill story."""
    _ensure_spike_on_path()
    from target_position import TargetPositionIntent, TargetType, plan_from_intent

    plan = plan_from_intent(
        TargetPositionIntent(
            instrument_id=instrument_id,
            target_type=TargetType.QUANTITY,
            target_value=Decimal(target_quantity),
            reason="nautilus-worker-fallback",
        ),
        current_quantity=Decimal(current_quantity),
    )
    engine_oid = tsd_command_id or f"NT-{uuid4().hex[:10]}"
    correlation = tsd_command_id or str(uuid4())
    return _events_from_plan(
        plan_side=plan.side,
        plan_qty=str(plan.quantity),
        current=str(plan.current_quantity),
        target=str(plan.target_quantity),
        instrument_id=instrument_id,
        deployment_id=deployment_id,
        correlation=correlation,
        engine_oid=engine_oid,
        engine="plan_only_fallback",
    )


def _events_from_plan(
    *,
    plan_side: str,
    plan_qty: str,
    current: str,
    target: str,
    instrument_id: str,
    deployment_id: str,
    correlation: str,
    engine_oid: str,
    engine: str,
) -> list[EngineEvent]:
    return [
        EngineEvent(
            event_id=str(uuid4()),
            event_type="trading.target.planned.v1",
            occurred_at=_now(),
            payload={
                "deployment_id": deployment_id,
                "correlation_id": correlation,
                "tsd_command_id": correlation,
                "engine": engine,
                "plan": {
                    "instrument_id": instrument_id,
                    "side": plan_side,
                    "quantity": plan_qty,
                    "current_quantity": current,
                    "target_quantity": target,
                },
            },
        ),
        EngineEvent(
            event_id=str(uuid4()),
            event_type="trading.order.submitted.v1",
            occurred_at=_now(),
            payload={
                "deployment_id": deployment_id,
                "correlation_id": correlation,
                "tsd_command_id": correlation,
                "engine_client_order_id": engine_oid,
                "side": plan_side,
                "quantity": plan_qty,
                "engine": engine,
            },
        ),
        EngineEvent(
            event_id=str(uuid4()),
            event_type="trading.order.filled.v1",
            occurred_at=_now(),
            payload={
                "deployment_id": deployment_id,
                "correlation_id": correlation,
                "tsd_command_id": correlation,
                "engine_client_order_id": engine_oid,
                "filled_quantity": plan_qty,
                "position_after": target,
                "engine": engine,
            },
        ),
        EngineEvent(
            event_id=str(uuid4()),
            event_type="trading.position.updated.v1",
            occurred_at=_now(),
            payload={
                "deployment_id": deployment_id,
                "correlation_id": correlation,
                "instrument_id": instrument_id,
                "quantity": target,
                "engine": engine,
            },
        ),
    ]


def run_nautilus_paper(
    *,
    instrument_id: str,
    current_quantity: str,
    target_quantity: str,
    deployment_id: str,
    tsd_command_id: str,
) -> list[EngineEvent]:
    """In-process: use spike PaperTargetRunner (requires nautilus_trader in this interpreter)."""
    spike = _ensure_spike_on_path()
    from tsd_bridge.command_store import JsonCommandIdentityStore
    from tsd_bridge.paper_runner import PaperTargetRequest, PaperTargetRunner

    runner = PaperTargetRunner(
        JsonCommandIdentityStore(spike / "artifacts" / "worker_command_identity.json"),
    )
    result = runner.run(
        PaperTargetRequest(
            tsd_command_id=tsd_command_id or f"worker-{uuid4().hex[:8]}",
            deployment_id=deployment_id,
            seed_quantity=current_quantity,
            target_quantity=target_quantity,
            instrument=instrument_id,
        ),
    )
    plans = result.evidence.get("plans") or []
    plan0 = plans[0] if plans else {
        "side": "BUY",
        "qty": str(Decimal(target_quantity) - Decimal(current_quantity)),
        "current": current_quantity,
        "target": target_quantity,
    }
    engine_oid = result.identity.engine_client_order_id or tsd_command_id
    return _events_from_plan(
        plan_side=plan0.get("side", "BUY"),
        plan_qty=str(plan0.get("qty", "0")),
        current=str(plan0.get("current", current_quantity)),
        target=str(result.evidence.get("final_position", target_quantity)),
        instrument_id=instrument_id,
        deployment_id=deployment_id,
        correlation=tsd_command_id,
        engine_oid=engine_oid,
        engine="nautilus_trader_paper_runner",
    )


def emit_target_cycle(
    *,
    instrument_id: str = "BTCUSDT.BINANCE",
    current_quantity: str = "0.18",
    target_quantity: str = "0.20",
    deployment_id: str = "paper-worker-1",
    tsd_command_id: str | None = None,
) -> list[EngineEvent]:
    cmd = tsd_command_id or f"tsd-worker-{uuid4().hex[:10]}"
    try:
        return run_nautilus_paper(
            instrument_id=instrument_id,
            current_quantity=current_quantity,
            target_quantity=target_quantity,
            deployment_id=deployment_id,
            tsd_command_id=cmd,
        )
    except Exception as exc:  # noqa: BLE001 — worker must still emit a story
        events = plan_only_events(
            instrument_id=instrument_id,
            current_quantity=current_quantity,
            target_quantity=target_quantity,
            deployment_id=deployment_id,
            tsd_command_id=cmd,
        )
        events.insert(
            0,
            EngineEvent(
                event_id=str(uuid4()),
                event_type="trading.worker.fallback.v1",
                occurred_at=_now(),
                payload={"error": str(exc), "engine": "plan_only_fallback"},
            ),
        )
        return events


def write_events(path: Path, events: Iterable[EngineEvent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(event.to_json() + "\n")


def run_as_subprocess(
    *,
    current_quantity: str,
    target_quantity: str,
    tsd_command_id: str,
    out: Path,
) -> subprocess.CompletedProcess[str]:
    """Launch this module with the spike venv python when available."""
    spike = _spike_root()
    py = os.getenv("TSD_NAUTILUS_PYTHON", "").strip()
    if not py:
        candidate = spike / ".venv" / "Scripts" / "python.exe"
        if not candidate.exists():
            candidate = spike / ".venv" / "bin" / "python"
        py = str(candidate) if candidate.exists() else sys.executable

    cmd = [
        py,
        "-m",
        "trading_bridge.nautilus_worker",
        "--seed",
        current_quantity,
        "--target",
        target_quantity,
        "--command-id",
        tsd_command_id,
        "--out",
        str(out),
    ]
    env = os.environ.copy()
    # Ensure backend package is importable
    backend = str(REPO_ROOT / "backend" / "back-end")
    env["PYTHONPATH"] = backend + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(cmd, check=False, capture_output=True, text=True, env=env)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TSD Nautilus paper worker")
    parser.add_argument("--seed", default="0.18")
    parser.add_argument("--target", default="0.20")
    parser.add_argument("--instrument", default="BTCUSDT.BINANCE")
    parser.add_argument("--deployment-id", default="paper-worker-1")
    parser.add_argument("--command-id", default="")
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parent / "last_run.jsonl"),
    )
    args = parser.parse_args(argv)

    events = emit_target_cycle(
        instrument_id=args.instrument,
        current_quantity=args.seed,
        target_quantity=args.target,
        deployment_id=args.deployment_id,
        tsd_command_id=args.command_id or None,
    )
    out = Path(args.out)
    write_events(out, events)
    for event in events:
        print(event.to_json())
    print(f"WROTE {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
