using System.Collections.ObjectModel;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using TSD.Desktop.Models;
using TSD.Desktop.Services;

namespace TSD.Desktop.ViewModels;

public partial class TargetBridgePanelViewModel : ViewModelBase
{
    readonly TradingApiClient _api;
    readonly DispatcherTimer _timer;

    public ObservableCollection<TargetProposal> Proposals { get; } = [];
    public ObservableCollection<BridgePosition> Positions { get; } = [];
    public ObservableCollection<BridgeEvent> Events { get; } = [];

    [ObservableProperty] string _instrumentId = "BTCUSDT.BINANCE";
    [ObservableProperty] string _targetValue = "0.20";
    [ObservableProperty] string _currentQuantity = "0.18";
    [ObservableProperty] bool _mutationsEnabled;
    [ObservableProperty] bool _liveTradingAllowed;
    [ObservableProperty] string _modeLabel = "paper";
    [ObservableProperty] string _statusMessage = string.Empty;

    public TargetBridgePanelViewModel(TradingApiClient api)
    {
        _api = api;
        _timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(5) };
        _timer.Tick += async (_, _) => await RefreshAsync();
        _timer.Start();
        _ = RefreshAsync();
    }

    async Task RefreshAsync()
    {
        try
        {
            var safety = await _api.GetSafetyAsync();
            MutationsEnabled = safety?.MutationsEnabled ?? false;

            var caps = await _api.GetCapabilitiesAsync();
            LiveTradingAllowed = caps?.LiveTrading ?? false;
            ModeLabel = caps?.Mode ?? "paper";

            var proposals = await _api.GetProposalsAsync() ?? [];
            Proposals.Clear();
            foreach (var p in proposals) Proposals.Add(p);

            var positions = await _api.GetBridgePositionsAsync() ?? [];
            Positions.Clear();
            foreach (var p in positions) Positions.Add(p);

            var events = (await _api.GetBridgeEventsAsync() ?? []).Take(5).ToList();
            Events.Clear();
            foreach (var e in events) Events.Add(e);
        }
        catch { /* backend may be starting */ }
    }

    [RelayCommand]
    async Task Propose()
    {
        if (!MutationsEnabled) { StatusMessage = "Set TRADING_MUTATIONS_ENABLED=true first"; return; }
        try
        {
            await _api.ProposeTargetAsync(new ProposeTargetRequest(
                InstrumentId, "quantity", TargetValue, CurrentQuantity,
                "Desktop paper demo"));
            StatusMessage = $"Proposed {CurrentQuantity} → {TargetValue}";
            await RefreshAsync();
        }
        catch (Exception ex) { StatusMessage = ex.Message; }
    }

    [RelayCommand]
    async Task Approve(string proposalId)
    {
        if (!MutationsEnabled) return;
        try
        {
            await _api.ApproveProposalAsync(proposalId);
            StatusMessage = "Approved";
            await RefreshAsync();
        }
        catch (Exception ex) { StatusMessage = ex.Message; }
    }

    [RelayCommand]
    async Task KillSwitch()
    {
        try { await _api.PostKillSwitchAsync(); StatusMessage = "Kill switch activated"; }
        catch (Exception ex) { StatusMessage = ex.Message; }
    }
}
