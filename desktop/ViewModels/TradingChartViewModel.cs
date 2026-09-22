using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace TSD.Desktop.ViewModels;

public partial class TradingChartViewModel : ViewModelBase
{
    [ObservableProperty] string _symbol = "BTCUSDT";
    [ObservableProperty] string _priceDisplay = "—";
    [ObservableProperty] string _changeDisplay = "—";

    string ApiBase =>
        (Environment.GetEnvironmentVariable("TSD_API_URL") ?? "http://localhost:8000").TrimEnd('/');

    /// <summary>FastAPI static chart page for NativeWebView.</summary>
    public string ChartUrl => $"{ApiBase}/static/chart.html?symbol={Uri.EscapeDataString(Symbol)}";

    partial void OnSymbolChanged(string value) => OnPropertyChanged(nameof(ChartUrl));

    [RelayCommand]
    void SetSymbol(string sym)
    {
        Symbol = sym.ToUpperInvariant();
    }
}
