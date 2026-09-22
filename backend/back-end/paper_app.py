"""Slim FastAPI app for paper trading verification (no google-adk / CAE deps).

From backend/:
  $env:PYTHONPATH = (Resolve-Path .\\back-end).Path
  .\\.venv\\Scripts\\python.exe -m uvicorn paper_app:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from trading.api import router as trading_router
from trading.safety import trading_safety_status
from trading_bridge.api import router as bridge_router

app = FastAPI(
    title="TSD Paper Trading API",
    description="Verification surface for bridge + fail-closed trading routes.",
    version="0.1.0-paper",
)

_raw_origins = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000",
).strip()
_origins = (
    ["*"]
    if _raw_origins == "*"
    else [o.strip() for o in _raw_origins.split(",") if o.strip()]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trading_router)
app.include_router(bridge_router)

_static = Path(__file__).resolve().parent / "static"
_static.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "TSD paper trading API",
        "safety": trading_safety_status(),
        "docs": "/docs",
    }
