"""Demonstrate restart does not duplicate submission for the same idempotency key."""
from __future__ import annotations

from pathlib import Path
import tempfile

from command_store import CommandStore


def simulate_worker(store: CommandStore, idem_key: str) -> str:
    record, created = store.begin(
        deployment_id="deploy-paper-1",
        idempotency_key=idem_key,
        intent_fingerprint="BTCUSDT.BINANCE|quantity|0.20|from:0.18",
    )
    if not created:
        # Restart path: existing identity found — do not submit again.
        assert record.engine_client_order_id is not None
        return f"REUSED:{record.engine_client_order_id}"

    # First pass: pretend engine accepted with client order id
    store.mark_submitted(record.tsd_command_id, engine_client_order_id="ENGINE-OID-1")
    return f"SUBMITTED:ENGINE-OID-1"


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    try:
        db = tmp / "commands.sqlite"
        store1 = CommandStore(db)
        first = simulate_worker(store1, "idem-btc-001")
        assert first.startswith("SUBMITTED:")

        store2 = CommandStore(db)
        second = simulate_worker(store2, "idem-btc-001")
        assert second == "REUSED:ENGINE-OID-1", second

        resolved = store2.resolve_after_restart("idem-btc-001")
        assert resolved is not None
        assert resolved.status == "SUBMITTED"
        assert resolved.engine_client_order_id == "ENGINE-OID-1"
        print("PASS restart resolves existing identity; no duplicate submit")
    finally:
        # Windows may keep a short lock; ignore cleanup errors.
        import shutil

        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    main()
