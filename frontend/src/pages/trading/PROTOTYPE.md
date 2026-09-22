# Trading workbench (prototype)

This UI (`/trading`) is a **prototype**. Charts/order books may still use synthetic fixtures.

- Server mode and broker capabilities are authoritative; do not treat a client Paper/Live toggle as permission to trade live.
- Backend mutations are fail-closed (`TRADING_MUTATIONS_ENABLED`, `TRADING_API_TOKEN`).
- Target architecture: `docs/trading-os-engineering-plan.md`
