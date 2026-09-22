from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class TargetType(str, Enum):
    quantity = "quantity"
    weight = "weight"
    notional = "notional"


class ProposalStatus(str, Enum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    executed_paper = "executed_paper"
    risk_rejected = "risk_rejected"
    expired = "expired"


class TargetPositionRequest(BaseModel):
    instrument_id: str = Field(examples=["BTCUSDT.BINANCE"])
    target_type: TargetType = TargetType.quantity
    target_value: Decimal = Field(examples=["0.20"])
    current_quantity: Decimal = Field(default=Decimal("0"))
    portfolio_equity: Decimal | None = None
    mark_price: Decimal | None = None
    deployment_id: str = "paper-default"
    strategy_id: str = "manual"
    strategy_version: str = "0.0.0"
    reason: str = ""
    idempotency_key: str | None = None
    correlation_id: str | None = None


class DerivedPlanView(BaseModel):
    instrument_id: str
    side: Literal["BUY", "SELL", "FLAT"]
    quantity: Decimal
    current_quantity: Decimal
    target_quantity: Decimal
    reason: str


class RiskDecisionView(BaseModel):
    accepted: bool
    reasons: list[str] = []


class TargetProposal(BaseModel):
    proposal_id: str
    status: ProposalStatus
    request: TargetPositionRequest
    plan: DerivedPlanView
    risk: RiskDecisionView
    tsd_command_id: str | None = None
    engine_client_order_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ApprovalRequest(BaseModel):
    proposal_id: str
    approve: bool = True
    note: str = ""


def new_id() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
