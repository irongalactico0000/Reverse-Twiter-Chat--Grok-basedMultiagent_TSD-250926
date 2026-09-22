using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;
using Avalonia.Controls;
using Microsoft.Extensions.DependencyInjection;
using TSD.Desktop.Services;
using TSD.Desktop.ViewModels;
using TSD.Desktop.Views;

namespace TSD.Desktop;

public partial class App : Application
{
    IServiceProvider? _services;

    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }

    public override void OnFrameworkInitializationCompleted()
    {
        var apiBase = Environment.GetEnvironmentVariable("TSD_API_URL") ?? "http://localhost:8000/";
        if (!apiBase.EndsWith('/')) apiBase += '/';

        var services = new ServiceCollection();
        services.AddHttpClient<TradingApiClient>(c => c.BaseAddress = new Uri(apiBase));
        _services = services.BuildServiceProvider();

        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            var api = _services.GetRequiredService<TradingApiClient>();
            desktop.MainWindow = new MainWindow
            {
                DataContext = new MainWindowViewModel(api),
            };
        }

        base.OnFrameworkInitializationCompleted();
    }
}