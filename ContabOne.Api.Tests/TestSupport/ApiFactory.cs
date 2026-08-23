using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.Configuration;

namespace ContabOne.Api.Tests.TestSupport;

/// <summary>
/// WebApplicationFactory do host real da API (top-level statements expostos
/// por `public partial class Program`), apontando o banco para o container
/// efêmero do PostgresFixture.
///
/// O startup roda `db.Database.MigrateAsync()` — contra o container, o que é
/// desejável: as migrations (incluindo o seed da RegraColeta v1) são
/// exercitadas a cada execução da suíte.
///
/// ATENÇÃO: o host lê `DATABASE_URL` do ambiente ANTES de
/// `ConnectionStrings:Default` (Program.cs). Rodar a suíte com `DATABASE_URL`
/// setada apontaria as migrations para esse banco — nunca rode os testes com
/// a variável apontando para o banco de desenvolvimento (ver README).
/// </summary>
public class ApiFactory : WebApplicationFactory<Program>
{
    public string ConnectionString { get; }

    public ApiFactory(PostgresFixture banco)
    {
        ConnectionString = banco.ConnectionString;
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseSetting("ConnectionStrings:Default", ConnectionString);
        builder.UseSetting("JWT_SIGNING_KEY", "dev-key-change-in-production-min-32-chars!!");
        builder.UseSetting("HMAC_CNPJ_KEY", "dev-hmac-cnpj-key-change-in-production!!");
        builder.UseSetting("CORS_ORIGINS", "http://localhost:5173");
        builder.ConfigureAppConfiguration((_, config) =>
        {
            // Garante que as chaves de teste valem mesmo se o ambiente do
            // processo tiver valores diferentes.
            config.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["ConnectionStrings:Default"] = ConnectionString,
                ["JWT_SIGNING_KEY"] = "dev-key-change-in-production-min-32-chars!!",
                ["HMAC_CNPJ_KEY"] = "dev-hmac-cnpj-key-change-in-production!!",
            });
        });
    }
}
