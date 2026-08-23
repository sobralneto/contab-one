using System.Text.RegularExpressions;

namespace ContabOne.Api.Infra;

/// <summary>
/// Railway delivers postgresql://user:pass@host:port/db.
/// Npgsql expects Host=...;Port=...;Username=...;Password=...;Database=...
/// This converts between them. (§11 item 2)
/// </summary>
public static partial class DatabaseUrlConverter
{
    // postgresql://user:password@host:port/database
    private static readonly Regex UrlRegex = UrlPattern();

    [GeneratedRegex(@"^postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):?(\d*)/([^?]+)")]
    private static partial Regex UrlPattern();

    public static string ToConnectionString(string databaseUrl)
    {
        var match = UrlRegex.Match(databaseUrl);
        if (!match.Success)
            return databaseUrl; // assume it's already a connection string

        var user = Uri.UnescapeDataString(match.Groups[1].Value);
        var pass = Uri.UnescapeDataString(match.Groups[2].Value);
        var host = match.Groups[3].Value;
        var port = match.Groups[4].Value;
        var db = match.Groups[5].Value;

        var connString = $"Host={host};Username={user};Password={pass};Database={db}";
        if (!string.IsNullOrEmpty(port))
            connString += $";Port={port}";

        return connString;
    }
}
