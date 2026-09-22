import { useState } from 'react';
import styled from 'styled-components';
import {
  useOpenOrders,
  usePositions,
  usePlaceOrder,
  useCancelOrder,
  useBrokers,
  useBridgeCapabilities,
  useTradingSafety,
} from '../../apis/queries/trading';

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
`;

const Panel = styled.div`
  background: #111827;
  border: 1px solid #1f2937;
  border-radius: 8px;
  padding: 16px;
`;

const Title = styled.h3`
  color: #e5e7eb;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ModeToggle = styled.div`
  display: flex;
  gap: 4px;
  margin-left: auto;
`;

const ModeChip = styled.span<{ active?: boolean; danger?: boolean; muted?: boolean }>`
  padding: 3px 10px;
  border-radius: 4px;
  border: 1px solid ${p => (p.danger ? '#7f1d1d' : '#374151')};
  background: ${p => (p.active ? (p.danger ? '#7f1d1d' : '#1e3a5f') : 'transparent')};
  color: ${p => (p.danger ? '#6b7280' : p.muted ? '#6b7280' : '#9ca3af')};
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  opacity: ${p => (p.muted ? 0.55 : 1)};
  cursor: default;
`;

const CapHint = styled.p`
  margin: 0 0 10px;
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.4;
`;

const Grid2 = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
`;

const Field = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
`;

const Label = styled.label`
  font-size: 11px;
  color: #6b7280;
  font-weight: 500;
`;

const Input = styled.input`
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 4px;
  color: #f3f4f6;
  padding: 6px 8px;
  font-size: 13px;
  width: 100%;
  box-sizing: border-box;
  &:focus { outline: none; border-color: #60a5fa; }
`;

const Select = styled.select`
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 4px;
  color: #f3f4f6;
  padding: 6px 8px;
  font-size: 13px;
  width: 100%;
`;

const SideRow = styled.div`
  display: flex;
  gap: 8px;
`;

const SideBtn = styled.button<{ side: 'BUY' | 'SELL'; active?: boolean }>`
  flex: 1;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid ${p => (p.side === 'BUY' ? '#166534' : '#7f1d1d')};
  background: ${p => (p.active ? (p.side === 'BUY' ? '#14532d' : '#450a0a') : 'transparent')};
  color: ${p => (p.side === 'BUY' ? '#86efac' : '#fca5a5')};
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  &:hover { opacity: 0.9; }
`;

const SubmitBtn = styled.button`
  width: 100%;
  margin-top: 8px;
  padding: 10px;
  border-radius: 4px;
  border: none;
  background: #1e3a5f;
  color: #60a5fa;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  &:hover { background: #1e40af; }
  &:disabled { opacity: 0.4; cursor: not-allowed; }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
`;
const Th = styled.th`
  color: #6b7280;
  text-align: left;
  padding: 4px 8px;
  border-bottom: 1px solid #1f2937;
  font-weight: 500;
`;
const Td = styled.td`
  color: #d1d5db;
  padding: 6px 8px;
  border-bottom: 1px solid #0f172a;
`;

const PlBadge = styled.span<{ positive?: boolean }>`
  color: ${p => (p.positive ? '#86efac' : '#fca5a5')};
  font-weight: 600;
`;

const AccountList = styled.ul`
  margin: 0 0 10px;
  padding-left: 16px;
  font-size: 11px;
  color: #cbd5e1;
`;

export default function ExecutionConsole() {
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [symbol, setSymbol] = useState('');
  const [qty, setQty] = useState('');
  const [price, setPrice] = useState('');
  const [orderType, setOrderType] = useState('MARKET');
  const [brokerId, setBrokerId] = useState('alpaca');

  const { data: orders = [] } = useOpenOrders();
  const { data: positions = [] } = usePositions();
  const { data: brokers = [] } = useBrokers();
  const caps = useBridgeCapabilities();
  const safety = useTradingSafety();
  const placeOrder = usePlaceOrder();
  const cancelOrder = useCancelOrder();

  const liveAllowed = Boolean(caps.data?.live_trading);
  const mode = (caps.data?.mode ?? 'paper').toUpperCase();
  const mutationsOn = Boolean(safety.data?.mutations_enabled);
  const connectedBrokers = brokers.filter(b => b.status === 'CONNECTED' && b.supports_orders);

  const handleSubmit = async () => {
    if (!symbol || !qty || !mutationsOn) return;
    await placeOrder.mutateAsync({
      broker_id: brokerId,
      symbol: symbol.toUpperCase(),
      side,
      order_type: orderType as 'MARKET' | 'LIMIT',
      quantity: parseFloat(qty),
      price: orderType === 'LIMIT' ? parseFloat(price) : undefined,
    });
    setSymbol('');
    setQty('');
    setPrice('');
  };

  return (
    <Wrapper>
      <Panel>
        <Title>
          Order Entry
          <ModeToggle>
            <ModeChip active={!liveAllowed} muted={false}>
              {mode || 'PAPER'}
            </ModeChip>
            <ModeChip danger muted={!liveAllowed} title="Server-authoritative — client cannot enable LIVE">
              LIVE {liveAllowed ? 'ON' : 'LOCKED'}
            </ModeChip>
          </ModeToggle>
        </Title>

        <CapHint>
          Mode authority: {caps.data?.mode_authority ?? '…'} · live=
          {String(caps.data?.live_trading ?? false)} · target_types=
          {(caps.data?.target_types ?? []).join(',') || '…'}
        </CapHint>

        {(caps.data?.accounts?.length ?? 0) > 0 && (
          <AccountList>
            {caps.data!.accounts!.map(a => (
              <li key={a.account_id}>
                {a.name}: {a.supports_orders ? 'orders' : 'data'} ·{' '}
                {a.is_paper ? 'paper' : 'live-flag'} · {a.status}
              </li>
            ))}
          </AccountList>
        )}

        <Field style={{ marginBottom: 8 }}>
          <Label>Broker</Label>
          <Select value={brokerId} onChange={e => setBrokerId(e.target.value)}>
            {connectedBrokers.map(b => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
            {connectedBrokers.length === 0 && <option value="">No brokers connected</option>}
          </Select>
        </Field>

        <SideRow>
          <SideBtn side="BUY" active={side === 'BUY'} onClick={() => setSide('BUY')}>BUY</SideBtn>
          <SideBtn side="SELL" active={side === 'SELL'} onClick={() => setSide('SELL')}>SELL</SideBtn>
        </SideRow>

        <Grid2 style={{ marginTop: 10 }}>
          <Field>
            <Label>Symbol</Label>
            <Input value={symbol} onChange={e => setSymbol(e.target.value)} placeholder="AAPL" />
          </Field>
          <Field>
            <Label>Order Type</Label>
            <Select value={orderType} onChange={e => setOrderType(e.target.value)}>
              <option value="MARKET">Market</option>
              <option value="LIMIT">Limit</option>
            </Select>
          </Field>
          <Field>
            <Label>Quantity</Label>
            <Input type="number" value={qty} onChange={e => setQty(e.target.value)} placeholder="1" />
          </Field>
          {orderType === 'LIMIT' && (
            <Field>
              <Label>Limit Price</Label>
              <Input type="number" value={price} onChange={e => setPrice(e.target.value)} placeholder="0.00" />
            </Field>
          )}
        </Grid2>

        <SubmitBtn
          disabled={
            placeOrder.isPending ||
            connectedBrokers.length === 0 ||
            !mutationsOn
          }
          onClick={handleSubmit}
        >
          {placeOrder.isPending ? 'Sending…' : `${side} ${symbol || '—'}`}
        </SubmitBtn>
      </Panel>

      <Panel>
        <Title>Positions</Title>
        <Table>
          <thead>
            <tr><Th>Symbol</Th><Th>Qty</Th><Th>Avg</Th><Th>P&L</Th></tr>
          </thead>
          <tbody>
            {positions.map((p, i) => (
              <tr key={i}>
                <Td><strong>{p.symbol}</strong></Td>
                <Td>{p.qty}</Td>
                <Td>{p.avg_entry_price != null ? `$${p.avg_entry_price.toFixed(2)}` : '—'}</Td>
                <Td>
                  {p.unrealized_pl != null ? (
                    <PlBadge positive={p.unrealized_pl >= 0}>
                      {p.unrealized_pl >= 0 ? '+' : ''}{p.unrealized_pl.toFixed(2)}
                    </PlBadge>
                  ) : '—'}
                </Td>
              </tr>
            ))}
            {positions.length === 0 && (
              <tr><Td colSpan={4} style={{ textAlign: 'center', color: '#4b5563' }}>No open positions</Td></tr>
            )}
          </tbody>
        </Table>
      </Panel>

      <Panel>
        <Title>Open Orders</Title>
        <Table>
          <thead>
            <tr><Th>Symbol</Th><Th>Side</Th><Th>Qty</Th><Th>Status</Th><Th></Th></tr>
          </thead>
          <tbody>
            {orders.map(o => (
              <tr key={o.id}>
                <Td><strong>{o.symbol}</strong></Td>
                <Td style={{ color: o.side === 'BUY' ? '#86efac' : '#fca5a5' }}>{o.side}</Td>
                <Td>{o.qty}</Td>
                <Td>{o.status}</Td>
                <Td>
                  <button
                    style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: 12 }}
                    onClick={() => cancelOrder.mutate({ orderId: o.id, brokerId: o.broker })}
                  >
                    Cancel
                  </button>
                </Td>
              </tr>
            ))}
            {orders.length === 0 && (
              <tr><Td colSpan={5} style={{ textAlign: 'center', color: '#4b5563' }}>No open orders</Td></tr>
            )}
          </tbody>
        </Table>
      </Panel>
    </Wrapper>
  );
}
