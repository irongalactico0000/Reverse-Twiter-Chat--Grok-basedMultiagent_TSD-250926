namespace TSD.Desktop.Models;

public record BrokerStatus(
    string Id,
    string Name,
    string Status,        // DISCONNECTED | CONNECTING | CONNECTED | ERROR
    bool SupportsOrders,
    bool IsPaper,
    string StatusDetail,
    string? Error = null
);

public record Position(
    string Broker,
    string Symbol,
    double Qty,
    double? AvgEntryPrice,
    double? MarketValue,
    double? UnrealizedPl,
    string? Side
);

public record OpenOrder(
    string Broker,
    string Id,
    string Symbol,
    string Side,
    double Qty,
    double? FilledQty,
    string? OrderType,
    string? Status,
    double? LimitPrice,
    string? SubmittedAt
);

public record SafetyStatus(
    bool Prototype,
    bool MutationsEnabled,
    bool RequireAuthForReads,
    bool ApiTokenConfigured,
    bool LiveTradingAllowed,
    string Message
);

public record TargetProposalPlan(
    string InstrumentId,
    string Side,
    string Quantity,
    string CurrentQuantity,
    string TargetQuantity,
    string Reason
);

public record TargetProposalRisk(bool Accepted, List<string> Reasons);

public record TargetProposal(
    string ProposalId,
    string Status,
    TargetProposalPlan Plan,
    TargetProposalRisk Risk,
    string? TsdCommandId,
    string? EngineClientOrderId
);

public record BridgePosition(string InstrumentId, string Quantity);

public record BridgeEvent(int EventId, string EventType);

public record OrderRequest(
    string BrokerId,
    string Symbol,
    string Side,
    string OrderType,
    double Quantity,
    double? Price = null,
    string TimeInForce = "DAY"
);

public record ProposeTargetRequest(
    string InstrumentId,
    string TargetType,
    string TargetValue,
    string CurrentQuantity,
    string Reason,
    string? IdempotencyKey = null
);
