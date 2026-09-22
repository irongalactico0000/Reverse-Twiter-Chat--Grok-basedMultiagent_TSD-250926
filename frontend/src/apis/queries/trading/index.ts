import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { tradingApi, bridgeApi, OrderRequest } from '../../axios/trading';

const KEYS = {
  brokers: ['trading', 'brokers'] as const,
  positions: ['trading', 'positions'] as const,
  orders: ['trading', 'orders'] as const,
  safety: ['trading', 'safety'] as const,
  capabilities: ['bridge', 'capabilities'] as const,
  proposals: ['bridge', 'proposals'] as const,
  bridgePositions: ['bridge', 'positions'] as const,
  bridgeEvents: ['bridge', 'events'] as const,
};

export const useBrokers = () =>
  useQuery({ queryKey: KEYS.brokers, queryFn: tradingApi.getBrokers, refetchInterval: 5000 });

export const usePositions = () =>
  useQuery({ queryKey: KEYS.positions, queryFn: tradingApi.getPositions, refetchInterval: 10000 });

export const useOpenOrders = () =>
  useQuery({ queryKey: KEYS.orders, queryFn: tradingApi.getOrders, refetchInterval: 5000 });

export const useTradingSafety = () =>
  useQuery({ queryKey: KEYS.safety, queryFn: tradingApi.getSafety, refetchInterval: 15000 });

/** Server-authoritative mode/capabilities — UI must not invent LIVE. */
export const useBridgeCapabilities = () =>
  useQuery({
    queryKey: KEYS.capabilities,
    queryFn: bridgeApi.getCapabilities,
    refetchInterval: 15000,
  });

export const useBridgeProposals = () =>
  useQuery({ queryKey: KEYS.proposals, queryFn: bridgeApi.listProposals, refetchInterval: 5000 });

export const useBridgePositions = () =>
  useQuery({
    queryKey: KEYS.bridgePositions,
    queryFn: bridgeApi.positions,
    refetchInterval: 5000,
  });

export const useBridgeEvents = () =>
  useQuery({ queryKey: KEYS.bridgeEvents, queryFn: bridgeApi.events, refetchInterval: 5000 });

export const useProposeTarget = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: bridgeApi.proposeTarget,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.proposals }),
  });
};

export const useApproveProposal = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (proposalId: string) => bridgeApi.approve(proposalId, true),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.proposals });
      qc.invalidateQueries({ queryKey: KEYS.bridgePositions });
      qc.invalidateQueries({ queryKey: KEYS.bridgeEvents });
    },
  });
};

export const useConnectBroker = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: tradingApi.connectBroker,
    onSettled: () => qc.invalidateQueries({ queryKey: KEYS.brokers }),
  });
};

export const useDisconnectBroker = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: tradingApi.disconnectBroker,
    onSettled: () => qc.invalidateQueries({ queryKey: KEYS.brokers }),
  });
};

export const usePlaceOrder = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: OrderRequest) => tradingApi.placeOrder(req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.orders });
      qc.invalidateQueries({ queryKey: KEYS.positions });
    },
  });
};

export const useCancelOrder = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, brokerId }: { orderId: string; brokerId: string }) =>
      tradingApi.cancelOrder(orderId, brokerId),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.orders }),
  });
};
