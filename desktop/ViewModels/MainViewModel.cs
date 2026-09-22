using CommunityToolkit.Mvvm.ComponentModel;

namespace TSD.Desktop.ViewModels;

public partial class MainViewModel : ViewModelBase
{
    [ObservableProperty]
    private string _greeting = "Welcome to Avalonia!";
}
