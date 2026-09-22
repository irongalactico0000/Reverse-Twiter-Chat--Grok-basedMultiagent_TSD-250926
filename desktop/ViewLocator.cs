using System;
using System.Diagnostics.CodeAnalysis;
using Avalonia.Controls;
using Avalonia.Controls.Templates;
using TSD.Desktop.ViewModels;

namespace TSD.Desktop;

/// <summary>
/// Maps <c>TSD.Desktop.ViewModels.FooViewModel</c> → <c>TSD.Desktop.Views.FooView</c>.
/// </summary>
[RequiresUnreferencedCode(
    "Default implementation of ViewLocator involves reflection which may be trimmed away.",
    Url = "https://docs.avaloniaui.net/docs/concepts/view-locator")]
public class ViewLocator : IDataTemplate
{
    public Control? Build(object? param)
    {
        if (param is null)
            return null;

        var vmName = param.GetType().FullName;
        if (string.IsNullOrEmpty(vmName))
            return null;

        // ViewModels.FooViewModel → Views.FooView
        var viewName = vmName
            .Replace(".ViewModels.", ".Views.", StringComparison.Ordinal)
            .Replace("ViewModel", "View", StringComparison.Ordinal);

        var type = Type.GetType(viewName)
                   ?? param.GetType().Assembly.GetType(viewName);

        if (type != null)
            return (Control)Activator.CreateInstance(type)!;

        return new TextBlock { Text = "Not Found: " + viewName };
    }

    public bool Match(object? data) => data is ViewModelBase;
}
