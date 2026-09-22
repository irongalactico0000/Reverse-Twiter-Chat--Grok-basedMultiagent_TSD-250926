using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using TSD.Desktop.Models;

namespace TSD.Desktop.Services;

public class TradingApiClient(HttpClient http)
{
    static readonly JsonSerializerOptions Opts = new()
    {
        PropertyNameCaseInsensitive = true,
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    // ── Broker status ──────────────────────────────────────────────────────
    public Task<List<BrokerStatus>?> GetBrokersAsync() =>
        http.GetFromJsonAsync<List<BrokerStatus>>("api/v1/trading/brokers", Opts);

    public async Task<BrokerStatus?> ConnectBrokerAsync(string id)
    {
        var r = await http.PostAsync($"api/v1/trading/brokers/{id}/connect", null);
        r.EnsureSuccessStatusCode();
        return await r.Content.ReadFromJsonAsync<BrokerStatus>(Opts);
    }

    public async Task<BrokerStatus?> DisconnectBrokerAsync(string id)
    {
        var r = await http.PostAsync($"api/v1/trading/brokers/{id}/disconnect", null);
        r.EnsureSuccessStatusCode();
        return await r.Content.ReadFromJsonAsync<BrokerStatus>(Opts);
    }

    // ── Positions + orders ─────────────────────────────────────────────────
    public Task<List<Position>?> GetPositionsAsync() =>
        http.GetFromJsonAsync<List<Position>>("api/v1/trading/positions", Opts);

    public Task<List<OpenOrder>?> GetOrdersAsync() =>
        http.GetFromJsonAsync<List<OpenOrder>>("api/v1/trading/orders", Opts);

    public async Task PlaceOrderAsync(OrderRequest req)
    {
        var r = await http.PostAsJsonAsync("api/v1/trading/orders", req, Opts);
        r.EnsureSuccessStatusCode();
    }

    public async Task CancelOrderAsync(string orderId, string brokerId)
    {
        var req = new HttpRequestMessage(HttpMethod.Delete, $"api/v1/trading/orders/{orderId}")
        {
            Content = JsonContent.Create(new { broker_id = brokerId }, options: Opts)
        };
        (await http.SendAsync(req)).EnsureSuccessStatusCode();
    }

    // ── Safety ─────────────────────────────────────────────────────────────
    public Task<SafetyStatus?> GetSafetyAsync() =>
        http.GetFromJsonAsync<SafetyStatus>("api/v1/trading/safety", Opts);

    public Task<BridgeCapabilities?> GetCapabilitiesAsync() =>
        http.GetFromJsonAsync<BridgeCapabilities>("api/v1/bridge/capabilities", Opts);

    // ── Bridge (paper target positions) ───────────────────────────────────
    public async Task<TargetProposal?> ProposeTargetAsync(ProposeTargetRequest req)
    {
        var r = await http.PostAsJsonAsync("api/v1/bridge/propose_target", req, Opts);
        r.EnsureSuccessStatusCode();
        return await r.Content.ReadFromJsonAsync<TargetProposal>(Opts);
    }

    public Task<List<TargetProposal>?> GetProposalsAsync() =>
        http.GetFromJsonAsync<List<TargetProposal>>("api/v1/bridge/proposals", Opts);

    public async Task<TargetProposal?> ApproveProposalAsync(string proposalId)
    {
        var r = await http.PostAsJsonAsync("api/v1/bridge/approve",
            new { proposal_id = proposalId, approve = true, note = "" }, Opts);
        r.EnsureSuccessStatusCode();
        return await r.Content.ReadFromJsonAsync<TargetProposal>(Opts);
    }

    public Task<List<BridgePosition>?> GetBridgePositionsAsync() =>
        http.GetFromJsonAsync<List<BridgePosition>>("api/v1/bridge/positions", Opts);

    public Task<List<BridgeEvent>?> GetBridgeEventsAsync() =>
        http.GetFromJsonAsync<List<BridgeEvent>>("api/v1/bridge/events", Opts);

    public async Task PostKillSwitchAsync()
    {
        var r = await http.PostAsync("api/v1/bridge/kill_switch", null);
        r.EnsureSuccessStatusCode();
    }
}
