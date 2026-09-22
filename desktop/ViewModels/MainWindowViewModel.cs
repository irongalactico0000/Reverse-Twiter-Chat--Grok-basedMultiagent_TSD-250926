using CommunityToolkit.Mvvm.ComponentModel;
using TSD.Desktop.Services;

namespace TSD.Desktop.ViewModels;

public partial class MainWindowViewModel : ViewModelBase
{
    [ObservableProperty] string _activeTab = "Trading"; // Trading | Workflow

    public BrokerStatusViewModel BrokerStatus { get; }
    public ExecutionConsoleViewModel ExecutionConsole { get; }
    public StrategyCatalogViewModel StrategyCatalog { get; }
    public TradingChartViewModel TradingChart { get; }
    public TargetBridgePanelViewModel TargetBridge { get; }

    public MainWindowViewModel(TradingApiClient api)
    {
        BrokerStatus = new BrokerStatusViewModel(api);
        ExecutionConsole = new ExecutionConsoleViewModel(api);
        StrategyCatalog = new StrategyCatalogViewModel();
        TradingChart = new TradingChartViewModel();
        TargetBridge = new TargetBridgePanelViewModel(api);
    }
}
