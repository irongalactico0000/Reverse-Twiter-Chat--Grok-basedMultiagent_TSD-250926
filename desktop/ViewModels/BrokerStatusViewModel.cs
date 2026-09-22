using System.Collections.ObjectModel;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using TSD.Desktop.Models;
using TSD.Desktop.Services;

namespace TSD.Desktop.ViewModels;

public partial class BrokerRowViewModel(BrokerStatus b) : ObservableObject
{
    [ObservableProperty] string _id = b.Id;
    [ObservableProperty] string _name = b.Name;
    [ObservableProperty] string _status = b.Status;
    [ObservableProperty] string _statusDetail = b.StatusDetail;
    [ObservableProperty] bool _supportsOrders = b.SupportsOrders;
    [ObservableProperty] bool _isPaper = b.IsPaper;

    public bool IsConnected => Status == "CONNECTED";
    public bool IsConnecting => Status == "CONNECTING";

    public void Update(BrokerStatus s)
    {
        Status = s.Status;
        StatusDetail = s.StatusDetail;
        SupportsOrders = s.SupportsOrders;
        OnPropertyChanged(nameof(IsConnected));
        OnPropertyChanged(nameof(IsConnecting));
    }
}

public partial class BrokerStatusViewModel : ViewModelBase
{
    readonly TradingApiClient _api;
    readonly DispatcherTimer _timer;

    public ObservableCollection<BrokerRowViewModel> Brokers { get; } = [];

    [ObservableProperty] string _errorMessage = string.Empty;

    public BrokerStatusViewModel(TradingApiClient api)
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
            var list = await _api.GetBrokersAsync() ?? [];
            foreach (var b in list)
            {
                var existing = Brokers.FirstOrDefault(r => r.Id == b.Id);
                if (existing is null)
                    Brokers.Add(new BrokerRowViewModel(b));
                else
                    existing.Update(b);
            }
            ErrorMessage = string.Empty;
        }
        catch (Exception ex)
        {
            ErrorMessage = $"Backend unreachable: {ex.Message}";
        }
    }

    [RelayCommand]
    async Task Connect(string id)
    {
        try { await _api.ConnectBrokerAsync(id); await RefreshAsync(); }
        catch (Exception ex) { ErrorMessage = ex.Message; }
    }

    [RelayCommand]
    async Task Disconnect(string id)
    {
        try { await _api.DisconnectBrokerAsync(id); await RefreshAsync(); }
        catch (Exception ex) { ErrorMessage = ex.Message; }
    }
}
