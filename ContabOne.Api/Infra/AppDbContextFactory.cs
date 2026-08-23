using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace ContabOne.Api.Infra;

/// <summary>
/// Design-time factory so `dotnet ef migrations` works without a running app.
/// Uses a connection string from DATABASE_URL env var or appsettings.
/// </summary>
public class AppDbContextFactory : IDesignTimeDbContextFactory<AppDbContext>
{
    public AppDbContext CreateDbContext(string[] args)
    {
        var optionsBuilder = new DbContextOptionsBuilder<AppDbContext>();

        // Try DATABASE_URL first (Railway), then appsettings for local dev
        var rawConnString = Environment.GetEnvironmentVariable("DATABASE_URL");
        if (string.IsNullOrEmpty(rawConnString))
        {
            rawConnString = "Host=localhost;Port=5432;Username=contabone;Password=contabone;Database=contab_one";
        }

        var connString = DatabaseUrlConverter.ToConnectionString(rawConnString);

        optionsBuilder.UseNpgsql(connString);

        // For design-time, use a dummy tenant context (no filters apply)
        return new AppDbContext(optionsBuilder.Options, new TenantContext());
    }
}
