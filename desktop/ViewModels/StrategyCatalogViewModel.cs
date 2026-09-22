using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace TSD.Desktop.ViewModels;

public partial class StrategyCardViewModel : ObservableObject
{
    [ObservableProperty] string _id = string.Empty;
    [ObservableProperty] string _name = string.Empty;
    [ObservableProperty] string _description = string.Empty;
    [ObservableProperty] string _status = "STOPPED"; // RUNNING | PAUSED | STOPPED
    [ObservableProperty] string _broker = string.Empty;
    [ObservableProperty] string _symbol = string.Empty;
    [ObservableProperty] double? _pnl;
    [ObservableProperty] string _signal = "FLAT"; // LONG | SHORT | FLAT

    public bool IsRunning => Status == "RUNNING";
    public bool CanToggle => Status != "STOPPED";
    public string ToggleLabel => Status == "RUNNING" ? "Pause" : "Resume";

    partial void OnStatusChanged(string value)
    {
        OnPropertyChanged(nameof(IsRunning));
        OnPropertyChanged(nameof(CanToggle));
        OnPropertyChanged(nameof(ToggleLabel));
    }
}

public partial class StrategyCatalogViewModel : ViewModelBase
{
    public ObservableCollection<StrategyCardViewModel> Strategies { get; } =
    [
        new StrategyCardViewModel
        {
            Id = "1", Name = "Momentum Breakout",
            Description = "EMA crossover with volume confirmation",
            Status = "RUNNING", Broker = "alpaca", Symbol = "AAPL",
            Pnl = 142.5, Signal = "LONG",
        },
        new StrategyCardViewModel
        {
            Id = "2", Name = "Mean Reversion",
            Description = "Bollinger Band squeeze entry",
            Status = "PAUSED", Broker = "ib", Symbol = "SPY",
            Pnl = -23.1, Signal = "FLAT",
        },
        new StrategyCardViewModel
        {
            Id = "3", Name = "Crypto Arb",
            Description = "Cross-exchange spread capture",
            Status = "STOPPED", Broker = "alpaca", Symbol = "BTC/USD",
            Pnl = 0, Signal = "FLAT",
        },
    ];

    [RelayCommand]
    void Toggle(StrategyCardViewModel card)
    {
        card.Status = card.Status == "RUNNING" ? "PAUSED" : "RUNNING";
    }

    [RelayCommand]
    void Stop(StrategyCardViewModel card) => card.Status = "STOPPED";
}
