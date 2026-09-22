"""Bridge facade unit tests (paper propose → approve → idempotent fill)."""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

BACK_END = Path(__file__).resolve().parents[1] / "back-end"
if str(BACK_END) not in sys.path:
    sys.path.insert(0, str(BACK_END))

from trading_bridge.facade import TradingBridge  # noqa: E402
from trading_bridge.models import (  # noqa: E402
    ApprovalRequest,
    ProposalStatus,
    TargetPositionRequest,
    TargetType,
)
from trading_bridge.store import BridgeStore  # noqa: E402


@pytest.fixture()
def bridge(tmp_path):
    return TradingBridge(store=BridgeStore(tmp_path / "bridge.sqlite"))


def test_propose_approve_paper_fill(bridge: TradingBridge):
    proposal = bridge.propose(
        TargetPositionRequest(
            instrument_id="BTCUSDT.BINANCE",
            target_type=TargetType.quantity,
            target_value=Decimal("0.20"),
            current_quantity=Decimal("0.18"),
            reason="test",
        )
    )
    assert proposal.status == ProposalStatus.proposed
    assert proposal.plan.side == "BUY"
    assert proposal.plan.quantity == Decimal("0.02")

    executed = bridge.approve(ApprovalRequest(proposal_id=proposal.proposal_id, approve=True))
    assert executed.status == ProposalStatus.executed_paper
    assert executed.engine_client_order_id
    positions = {p["instrument_id"]: p["quantity"] for p in bridge.positions()}
    assert positions["BTCUSDT.BINANCE"] == "0.20"


def test_command_store_restart_no_duplicate(bridge: TradingBridge):
    cmd1, created1 = bridge.store.begin_command(
        tsd_command_id="cmd-1",
        deployment_id="d1",
        idempotency_key="idem-1",
        intent_fingerprint="fp",
    )
    assert created1 is True
    bridge.store.mark_command_submitted("cmd-1", engine_client_order_id="ENGINE-1")

    cmd2, created2 = bridge.store.begin_command(
        tsd_command_id="cmd-2",
        deployment_id="d1",
        idempotency_key="idem-1",
        intent_fingerprint="fp",
    )
    assert created2 is False
    assert cmd2["tsd_command_id"] == "cmd-1"
    assert cmd2["engine_client_order_id"] == "ENGINE-1"


def test_risk_rejects_oversized(bridge: TradingBridge):
    bridge.max_order_qty = Decimal("0.01")
    proposal = bridge.propose(
        TargetPositionRequest(
            instrument_id="BTCUSDT.BINANCE",
            target_type=TargetType.quantity,
            target_value=Decimal("0.20"),
            current_quantity=Decimal("0.18"),
        )
    )
    assert proposal.status == ProposalStatus.risk_rejected


def test_kill_switch_blocks(bridge: TradingBridge):
    bridge.set_kill_switch(True)
    proposal = bridge.propose(
        TargetPositionRequest(
            instrument_id="BTCUSDT.BINANCE",
            target_type=TargetType.quantity,
            target_value=Decimal("0.20"),
            current_quantity=Decimal("0.18"),
        )
    )
    assert proposal.status == ProposalStatus.risk_rejected
    assert any("kill_switch" in r for r in proposal.risk.reasons)
