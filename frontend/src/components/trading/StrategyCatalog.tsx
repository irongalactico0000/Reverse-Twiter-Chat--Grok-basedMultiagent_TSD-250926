import { useState } from 'react';
import styled from 'styled-components';

interface Strategy {
  id: string;
  name: string;
  description: string;
  status: 'RUNNING' | 'PAUSED' | 'STOPPED';
  broker: string;
  symbol: string;
  pnl?: number;
  signal?: 'LONG' | 'SHORT' | 'FLAT';
}

// Placeholder strategies — will be driven by the multi-agent backend in a future phase
const DEMO_STRATEGIES: Strategy[] = [
  { id: '1', name: 'Momentum Breakout', description: 'EMA crossover with volume confirmation', status: 'RUNNING', broker: 'alpaca', symbol: 'AAPL', pnl: 142.5, signal: 'LONG' },
  { id: '2', name: 'Mean Reversion', description: 'Bollinger Band squeeze entry', status: 'PAUSED', broker: 'ib', symbol: 'SPY', pnl: -23.1, signal: 'FLAT' },
  { id: '3', name: 'Crypto Arb', description: 'Cross-exchange spread capture', status: 'STOPPED', broker: 'alpaca', symbol: 'BTC/USD', pnl: 0, signal: 'FLAT' },
];

const Wrapper = styled.div`
  background: #111827;
  border: 1px solid #1f2937;
  border-radius: 8px;
  padding: 16px;
  height: 100%;
`;

const Title = styled.h3`
  color: #e5e7eb;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 0 0 14px;
`;

const Cards = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const Card = styled.div<{ status: Strategy['status'] }>`
  background: #0f172a;
  border: 1px solid ${p => p.status === 'RUNNING' ? '#1e3a5f' : '#1f2937'};
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  &:hover { border-color: #374151; }
`;

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
`;

const CardName = styled.span`
  color: #f3f4f6;
  font-weight: 600;
  font-size: 13px;
`;

const StatusChip = styled.span<{ status: Strategy['status'] }>`
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 3px;
  letter-spacing: 0.05em;
  background: ${p => ({ RUNNING: '#14532d', PAUSED: '#1e3a5f', STOPPED: '#1f2937' }[p.status])};
  color: ${p => ({ RUNNING: '#86efac', PAUSED: '#60a5fa', STOPPED: '#6b7280' }[p.status])};
`;

const CardMeta = styled.div`
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 8px;
`;

const CardFooter = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Signal = styled.span<{ s?: Strategy['signal'] }>`
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 3px;
  background: ${p => p.s === 'LONG' ? '#14532d' : p.s === 'SHORT' ? '#450a0a' : '#1f2937'};
  color: ${p => p.s === 'LONG' ? '#86efac' : p.s === 'SHORT' ? '#fca5a5' : '#6b7280'};
`;

const Pnl = styled.span<{ positive?: boolean }>`
  font-size: 12px;
  font-weight: 600;
  color: ${p => p.positive ? '#86efac' : '#fca5a5'};
`;

const ActionRow = styled.div`
  display: flex;
  gap: 6px;
  margin-top: 10px;
`;

const Btn = styled.button`
  flex: 1;
  padding: 5px 8px;
  border-radius: 4px;
  border: 1px solid #374151;
  background: transparent;
  color: #9ca3af;
  font-size: 11px;
  cursor: pointer;
  &:hover { background: #1f2937; color: #e5e7eb; }
`;

export default function StrategyCatalog() {
  const [strategies, setStrategies] = useState(DEMO_STRATEGIES);

  const toggle = (id: string) =>
    setStrategies(prev => prev.map(s =>
      s.id === id ? { ...s, status: s.status === 'RUNNING' ? 'PAUSED' : 'RUNNING' } : s
    ));

  const stop = (id: string) =>
    setStrategies(prev => prev.map(s => s.id === id ? { ...s, status: 'STOPPED' } : s));

  return (
    <Wrapper>
      <Title>Strategy Catalog</Title>
      <Cards>
        {strategies.map(s => (
          <Card key={s.id} status={s.status}>
            <CardHeader>
              <CardName>{s.name}</CardName>
              <StatusChip status={s.status}>{s.status}</StatusChip>
            </CardHeader>
            <CardMeta>{s.description} · {s.symbol} · {s.broker}</CardMeta>
            <CardFooter>
              <Signal s={s.signal}>{s.signal ?? 'FLAT'}</Signal>
              {s.pnl !== undefined && (
                <Pnl positive={s.pnl >= 0}>{s.pnl >= 0 ? '+' : ''}{s.pnl.toFixed(2)}</Pnl>
              )}
            </CardFooter>
            <ActionRow>
              <Btn onClick={() => toggle(s.id)} disabled={s.status === 'STOPPED'}>
                {s.status === 'RUNNING' ? 'Pause' : 'Resume'}
              </Btn>
              <Btn onClick={() => stop(s.id)} style={{ color: '#f87171' }}>Stop</Btn>
            </ActionRow>
          </Card>
        ))}
      </Cards>
    </Wrapper>
  );
}
