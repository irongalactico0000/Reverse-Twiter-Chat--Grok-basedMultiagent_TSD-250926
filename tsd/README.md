# TSD-cpp251006

# Trading System Domain (TSD) Integration Guide

This README captures the code-facing work required to connect the existing Trading System Domain (TSD) stack with the multi-agent orchestration service so the combined system can function as an agent-assisted AI trader.

> **2026-09-22 note:** Merge conflict markers were removed from this file. Authoritative trading-OS direction is now in `docs/trading-os-engineering-plan.md` and `docs/NEXT_AGENT_TODO.md`. Prefer target-position intents + an adopted engine (Nautilus spike) over expanding direct OSM order routes.

## 1. Grounding: What Already Works
- **Market plumbing (DSM)**: WebSocket/ZMQ publishers and parsing utilities provide real-time order book streaming primitives (`tsd/dsm`).
- **Order execution shell (OSM)**: Authenticated order managers, latency metrics, and signature helpers exist for Binance, Bybit, Coinbase, and OKX (`tsd/osm`).
- **Type system & config scaffolding**: Shared enums/structs for instruments, orders, and routing plus environment-driven config loaders are in place (`tsd/core`, `tsd/config`).
- **Multi-agent host**: The FastAPI service can orchestrate tool-using Gemini agents and already handles asynchronous message lifecycles (`backend/back-end`).

## 2. Key Gaps to Close
- **Integration surface**: No adapters expose DSM/OSM/TSM functionality as callable tools for the multi-agent backend.
- **Configuration mismatch**: `OrderServiceManager` expects lowercase keys, while `config.EXCHANGE_CONFIG` uses enum keys and omits REST URLs.
- **Strategy layer**: `tsd/tsm` lacks executable strategies, signals, or evaluation loops.
- **Knowledge persistence**: Streaming data is not persisted for later retrieval/analysis by agents; no external intelligence store exists.
- **Agent prompts & tooling**: Current Gemini prompts focus on CAE workflows, not trading-specific reasoning, risk, or execution.

## 3. Code-Level Action Plan
1. **Normalize Order Service configuration**
   - Extend `config.EXCHANGE_CONFIG` with REST/WebSocket endpoints keyed by lowercase exchange names or refactor `OrderServiceManager` to accept `Exchange` enums directly.
   - Audit each order manager constructor (`tsd/osm/managers/*.py`) to ensure consistent parameter order and error handling.

2. **Expose TSD primitives as agent tools**
   - Prefer a **proposal / target-position** facade (not raw `send_order`) for agents.
   - Long-term: bridge to the adopted trading engine; keep broker credentials inside the trading runtime.

3. **Stand up persistence/knowledge store**
   - Choose TimescaleDB/Influx (matching existing docs) and add a recorder in `tsd/dsm/recorder` to persist normalized order books/trades/news.
   - Provide query utilities that agents can call to fetch historical context.

4. **Implement the agentic intelligence crawler**
   - Create an ingestion worker that scrapes APIs/RSS/social feeds, enriches the data, and stores it alongside market data.

5. **Develop the Trading Strategy Manager (TSM)**
   - Executable strategy versions that emit `TargetPositionIntent`; do not treat `tsd/tsm/training` as production runtime.

6. **Refactor agent prompts & orchestration for trading**
   - Trading roles (market analyst, risk manager, execution agent) with approval gates before paper/live.

7. **Testing & validation**
   - Sandbox/paper tests only in CI; never real order submission in CI.

## 4. Future Considerations
- **Local LLM support**, observability, and risk/compliance before any live trading.

Use `docs/NEXT_AGENT_TODO.md` as the executable checklist for the current spike.
