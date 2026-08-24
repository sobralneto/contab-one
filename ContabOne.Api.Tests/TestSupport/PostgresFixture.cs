using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Infra;
using Testcontainers.PostgreSql;
using Xunit;

namespace ContabOne.Api.Tests.TestSupport;

/// <summary>
/// Postgres efêmero por execução da suíte (Testcontainers). Mesma tag do
/// docker-compose.yml (`postgres:18-alpine`) — a imagem já está cacheada na
/// máquina de desenvolvimento, e teste e desenvolvimento rodam no mesmo motor.
///
/// Um container por coleção de testes: as classes que precisam de banco
/// compartilham o container e isolam por escritório (criar escritórios
/// distintos é mais barato que recriar schema — design.md, Decisão 3).
/// </summary>
[CollectionDefinition("Banco")]
public class BancoCollection : ICollectionFixture<PostgresFixture>
{
}

public class PostgresFixture : IAsyncLifetime
{
    private PostgreSqlContainer _container = null!;

    public string ConnectionString { get; private set; } = string.Empty;

    public async Task InitializeAsync()
    {
        _container = new PostgreSqlBuilder()
            .WithImage("postgres:18-alpine")
            .WithDatabase("contab_one_teste")
            .WithUsername("contabone")
            .WithPassword("contabone")
            .Build();
        await _container.StartAsync();
        ConnectionString = _container.GetConnectionString();

        // Aplica as migrations no container aqui, na fixture — senão o schema
        // dependeria da ordem em que as classes da coleção rodam (só as que
        // sobem o WebApplicationFactory migrariam, e o AlertaJobTest, que usa
        // DbContext direto, quebraria se rodasse primeiro). O startup do host
        // de teste também roda MigrateAsync (idempotente), o que exercita as
        // migrations por outro caminho — os dois caminhos juntos garantem que
        // o schema existe antes de qualquer teste.
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseNpgsql(ConnectionString)
            .Options;
        using var db = new AppDbContext(options, new TenantContext());
        await db.Database.MigrateAsync();
    }

    public Task DisposeAsync()
        => _container.DisposeAsync().AsTask();

    public void RodarSql(string sql)
    {
        using var conn = new Npgsql.NpgsqlConnection(ConnectionString);
        conn.Open();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        cmd.ExecuteNonQuery();
    }

    public long Contar(string tabela)
    {
        using var conn = new Npgsql.NpgsqlConnection(ConnectionString);
        conn.Open();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $"SELECT count(*) FROM \"{tabela}\"";
        return (long)cmd.ExecuteScalar()!;
    }

    public (int versao, bool ativa) LerRegraV1()
    {
        using var conn = new Npgsql.NpgsqlConnection(ConnectionString);
        conn.Open();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT \"Versao\", \"Ativa\" FROM \"RegraColetas\" ORDER BY \"Versao\" LIMIT 1";
        using var reader = cmd.ExecuteReader();
        reader.Read();
        return (reader.GetInt32(0), reader.GetBoolean(1));
    }
}
