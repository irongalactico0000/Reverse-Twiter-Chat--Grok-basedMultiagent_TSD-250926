"""Adapt engine JSONL events into the TSD bridge store / positions."""
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from .facade import TradingBridge, get_bridge


def ingest_jsonl(path: Path, bridge: TradingBridge | None = None) -> dict:
    bridge = bridge or get_bridge()
    counts = {"events": 0, "positions_updated": 0, "orders": 0}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            et = event.get("event_type", "")
            payload = event.get("payload", {})
            bridge.store.append_event(et, payload)
            counts["events"] += 1

            if et == "trading.order.submitted.v1":
                counts["orders"] += 1
                oid = payload.get("engine_client_order_id")
                if oid:
                    cmd, _created = bridge.store.begin_command(
                        tsd_command_id=str(uuid4()),
                        deployment_id=str(payload.get("deployment_id", "worker")),
                        idempotency_key=f"engine:{oid}",
                        intent_fingerprint=json.dumps(payload, sort_keys=True),
                    )
                    bridge.store.mark_command_submitted(
                        cmd["tsd_command_id"],
                        engine_client_order_id=oid,
                    )

            if et == "trading.position.updated.v1":
                bridge.store.set_position(
                    payload["instrument_id"],
                    str(payload["quantity"]),
                )
                counts["positions_updated"] += 1
    return counts


def run_stub_and_ingest(bridge: TradingBridge | None = None) -> dict:
    from . import nautilus_worker as worker

    bridge = bridge or get_bridge()
    out = Path(__file__).resolve().parent / "last_run.jsonl"
    worker.write_events(
        out,
        worker.emit_target_cycle(
            current_quantity="0.18",
            target_quantity="0.20",
            tsd_command_id=f"ingest-{uuid4().hex[:8]}",
        ),
    )
    result = ingest_jsonl(out, bridge=bridge)
    result["positions"] = bridge.positions()
    result["jsonl"] = str(out)
    return result


def main() -> None:
    print("INGESTED", run_stub_and_ingest())


if __name__ == "__main__":
    main()
