"""Fail-closed trading safety gates.

Trading mutations (connect, disconnect, place, cancel) are disabled unless:
1. TRADING_MUTATIONS_ENABLED is explicitly true, and
2. The request carries Authorization: Bearer <TRADING_API_TOKEN>.

Read-only endpoints require the bearer token when TRADING_REQUIRE_AUTH_FOR_READS
is true (default).

Live trading is never enabled by these flags alone.
"""
from __future__ import annotations

import os
from functools import lru_cache

from fastapi import Header, HTTPException, status


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def mutations_enabled() -> bool:
    return _truthy(os.getenv("TRADING_MUTATIONS_ENABLED", "false"))


@lru_cache(maxsize=1)
def require_auth_for_reads() -> bool:
    return _truthy(os.getenv("TRADING_REQUIRE_AUTH_FOR_READS", "true"))


@lru_cache(maxsize=1)
def configured_api_token() -> str | None:
    token = (os.getenv("TRADING_API_TOKEN") or "").strip()
    return token or None


def trading_safety_status() -> dict:
    return {
        "prototype": True,
        "mutations_enabled": mutations_enabled(),
        "require_auth_for_reads": require_auth_for_reads(),
        "api_token_configured": configured_api_token() is not None,
        "live_trading_allowed": False,
        "message": (
            "Trading package is a prototype. Mutations are fail-closed by default. "
            "Live trading is disabled until engineering-plan gates pass."
        ),
    }


def extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


def _assert_bearer(authorization: str | None) -> str:
    expected = configured_api_token()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Trading API token is not configured. Set TRADING_API_TOKEN "
                "before enabling trading routes."
            ),
        )
    provided = extract_bearer(authorization)
    if not provided or provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing trading bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return provided


def require_trading_read(authorization: str | None = Header(default=None)) -> str | None:
    if not require_auth_for_reads():
        return None
    return _assert_bearer(authorization)


def require_trading_mutation(authorization: str | None = Header(default=None)) -> str:
    if not mutations_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Trading mutations are disabled. Set TRADING_MUTATIONS_ENABLED=true "
                "only in a controlled paper environment after reviewing "
                "docs/NEXT_AGENT_TODO.md."
            ),
        )
    return _assert_bearer(authorization)


def clear_safety_cache() -> None:
    """Test helper: reset cached env decisions."""
    mutations_enabled.cache_clear()
    require_auth_for_reads.cache_clear()
    configured_api_token.cache_clear()
