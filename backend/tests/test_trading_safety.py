"""Unit tests for fail-closed trading safety gates."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

SAFETY_PATH = (
    Path(__file__).resolve().parents[1] / "back-end" / "trading" / "safety.py"
)
_spec = importlib.util.spec_from_file_location("trading_safety_under_test", SAFETY_PATH)
assert _spec and _spec.loader
safety = importlib.util.module_from_spec(_spec)
sys.modules["trading_safety_under_test"] = safety
_spec.loader.exec_module(safety)


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch):
    safety.clear_safety_cache()
    monkeypatch.delenv("TRADING_MUTATIONS_ENABLED", raising=False)
    monkeypatch.delenv("TRADING_API_TOKEN", raising=False)
    monkeypatch.delenv("TRADING_REQUIRE_AUTH_FOR_READS", raising=False)
    safety.clear_safety_cache()
    yield
    safety.clear_safety_cache()


def test_mutations_disabled_by_default():
    assert safety.mutations_enabled() is False
    status = safety.trading_safety_status()
    assert status["mutations_enabled"] is False
    assert status["live_trading_allowed"] is False
    assert status["prototype"] is True


def test_read_requires_token_by_default(monkeypatch):
    monkeypatch.setenv("TRADING_API_TOKEN", "expected-token")
    safety.clear_safety_cache()
    with pytest.raises(HTTPException) as exc:
        safety.require_trading_read(authorization=None)
    assert exc.value.status_code == 401


def test_read_accepts_bearer(monkeypatch):
    monkeypatch.setenv("TRADING_API_TOKEN", "expected-token")
    safety.clear_safety_cache()
    assert safety.require_trading_read(authorization="Bearer expected-token") == "expected-token"


def test_mutation_blocked_when_disabled(monkeypatch):
    monkeypatch.setenv("TRADING_API_TOKEN", "expected-token")
    monkeypatch.setenv("TRADING_MUTATIONS_ENABLED", "false")
    safety.clear_safety_cache()
    with pytest.raises(HTTPException) as exc:
        safety.require_trading_mutation(authorization="Bearer expected-token")
    assert exc.value.status_code == 403


def test_mutation_allowed_when_enabled(monkeypatch):
    monkeypatch.setenv("TRADING_API_TOKEN", "expected-token")
    monkeypatch.setenv("TRADING_MUTATIONS_ENABLED", "true")
    safety.clear_safety_cache()
    assert safety.require_trading_mutation(authorization="Bearer expected-token") == "expected-token"


def test_mutation_requires_token_when_enabled(monkeypatch):
    monkeypatch.setenv("TRADING_MUTATIONS_ENABLED", "true")
    safety.clear_safety_cache()
    with pytest.raises(HTTPException) as exc:
        safety.require_trading_mutation(authorization="Bearer expected-token")
    assert exc.value.status_code == 503
