import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from .broker_pool import get_pool
from .broker_connection import OrderRequest
from .models import (
    BrokerStatusResponse, OrderRequestBody, OrderResponse,
    CancelOrderBody, PositionItem, OrderItem,
)
from .safety import (
    require_trading_mutation,
    require_trading_read,
    trading_safety_status,
    configured_api_token,
    extract_bearer,
)

router = APIRouter(prefix="/api/v1/trading", tags=["Trading (prototype)"])


@router.get("/safety")
async def get_trading_safety():
    """Public readiness probe — does not expose secrets."""
    return trading_safety_status()


# ── Broker Status ──────────────────────────────────────────────────────────────

@router.get("/brokers", response_model=list[BrokerStatusResponse])
async def list_brokers(_: str = Depends(require_trading_read)):
    """Return live connection status for all configured brokers."""
    pool = get_pool()
    return [
        BrokerStatusResponse(
            id=info.id,
            name=info.name,
            status=info.status,
            supports_orders=info.supports_orders,
            is_paper=info.is_paper,
            status_detail=info.status_detail,
            error=info.error,
        )
        for info in pool.list_brokers()
    ]


@router.post("/brokers/{broker_id}/connect", response_model=BrokerStatusResponse)
async def connect_broker(broker_id: str, _: str = Depends(require_trading_mutation)):
    """Initiate connection to a specific broker."""
    pool = get_pool()
    try:
        info = await pool.connect(broker_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return BrokerStatusResponse(**info.__dict__)


@router.post("/brokers/{broker_id}/disconnect", response_model=BrokerStatusResponse)
async def disconnect_broker(broker_id: str, _: str = Depends(require_trading_mutation)):
    pool = get_pool()
    try:
        info = await pool.disconnect(broker_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return BrokerStatusResponse(**info.__dict__)


# ── Positions ─────────────────────────────────────────────────────────────────

@router.get("/positions", response_model=list[PositionItem])
async def get_positions(_: str = Depends(require_trading_read)):
    """Aggregate positions from all connected brokers."""
    pool = get_pool()
    raw = await pool.get_all_positions()
    return [PositionItem(**p) for p in raw]


# ── Orders ────────────────────────────────────────────────────────────────────

@router.get("/orders", response_model=list[OrderItem])
async def get_orders(_: str = Depends(require_trading_read)):
    """Aggregate open orders from all connected brokers."""
    pool = get_pool()
    raw = await pool.get_all_orders()
    return [OrderItem(**o) for o in raw]


@router.post("/orders", response_model=OrderResponse)
async def place_order(body: OrderRequestBody, _: str = Depends(require_trading_mutation)):
    pool = get_pool()
    broker = pool.get(body.broker_id)
    if not broker:
        raise HTTPException(status_code=404, detail=f"Broker '{body.broker_id}' not found")

    from .broker_connection import ConnectionStatus
    if broker.status != ConnectionStatus.CONNECTED:
        raise HTTPException(status_code=409, detail=f"Broker '{body.broker_id}' is not connected")

    req = OrderRequest(
        symbol=body.symbol,
        side=body.side,
        order_type=body.order_type,
        quantity=body.quantity,
        price=body.price,
        time_in_force=body.time_in_force,
    )
    try:
        result = await broker.send_order(req)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return OrderResponse(broker_id=body.broker_id, result=result)


@router.delete("/orders/{order_id}", response_model=dict)
async def cancel_order(
    order_id: str,
    body: CancelOrderBody,
    _: str = Depends(require_trading_mutation),
):
    pool = get_pool()
    broker = pool.get(body.broker_id)
    if not broker:
        raise HTTPException(status_code=404, detail=f"Broker '{body.broker_id}' not found")
    try:
        result = await broker.cancel_order(order_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return result


# ── WebSocket: real-time broker status feed ───────────────────────────────────

@router.websocket("/ws/status")
async def broker_status_stream(websocket: WebSocket):
    """Streams broker status updates every 3 s. Requires ?token= or Authorization."""
    expected = configured_api_token()
    if not expected:
        await websocket.close(code=1011, reason="TRADING_API_TOKEN not configured")
        return

    auth_header = websocket.headers.get("authorization")
    query_token = websocket.query_params.get("token")
    provided = extract_bearer(auth_header) or (query_token.strip() if query_token else None)
    if provided != expected:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()
    pool = get_pool()
    try:
        while True:
            statuses = [
                {
                    "id": info.id,
                    "name": info.name,
                    "status": info.status,
                    "status_detail": info.status_detail,
                    "supports_orders": info.supports_orders,
                    "is_paper": info.is_paper,
                }
                for info in pool.list_brokers()
            ]
            await websocket.send_text(json.dumps(statuses))
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        pass
