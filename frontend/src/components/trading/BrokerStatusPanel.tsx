import styled from 'styled-components';
import { useBrokers, useConnectBroker, useDisconnectBroker } from '../../apis/queries/trading';
import type { BrokerStatus } from '../../apis/axios/trading';

const statusColor = (s: BrokerStatus['status']) => {
  switch (s) {
    case 'CONNECTED': return '#22c55e';
    case 'CONNECTING': return '#f59e0b';
    case 'ERROR': return '#ef4444';
    default: return '#6b7280';
  }
};

const Wrapper = styled.div`
  background: #111827;
  border: 1px solid #1f2937;
  border-radius: 8px;
  padding: 16px;
`;

const Title = styled.h2`
  color: #e5e7eb;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 0 0 12px;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
`;

const Th = styled.th`
  color: #6b7280;
  font-weight: 500;
  text-align: left;
  padding: 6px 10px;
  border-bottom: 1px solid #1f2937;
`;

const Td = styled.td`
  color: #d1d5db;
  padding: 8px 10px;
  border-bottom: 1px solid #111827;
  vertical-align: middle;
`;

const Dot = styled.span<{ color: string }>`
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${p => p.color};
  margin-right: 8px;
  flex-shrink: 0;
`;

const StatusCell = styled.div`
  display: flex;
  align-items: center;
`;

const Badge = styled.span<{ ok?: boolean }>`
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: ${p => p.ok ? '#14532d' : '#1f2937'};
  color: ${p => p.ok ? '#86efac' : '#6b7280'};
`;

const Btn = styled.button<{ variant?: 'connect' | 'disconnect' }>`
  padding: 4px 12px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  background: ${p => p.variant === 'disconnect' ? '#1f2937' : '#1e3a5f'};
  color: ${p => p.variant === 'disconnect' ? '#9ca3af' : '#60a5fa'};
  &:hover { opacity: 0.8; }
  &:disabled { opacity: 0.4; cursor: not-allowed; }
`;

const PaperChip = styled.span`
  margin-left: 6px;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
  background: #1e3a5f;
  color: #60a5fa;
`;

export default function BrokerStatusPanel() {
  const { data: brokers = [], isLoading } = useBrokers();
  const connect = useConnectBroker();
  const disconnect = useDisconnectBroker();

  if (isLoading) return <Wrapper><Title>Brokers</Title><p style={{ color: '#6b7280', fontSize: 13 }}>Loading…</p></Wrapper>;

  return (
    <Wrapper>
      <Title>Broker Connections</Title>
      <Table>
        <thead>
          <tr>
            <Th>Broker</Th>
            <Th>Connected</Th>
            <Th>Orders?</Th>
            <Th></Th>
          </tr>
        </thead>
        <tbody>
          {brokers.map(b => (
            <tr key={b.id}>
              <Td>
                <strong style={{ color: '#f3f4f6' }}>{b.name}</strong>
                {b.is_paper && <PaperChip>PAPER</PaperChip>}
              </Td>
              <Td>
                <StatusCell>
                  <Dot color={statusColor(b.status)} />
                  <span>{b.status_detail || b.status}</span>
                </StatusCell>
              </Td>
              <Td>
                <Badge ok={b.supports_orders && b.status === 'CONNECTED'}>
                  {b.supports_orders ? 'Yes' : 'Data only'}
                </Badge>
              </Td>
              <Td>
                {b.status === 'CONNECTED' ? (
                  <Btn
                    variant="disconnect"
                    disabled={disconnect.isPending}
                    onClick={() => disconnect.mutate(b.id)}
                  >
                    Disconnect
                  </Btn>
                ) : (
                  <Btn
                    variant="connect"
                    disabled={connect.isPending || b.status === 'CONNECTING'}
                    onClick={() => connect.mutate(b.id)}
                  >
                    {b.status === 'CONNECTING' ? 'Connecting…' : 'Connect'}
                  </Btn>
                )}
              </Td>
            </tr>
          ))}
          {brokers.length === 0 && (
            <tr>
              <Td colSpan={4} style={{ textAlign: 'center', color: '#6b7280' }}>
                No brokers configured — add credentials to .env
              </Td>
            </tr>
          )}
        </tbody>
      </Table>
    </Wrapper>
  );
}
