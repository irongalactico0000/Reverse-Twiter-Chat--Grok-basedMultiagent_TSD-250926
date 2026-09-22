import styled from 'styled-components';
import {
  useApproveProposal,
  useBridgeCapabilities,
  useBridgeEvents,
  useBridgePositions,
  useBridgeProposals,
  useProposeTarget,
  useTradingSafety,
} from '../../apis/queries/trading';

const Wrap = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 8px;
`;

const Title = styled.h3`
  margin: 0;
  font-size: 13px;
  letter-spacing: 0.04em;
  color: #93c5fd;
`;

const Hint = styled.p`
  margin: 0;
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.4;
`;

const Row = styled.div`
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
`;

const Btn = styled.button`
  background: #1d4ed8;
  color: white;
  border: 0;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
  &:disabled { opacity: 0.5; cursor: not-allowed; }
`;

const Ghost = styled(Btn)`
  background: #334155;
`;

const List = styled.ul`
  margin: 0;
  padding-left: 16px;
  font-size: 11px;
  color: #cbd5e1;
`;

export default function TargetBridgePanel() {
  const safety = useTradingSafety();
  const caps = useBridgeCapabilities();
  const proposals = useBridgeProposals();
  const positions = useBridgePositions();
  const events = useBridgeEvents();
  const propose = useProposeTarget();
  const approve = useApproveProposal();

  const mutationsOn = Boolean(safety.data?.mutations_enabled);

  return (
    <Wrap>
      <Title>PAPER TARGET BRIDGE</Title>
      <Hint>
        Strategy expresses target positions. Approve runs risk again, then paper-fills.
        Live trading is disabled. Mutations require TRADING_MUTATIONS_ENABLED + token.
      </Hint>
      <Hint>
        safety: mutations={String(safety.data?.mutations_enabled ?? '…')} · mode=
        {caps.data?.mode ?? '…'} · live={String(caps.data?.live_trading ?? false)} · authority=
        {caps.data?.mode_authority ?? '…'}
      </Hint>
      <Row>
        <Btn
          disabled={!mutationsOn || propose.isPending}
          onClick={() =>
            propose.mutate({
              instrument_id: 'BTCUSDT.BINANCE',
              target_type: 'quantity',
              target_value: '0.20',
              current_quantity: '0.18',
              reason: 'UI paper demo',
            })
          }
        >
          Propose 0.18→0.20 BTC
        </Btn>
      </Row>
      <div>
        <Hint>Proposals</Hint>
        <List>
          {(proposals.data ?? []).slice(0, 5).map((p) => (
            <li key={p.proposal_id}>
              {p.status} {p.plan.side} {p.plan.quantity} → {p.plan.target_quantity}{' '}
              {p.status === 'proposed' && (
                <Ghost
                  disabled={!mutationsOn || approve.isPending}
                  onClick={() => approve.mutate(p.proposal_id)}
                >
                  Approve
                </Ghost>
              )}
            </li>
          ))}
        </List>
      </div>
      <div>
        <Hint>Bridge positions</Hint>
        <List>
          {(positions.data ?? []).map((pos) => (
            <li key={pos.instrument_id}>
              {pos.instrument_id}: {pos.quantity}
            </li>
          ))}
        </List>
      </div>
      <div>
        <Hint>Recent events</Hint>
        <List>
          {(events.data ?? []).slice(0, 5).map((e: { event_id: number; event_type: string }) => (
            <li key={e.event_id}>{e.event_type}</li>
          ))}
        </List>
      </div>
    </Wrap>
  );
}
