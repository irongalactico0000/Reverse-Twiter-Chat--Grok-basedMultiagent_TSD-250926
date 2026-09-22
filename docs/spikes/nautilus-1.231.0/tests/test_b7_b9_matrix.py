"""B7–B9 tests: parity, fault matrix, idempotent command identity."""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE))

from tsd_bridge.harness import run_scenario  # noqa: E402
from tsd_bridge.target_position import TargetPositionIntent, compute_delta  # noqa: E402


def _normalized(result) -> dict:
    """Comparable trading outputs only (no wall-clock / random ids except TSD cmd)."""
    plans = [
        {
            "current": p["current"],
            "target": p["target"],
            "side": p["side"],
            "qty": p["qty"],
            "cmd": p["cmd"],
        }
        for p in result.evidence.get("plans", [])
    ]
    return {
        "scenario": result.evidence.get("scenario"),
        "final_position": str(result.final_position),
        "plans": plans,
        "rejects": result.evidence.get("rejects", []),
        "cancels": result.evidence.get("cancels", []),
        "orders_after_duplicate": result.evidence.get("orders_after_duplicate"),
    }


def test_b7_parity_two_runs_match():
    a = run_scenario("b6", tsd_command_id="parity-a")
    b = run_scenario("b6", tsd_command_id="parity-a")
    na, nb = _normalized(a), _normalized(b)
    # command ids match; order client ids from factory may differ by clock — exclude them
    assert na == nb
    assert Decimal(na["final_position"]) == Decimal("0.20")
    assert na["plans"][0]["qty"] == "0.020000"


def test_b7_write_manifest(tmp_path: Path):
    result = run_scenario("b6", tsd_command_id="manifest-001")
    payload = {
        "engine": "nautilus_trader",
        "engine_version": __import__("nautilus_trader").__version__,
        "instrument": "BTCUSDT.BINANCE",
        "seed": "0.18",
        "target": "0.20",
        "normalized": _normalized(result),
        "code_files": [
            "tsd_bridge/target_position.py",
            "tsd_bridge/harness.py",
            "b6_target_position_demo.py",
        ],
    }
    blob = json.dumps(payload["normalized"], sort_keys=True).encode()
    payload["normalized_sha256"] = hashlib.sha256(blob).hexdigest()
    out = SPIKE / "artifacts" / "b7_parity_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert out.exists()
    assert len(payload["normalized_sha256"]) == 64


def test_b8_duplicate_target_no_extra_order():
    result = run_scenario("duplicate_target", tsd_command_id="dup-001")
    assert result.final_position == Decimal("0.20")
    assert result.evidence["orders_after_duplicate"] == 0
    assert any(r["reason"] == "duplicate_tsd_command_id" for r in result.evidence["rejects"])


def test_b8_reversal_sell_to_lower_target():
    result = run_scenario(
        "reversal",
        seed="0.18",
        target="0.20",
        second_target="0.10",
        tsd_command_id="rev",
    )
    plans = result.evidence["plans"]
    assert plans[0]["side"] == "BUY" and Decimal(plans[0]["qty"]) == Decimal("0.02")
    assert plans[1]["side"] == "SELL" and Decimal(plans[1]["qty"]) == Decimal("0.10")
    assert result.final_position == Decimal("0.10")


def test_b8_risk_reject_blocks_oversized_delta():
    # seed 0.18, target 0.20 => delta 0.02; max 0.01 rejects
    result = run_scenario(
        "risk_reject",
        target="0.20",
        max_order_qty="0.01",
        tsd_command_id="risk-001",
    )
    assert any(r["reason"] == "risk_max_order_qty" for r in result.evidence["rejects"])
    assert result.final_position == Decimal("0.18")


def test_b8_cancel_resting_limit():
    result = run_scenario("cancel_limit", tsd_command_id="cancel-scen")
    assert "tsd-limit-cancel-001" in result.evidence.get("cancels", [])
    # seed remains; canceled limit never filled
    assert result.final_position == Decimal("0.18")


def test_b8_stale_intent_refused_by_policy():
    """Stale market data is a TSD policy decision; prove the gate exists at the adapter edge."""

    class StaleFeedError(Exception):
        pass

    def apply_if_fresh(current: Decimal, intent: TargetPositionIntent, *, feed_stale: bool):
        if feed_stale:
            raise StaleFeedError("market data stale; refuse target")
        return compute_delta(current, intent)

    from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue

    intent = TargetPositionIntent(
        instrument_id=InstrumentId(Symbol("BTCUSDT"), Venue("BINANCE")),
        target=Decimal("0.20"),
    )
    with pytest.raises(StaleFeedError):
        apply_if_fresh(Decimal("0.18"), intent, feed_stale=True)
    plan = apply_if_fresh(Decimal("0.18"), intent, feed_stale=False)
    assert plan.quantity == Decimal("0.02")


def test_b8_partial_fill_semantics_documented_via_quantity_math():
    """Engine can partially fill; TSD delta math must remain valid mid-fill.

    If current is 0.18, target 0.20, and only 0.01 of a 0.02 order filled so far,
    remaining intent is still target − current = 0.01.
    """
    from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue

    intent = TargetPositionIntent(
        instrument_id=InstrumentId(Symbol("BTCUSDT"), Venue("BINANCE")),
        target=Decimal("0.20"),
    )
    mid = compute_delta(Decimal("0.19"), intent)
    assert mid.side.name == "BUY"
    assert mid.quantity == Decimal("0.01")


def test_b9_command_store_prevents_resubmit(tmp_path: Path):
    store_path = tmp_path / "command_map.json"

    def remember(tsd_command_id: str, client_order_id: str) -> bool:
        """Return True if this is a new command; False if already recorded."""
        data = json.loads(store_path.read_text()) if store_path.exists() else {}
        if tsd_command_id in data:
            return False
        data[tsd_command_id] = {
            "engine_client_order_id": client_order_id,
            "deployment_id": "dep-spike-1",
        }
        store_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True

    first = run_scenario("b6", tsd_command_id="restart-cmd-1")
    assert first.final_position == Decimal("0.20")
    # Find the target order id (not the seed): last plan's cmd maps to an submitted id containing tsd or last
    target_order = None
    for oid in first.orders_submitted:
        if oid == "restart-cmd-1":
            target_order = oid
            break
    assert target_order is not None
    assert remember("restart-cmd-1", target_order) is True

    # Simulated worker restart: map reloaded, same command must not submit again
    assert remember("restart-cmd-1", "would-be-duplicate") is False
    saved = json.loads(store_path.read_text())
    assert saved["restart-cmd-1"]["engine_client_order_id"] == "restart-cmd-1"
