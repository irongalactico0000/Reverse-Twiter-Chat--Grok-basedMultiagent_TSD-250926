import axios from 'axios';

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

/** Trading / bridge requests require TRADING_API_TOKEN on the server. */
function authHeaders(): Record<string, string> {
  const token = import.meta.env.VITE_TRADING_API_TOKEN as string | undefined;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const api = axios.create({
  baseURL: `${BASE}/api/v1/trading`,
  headers: authHeaders(),
});

const bridge = axios.create({
  baseURL: `${BASE}/api/v1/bridge`,
  headers: authHeaders(),
});

export interface BrokerStatus {
  id: string;
  name: string;
  status: 'DISCONNECTED' | 'CONNECTING' | 'CONNECTED' | 'ERROR';
  supports_orders: boolean;
  is_paper: boolean;
  status_detail: string;
  error?: string | null;
}

export interface Position {
  broker: string;
  symbol: string;
  qty: number;
  avg_entry_price?: number | null;
  market_value?: number | null;
  unrealized_pl?: number | null;
  side?: string | null;
}

export interface Order {
  broker: string;
  id: string;
  symbol: string;
  side: string;
  qty: number;
  filled_qty?: number | null;
  order_type?: string | null;
  status?: string | null;
  limit_price?: number | null;
  submitted_at?: string | null;
}

export interface OrderRequest {
  broker_id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  order_type: 'MARKET' | 'LIMIT';
  quantity: number;
  price?: number;
  time_in_force?: string;
}

export interface TargetProposal {
  proposal_id: string;
  status: string;
  plan: {
    instrument_id: string;
    side: string;
    quantity: string;
    current_quantity: string;
    target_quantity: string;
    reason: string;
  };
  risk: { accepted: boolean; reasons: string[] };
  tsd_command_id?: string | null;
  engine_client_order_id?: string | null;
}

export const tradingApi = {
  getBrokers: () => api.get<BrokerStatus[]>('/brokers').then(r => r.data),
  connectBroker: (id: string) => api.post<BrokerStatus>(`/brokers/${id}/connect`).then(r => r.data),
  disconnectBroker: (id: string) => api.post<BrokerStatus>(`/brokers/${id}/disconnect`).then(r => r.data),
  getPositions: () => api.get<Position[]>('/positions').then(r => r.data),
  getOrders: () => api.get<Order[]>('/orders').then(r => r.data),
  placeOrder: (req: OrderRequest) => api.post('/orders', req).then(r => r.data),
  cancelOrder: (orderId: string, brokerId: string) =>
    api.delete(`/orders/${orderId}`, { data: { broker_id: brokerId } }).then(r => r.data),
  getSafety: () => api.get('/safety').then(r => r.data),
};

export interface BridgeCapabilities {
  live_trading: boolean;
  paper_trading: boolean;
  mode: 'paper' | 'live' | string;
  mode_authority: 'server' | string;
  target_types: string[];
  target_types_planned?: string[];
  execution_engines: string[];
  nautilus_paper_env?: string;
  mutations_require_token?: boolean;
  chart?: string;
  accounts?: Array<{
    account_id: string;
    name: string;
    status: string;
    supports_orders: boolean;
    is_paper: boolean;
    live_trading: boolean;
    mode: string;
  }>;
}

export const bridgeApi = {
  getSafety: () => bridge.get('/safety').then(r => r.data),
  getCapabilities: () => bridge.get<BridgeCapabilities>('/capabilities').then(r => r.data),
  proposeTarget: (body: {
    instrument_id: string;
    target_type?: 'quantity' | 'weight' | 'notional';
    target_value: string;
    current_quantity?: string;
    reason?: string;
    idempotency_key?: string;
  }) => bridge.post<TargetProposal>('/propose_target', body).then(r => r.data),
  listProposals: () => bridge.get<TargetProposal[]>('/proposals').then(r => r.data),
  approve: (proposal_id: string, approve = true, note = '') =>
    bridge.post<TargetProposal>('/approve', { proposal_id, approve, note }).then(r => r.data),
  positions: () => bridge.get<{ instrument_id: string; quantity: string }[]>('/positions').then(r => r.data),
  events: () => bridge.get('/events').then(r => r.data),
};

export const WS_URL = `${BASE.replace('http', 'ws')}/api/v1/trading/ws/status`;
