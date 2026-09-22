"""Prototype trading HTTP surface.

This package is **not** production-ready. Mutations are fail-closed via `safety.py`.
See `docs/trading-os-engineering-plan.md`.
"""

__all__ = ["router"]


def __getattr__(name: str):
    if name == "router":
        from .api import router as _router

        return _router
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
