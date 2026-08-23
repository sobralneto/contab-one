using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Jobs;
using ContabOne.Api.Tests.TestSupport;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// O job diário de alertas (AlertaJob) contra o Postgres efêmero. O job roda
/// fora do WebApplicationFactory (CronRunner monta o próprio host a partir de
/// DATABASE_URL), então é instanciado diretamente com um AppDbContext
/// apontado para o container — o caminho de linha de comando em si não é
/// exercitado (ver design.md, Risco "Testcontainers ainda não cobre o job").
/// </summary>
[Trait("Category", "Banco")]
[Collection("Banco")]
public class AlertaJobTest
{
    private readonly PostgresFixture _banco;
    private readonly string _sufixo;

    public AlertaJobTest(PostgresFixture banco)
    {
        _banco = banco;
        _sufixo = Guid.NewGuid().ToString("N")[..8];
    }

    private AppDbContext NovoDbContext()
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseNpgsql(_banco.ConnectionString)
            .Options;
        return new AppDbContext(options, new TenantContext());
    }

    private static async Task RodarJob(AppDbContext db)
        => await new AlertaJob(db).ExecutarAsync();

    // ── 8.1: certificado vencido, a vencer em 30 dias, e válido ──

    [Fact]
    public async Task CertificadosVencidosEAVencer_AbreAlertas_VencidosNao()
    {
        using var db = NovoDbContext();
        var hoje = DateOnly.FromDateTime(DateTime.UtcNow);
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Certs {_sufixo}");

        var vencido = DataHelpers.CriarCliente(db, esc.Id, "0001", "Cert Vencido");
        vencido.CertificadoValidade = hoje.AddDays(-10);
        var aVencer = DataHelpers.CriarCliente(db, esc.Id, "0002", "Cert a Vencer");
        aVencer.CertificadoValidade = hoje.AddDays(20);
        var valido = DataHelpers.CriarCliente(db, esc.Id, "0003", "Cert Válido");
        valido.CertificadoValidade = hoje.AddDays(400);
        db.SaveChanges();

        await RodarJob(db);

        using var db2 = NovoDbContext();
        var alertas = db2.Alertas.IgnoreQueryFilters()
            .Where(a => a.EscritorioId == esc.Id).ToList();
        Assert.Contains(alertas, a => a.Tipo == TipoAlerta.CertificadoVencido);
        Assert.Contains(alertas, a => a.Tipo == TipoAlerta.CertificadoVencendo);
        Assert.DoesNotContain(alertas, a => a.ClienteId == valido.Id);
    }

    // ── 8.2: agente silencioso ──

    [Fact]
    public async Task EscritorioComAgenteAtivoSemExecucao_AbreAlertaDeAgenteSilencioso()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Silencioso {_sufixo}");
        DataHelpers.CriarAgente(db, esc.Id, $"Agente Silencioso {_sufixo}");

        await RodarJob(db);

        using var db2 = NovoDbContext();
        var alerta = db2.Alertas.IgnoreQueryFilters()
            .FirstOrDefault(a => a.EscritorioId == esc.Id && a.Tipo == TipoAlerta.AgenteSilencioso);
        Assert.NotNull(alerta);
        Assert.Null(alerta.ClienteId);
    }

    [Fact]
    public async Task EscritorioComExecucaoRecente_NaoAbreAlertaDeAgenteSilencioso()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Ativo {_sufixo}");
        DataHelpers.CriarAgente(db, esc.Id, $"Agente Ativo {_sufixo}");
        db.Execucoes.Add(new Execucao
        {
            EscritorioId = esc.Id,
            AgenteId = db.Agentes.IgnoreQueryFilters().First(a => a.EscritorioId == esc.Id).Id,
            IniciadoEm = DateTime.UtcNow,
        });
        db.SaveChanges();

        await RodarJob(db);

        using var db2 = NovoDbContext();
        Assert.Empty(db2.Alertas.IgnoreQueryFilters()
            .Where(a => a.EscritorioId == esc.Id && a.Tipo == TipoAlerta.AgenteSilencioso));
    }

    // ── 8.3: rodar duas vezes não duplica ──

    [Fact]
    public async Task RodarDuasVezes_NaoDuplicaAlertas()
    {
        using var db = NovoDbContext();
        var hoje = DateOnly.FromDateTime(DateTime.UtcNow);
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Duplicado {_sufixo}");
        var vencido = DataHelpers.CriarCliente(db, esc.Id, "0001", "Vencido 2x");
        vencido.CertificadoValidade = hoje.AddDays(-5);
        db.SaveChanges();

        await RodarJob(db);
        await RodarJob(db);

        using var db2 = NovoDbContext();
        var total = db2.Alertas.IgnoreQueryFilters()
            .Count(a => a.EscritorioId == esc.Id && a.Tipo == TipoAlerta.CertificadoVencido);
        Assert.Equal(1, total);
    }

    // ── 8.4: percorre todos os escritórios ativos sem abortar ──

    [Fact]
    public async Task PercorreTodosOsEscritoriosAtivos_SemAbortar()
    {
        using var db = NovoDbContext();
        var hoje = DateOnly.FromDateTime(DateTime.UtcNow);

        for (var i = 0; i < 5; i++)
        {
            var esc = DataHelpers.CriarEscritorio(db, $"Escritório Varredura {_sufixo}-{i}");
            DataHelpers.CriarAgente(db, esc.Id, $"Agente Varredura {_sufixo}-{i}");
            if (i % 2 == 0)
            {
                var c = DataHelpers.CriarCliente(db, esc.Id, $"00{i}", $"Cliente {i}");
                c.CertificadoValidade = hoje.AddDays(-i); // metade com cert vencido
            }
            db.SaveChanges();
        }
        // Escritório inativo não deve ser varrido nem quebrar nada
        var inativo = DataHelpers.CriarEscritorio(db, $"Escritório Inativo {_sufixo}");
        inativo.Status = StatusEscritorio.Suspenso;
        db.SaveChanges();

        // Não lança — era exatamente o caminho que abortava com a
        // InvalidOperationException de a.Aberto antes da correção.
        await RodarJob(db);

        using var db2 = NovoDbContext();
        var alertas = db2.Alertas.IgnoreQueryFilters()
            .Where(a => a.EscritorioId != inativo.Id).ToList();
        Assert.NotEmpty(alertas);
        Assert.Empty(db2.Alertas.IgnoreQueryFilters().Where(a => a.EscritorioId == inativo.Id));
    }
}
