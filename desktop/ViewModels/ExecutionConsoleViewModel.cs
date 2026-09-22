using System.Collections.ObjectModel;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using TSD.Desktop.Models;
using TSD.Desktop.Services;

namespace TSD.Desktop.ViewModels;

public partial class ExecutionConsoleViewModel : ViewModelBase
{
    readonly TradingApiClient _api;
    readonly DispatcherTimer _timer;

    public ObservableCollection<Position> Positions { get; } = [];
    public ObservableCollection<OpenOrder> Orders { get; } = [];
    public ObservableCollection<BridgeAccountCapability> Accounts { get; } = [];

    // Order entry
    [ObservableProperty] string _symbol = string.Empty;
    [ObservableProperty] string _quantity = string.Empty;
    [ObservableProperty] string _limitPrice = string.Empty;
    [ObservableProperty] string _selectedSide = "BUY";
    [ObservableProperty] string _selectedOrderType = "MARKET";
    [ObservableProperty] string _selectedBrokerId = "alpaca";
    [ObservableProperty] string _modeLabel = "PAPER";
    [ObservableProperty] bool _liveTradingAllowed;
    [ObservableProperty] string _modeAuthority = "server";
    [ObservableProperty] string _statusMessage = string.Empty;

    public bool IsLimitOrder => SelectedOrderType == "LIMIT";
    public bool IsPaperMode => !LiveTradingAllowed;

    partial void OnSelectedOrderTypeChanged(string value) => OnPropertyChanged(nameof(IsLimitOrder));
    partial void OnLiveTradingAllowedChanged(bool value) => OnPropertyChanged(nameof(IsPaperMode));

    public ExecutionConsoleViewModel(TradingApiClient api)
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
            var caps = await _api.GetCapabilitiesAsync();
            if (caps != null)
            {
                LiveTradingAllowed = caps.LiveTrading;
                ModeLabel = string.IsNullOrWhiteSpace(caps.Mode)
                    ? (caps.LiveTrading ? "LIVE" : "PAPER")
                    : caps.Mode.ToUpperInvariant();
                ModeAuthority = caps.ModeAuthority ?? "server";
                Accounts.Clear();
                foreach (var a in caps.Accounts ?? [])
                    Accounts.Add(a);
            }

            var positions = await _api.GetPositionsAsync() ?? [];
            Positions.Clear();
            foreach (var p in positions) Positions.Add(p);

            var orders = await _api.GetOrdersAsync() ?? [];
            Orders.Clear();
            foreach (var o in orders) Orders.Add(o);
        }
        catch { /* backend may not be running yet */ }
    }

    [RelayCommand]
    async Task PlaceOrder()
    {
        if (string.IsNullOrWhiteSpace(Symbol) || !double.TryParse(Quantity, out var qty)) return;

        double? price = null;
        if (IsLimitOrder && double.TryParse(LimitPrice, out var lp)) price = lp;

        try
        {
            await _api.PlaceOrderAsync(new OrderRequest(
                SelectedBrokerId, Symbol.ToUpper(), SelectedSide,
                SelectedOrderType, qty, price));
            StatusMessage = $"Order sent: {SelectedSide} {qty} {Symbol.ToUpper()}";
            Symbol = Quantity = LimitPrice = string.Empty;
            await RefreshAsync();
        }
        catch (Exception ex) { StatusMessage = $"Error: {ex.Message}"; }
    }

    [RelayCommand]
    async Task CancelOrder(OpenOrder order)
    {
        try
        {
            await _api.CancelOrderAsync(order.Id, order.Broker);
            await RefreshAsync();
        }
        catch (Exception ex) { StatusMessage = $"Cancel failed: {ex.Message}"; }
    }

    [RelayCommand]
    void ToggleSide(string side) => SelectedSide = side;
}
