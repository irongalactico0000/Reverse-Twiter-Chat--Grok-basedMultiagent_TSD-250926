"""Event adapter + worker stub tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACK_END = Path(__file__).resolve().parents[1] / "back-end"
if str(BACK_END) not in sys.path:
    sys.path.insert(0, str(BACK_END))

from trading_bridge.event_adapter import run_stub_and_ingest  # noqa: E402
from trading_bridge.facade import TradingBridge  # noqa: E402
from trading_bridge.store import BridgeStore  # noqa: E402


def test_stub_ingest_updates_position(tmp_path):
    bridge = TradingBridge(store=BridgeStore(tmp_path / "b.sqlite"))
    result = run_stub_and_ingest(bridge)
    assert result["events"] >= 3
    assert result["positions_updated"] >= 1
    positions = {p["instrument_id"]: p["quantity"] for p in bridge.positions()}
    assert float(positions["BTCUSDT.BINANCE"]) == pytest.approx(0.20)
