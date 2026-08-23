using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Jobs;

/// <summary>
/// Railway Cron job — runs once per day (§9).
/// Scans all escritorios for alert conditions.
/// Alerts are idempotent: won't create a duplicate if one is already open.
/// </summary>
public class AlertaJob
{
    private readonly AppDbContext _db;

    public AlertaJob(AppDbContext db)
    {
        _db = db;
    }

    public async Task ExecutarAsync(CancellationToken ct = default)
    {
        var hoje = DateOnly.FromDateTime(DateTime.UtcNow);
        var limite30d = hoje.AddDays(30);
        var tresDiasAtras = DateTime.UtcNow.AddDays(-3);

        var escritorios = await _db.Escritorios
            .IgnoreQueryFilters()
            .Where(e => e.Status == StatusEscritorio.Ativo)
            .ToListAsync(ct);

        foreach (var esc in escritorios)
        {
            await VerificarCertificadosAsync(esc.Id, hoje, limite30d, ct);
            await VerificarAgenteSilenciosoAsync(esc.Id, tresDiasAtras, ct);
        }
    }

    private async Task VerificarCertificadosAsync(
        Guid escritorioId, DateOnly hoje, DateOnly limite30d, CancellationToken ct)
    {
        var clientes = await _db.Clientes
            .IgnoreQueryFilters()
            .Where(c => c.EscritorioId == escritorioId && c.CertificadoValidade != null)
            .ToListAsync(ct);

        foreach (var cliente in clientes)
        {
            var validade = cliente.CertificadoValidade!.Value;

            if (validade < hoje)
            {
                await CriarAlertaSeNaoExiste(escritorioId, cliente.Id,
                    TipoAlerta.CertificadoVencido,
                    SeveridadeAlerta.Critico,
                    $"Certificado de {cliente.Nome} ({cliente.Codigo}) venceu em {validade:dd/MM/yyyy}",
                    ct);
            }
            else if (validade <= limite30d)
            {
                await CriarAlertaSeNaoExiste(escritorioId, cliente.Id,
                    TipoAlerta.CertificadoVencendo,
                    SeveridadeAlerta.Atencao,
                    $"Certificado de {cliente.Nome} ({cliente.Codigo}) vence em {validade:dd/MM/yyyy}",
                    ct);
            }
        }
    }

    private async Task VerificarAgenteSilenciosoAsync(
        Guid escritorioId, DateTime tresDiasAtras, CancellationToken ct)
    {
        var temExecucaoRecente = await _db.Execucoes
            .IgnoreQueryFilters()
            .AnyAsync(e => e.EscritorioId == escritorioId && e.IniciadoEm >= tresDiasAtras, ct);

        if (!temExecucaoRecente)
        {
            // Check if there are any agents at all
            var temAgentes = await _db.Agentes
                .IgnoreQueryFilters()
                .AnyAsync(a => a.EscritorioId == escritorioId && a.RevogadoEm == null, ct);

            if (temAgentes)
            {
                await CriarAlertaSeNaoExiste(escritorioId, null,
                    TipoAlerta.AgenteSilencioso,
                    SeveridadeAlerta.Atencao,
                    "Nenhuma execução registrada há mais de 3 dias",
                    ct);
            }
        }
    }

    private async Task CriarAlertaSeNaoExiste(
        Guid escritorioId, Guid? clienteId,
        TipoAlerta tipo, SeveridadeAlerta severidade,
        string mensagem, CancellationToken ct)
    {
        var jaExiste = await _db.Alertas
            .IgnoreQueryFilters()
            .AnyAsync(AlertaExpressoes.Aberto(escritorioId, tipo, clienteId), ct);

        if (!jaExiste)
        {
            _db.Alertas.Add(new Alerta
            {
                EscritorioId = escritorioId,
                ClienteId = clienteId,
                Tipo = tipo,
                Severidade = severidade,
                Mensagem = mensagem,
            });
            await _db.SaveChangesAsync(ct);
        }
    }
}
