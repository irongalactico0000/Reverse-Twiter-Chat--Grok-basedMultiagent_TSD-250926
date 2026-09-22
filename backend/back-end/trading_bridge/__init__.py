"""TSD trading bridge — target-position facade over (future) engine execution.

Prototype path: plans deltas, risk-checks, persists command identities, and
records paper ledger events locally. Does not call live brokers.
"""
from __future__ import annotations

from .facade import TradingBridge
from .models import (
    ApprovalRequest,
    ProposalStatus,
    TargetProposal,
    TargetPositionRequest,
)

__all__ = [
    "TradingBridge",
    "TargetPositionRequest",
    "TargetProposal",
    "ApprovalRequest",
    "ProposalStatus",
]
