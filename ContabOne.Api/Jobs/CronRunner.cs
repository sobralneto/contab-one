using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Infra;
using Serilog;

namespace ContabOne.Api.Jobs;

/// <summary>
/// Standalone entry point for Railway Cron.
/// Usage: dotnet ContabOne.Api.dll --job=alertas
/// Set DATABASE_URL env var before running.
/// </summary>
public static class CronRunner
{
    public static async Task<int> RunAsync(string[] args)
    {
        Log.Information("CronRunner starting: {Job}", args);

        var jobName = args.FirstOrDefault(a => a.StartsWith("--job="))?.Split('=')[1];
        if (string.IsNullOrEmpty(jobName))
        {
            Log.Error("No job specified. Use --job=alertas");
            return 1;
        }

        // Manually build what we need (no DI host for cron)
        var rawConnString = Environment.GetEnvironmentVariable("DATABASE_URL")
                            ?? throw new InvalidOperationException("DATABASE_URL is required");

        var connString = DatabaseUrlConverter.ToConnectionString(rawConnString);

        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseNpgsql(connString)
            .Options;

        await using var db = new AppDbContext(options, new TenantContext());

        if (jobName == "alertas")
        {
            var job = new AlertaJob(db);
            await job.ExecutarAsync();
            Log.Information("AlertaJob completed successfully");
            return 0;
        }

        Log.Error("Unknown job: {JobName}", jobName);
        return 1;
    }
}
