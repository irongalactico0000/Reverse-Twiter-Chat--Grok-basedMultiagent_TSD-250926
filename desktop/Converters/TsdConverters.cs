using System;
using System.Globalization;
using Avalonia.Data.Converters;
using Avalonia.Media;

namespace TSD.Desktop.Converters;

/// <summary>Broker connection status → status-dot brush.</summary>
public sealed class StatusColorConverter : IValueConverter
{
    public static readonly StatusColorConverter Instance = new();

    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        var s = (value as string)?.ToUpperInvariant() ?? "";
        return s switch
        {
            "CONNECTED" => Brush("#22C55E"),
            "CONNECTING" => Brush("#F59E0B"),
            "DEGRADED" => Brush("#F59E0B"),
            "AUTH_FAILED" or "AUTHENTICATIONFAILED" or "ERROR" => Brush("#EF4444"),
            "DATAONLY" => Brush("#60A5FA"),
            _ => Brush("#6B7280"), // DISCONNECTED / unknown
        };
    }

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        => throw new NotSupportedException();

    static IBrush Brush(string hex) => new SolidColorBrush(Color.Parse(hex));
}

/// <summary>SupportsOrders bool → badge background.</summary>
public sealed class BoolToOrderBgConverter : IValueConverter
{
    public static readonly BoolToOrderBgConverter Instance = new();

    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
        => value is true
            ? new SolidColorBrush(Color.Parse("#14532D"))
            : new SolidColorBrush(Color.Parse("#1F2937"));

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        => throw new NotSupportedException();
}

/// <summary>SupportsOrders bool → badge foreground.</summary>
public sealed class BoolToOrderFgConverter : IValueConverter
{
    public static readonly BoolToOrderFgConverter Instance = new();

    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
        => value is true
            ? new SolidColorBrush(Color.Parse("#86EFAC"))
            : new SolidColorBrush(Color.Parse("#9CA3AF"));

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        => throw new NotSupportedException();
}

/// <summary>SupportsOrders bool → badge label.</summary>
public sealed class BoolToOrderLabelConverter : IValueConverter
{
    public static readonly BoolToOrderLabelConverter Instance = new();

    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
        => value is true ? "Full" : "Data";

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        => throw new NotSupportedException();
}

/// <summary>Strategy IsRunning → card border brush.</summary>
public sealed class RunningBorderConverter : IValueConverter
{
    public static readonly RunningBorderConverter Instance = new();

    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
        => value is true
            ? new SolidColorBrush(Color.Parse("#22C55E"))
            : new SolidColorBrush(Color.Parse("#1F2937"));

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        => throw new NotSupportedException();
}

/// <summary>Strategy status string → chip background.</summary>
public sealed class StatusChipBgConverter : IValueConverter
{
    public static readonly StatusChipBgConverter Instance = new();

    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        var s = (value as string)?.ToUpperInvariant() ?? "";
        return s switch
        {
            "RUNNING" => new SolidColorBrush(Color.Parse("#14532D")),
            "PAUSED" => new SolidColorBrush(Color.Parse("#1E3A5F")),
            "STOPPED" => new SolidColorBrush(Color.Parse("#1F2937")),
            "LIVE" => new SolidColorBrush(Color.Parse("#7F1D1D")),
            _ => new SolidColorBrush(Color.Parse("#1F2937")),
        };
    }

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        => throw new NotSupportedException();
}

/// <summary>Strategy status string → chip foreground.</summary>
public sealed class StatusChipFgConverter : IValueConverter
{
    public static readonly StatusChipFgConverter Instance = new();

    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        var s = (value as string)?.ToUpperInvariant() ?? "";
        return s switch
        {
            "RUNNING" => new SolidColorBrush(Color.Parse("#86EFAC")),
            "PAUSED" => new SolidColorBrush(Color.Parse("#60A5FA")),
            "STOPPED" => new SolidColorBrush(Color.Parse("#9CA3AF")),
            "LIVE" => new SolidColorBrush(Color.Parse("#FCA5A5")),
            _ => new SolidColorBrush(Color.Parse("#9CA3AF")),
        };
    }

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        => throw new NotSupportedException();
}

/// <summary>Signal LONG/SHORT/FLAT → badge background.</summary>
public sealed class SignalBgConverter : IValueConverter
{
    public static readonly SignalBgConverter Instance = new();

    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        var s = (value as string)?.ToUpperInvariant() ?? "";
        return s switch
        {
            "LONG" or "BUY" => new SolidColorBrush(Color.Parse("#14532D")),
            "SHORT" or "SELL" => new SolidColorBrush(Color.Parse("#450A0A")),
            _ => new SolidColorBrush(Color.Parse("#1F2937")),
        };
    }

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        => throw new NotSupportedException();
}

/// <summary>Signal LONG/SHORT/FLAT → badge foreground.</summary>
public sealed class SignalFgConverter : IValueConverter
{
    public static readonly SignalFgConverter Instance = new();

    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        var s = (value as string)?.ToUpperInvariant() ?? "";
        return s switch
        {
            "LONG" or "BUY" => new SolidColorBrush(Color.Parse("#86EFAC")),
            "SHORT" or "SELL" => new SolidColorBrush(Color.Parse("#FCA5A5")),
            _ => new SolidColorBrush(Color.Parse("#9CA3AF")),
        };
    }

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        => throw new NotSupportedException();
}
