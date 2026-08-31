using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Dashboard;

public static class DashboardEndpoints
{
    public static RouteGroupBuilder MapDashboardEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/kpis", KpisAsync);
        group.MapGet("/series", SeriesAsync);
        group.MapGet("/ranking", RankingAsync);
        group.MapGet("/certificados", CertificadosAsync);
        return group;
    }

    private static async Task<IResult> KpisAsync(
        AppDbContext db,
        TenantContext tenant)
    {
        var hoje = DateOnly.FromDateTime(DateTime.UtcNow);
        var mesAtual = $"{hoje.Year:D4}-{hoje.Month:D2}";

        var totalClientes = await db.Clientes.CountAsync();
        var totalAgentesAtivos = await db.Agentes.CountAsync(a => a.RevogadoEm == null);

        var notasMes = await db.ExecucaoMetricas
            .Where(m => m.Competencia == mesAtual)
            .SumAsync(m => m.QtdBaixadas);

        var certificadosVencendo = await db.Clientes
            .Where(c => c.CertificadoValidade != null &&
                        c.CertificadoValidade <= hoje.AddDays(30) &&
                        c.CertificadoValidade >= hoje)
            .CountAsync();

        var ultimaExecucao = await db.Execucoes
            .OrderByDescending(e => e.IniciadoEm)
            .Select(e => new
            {
                e.Id,
                Status = e.Status.ToString(),
                e.IniciadoEm,
                DuracaoMs = e.FinalizadoEm != null
                    ? (long)(e.FinalizadoEm.Value - e.IniciadoEm).TotalMilliseconds
                    : (long?)null
            })
            .FirstOrDefaultAsync();

        return Results.Ok(new
        {
            totalClientes,
            totalAgentesAtivos,
            notasBaixadasMes = notasMes,
            certificadosVencendo30d = certificadosVencendo,
            ultimaExecucao,
        });
    }

    private static async Task<IResult> SeriesAsync(
        string? de,
        string? ate,
        Guid? escritorioId,
        Guid? clienteId,
        AppDbContext db)
    {
        var query = db.ExecucaoMetricas.AsQueryable();

        if (!string.IsNullOrEmpty(de))
            query = query.Where(m => m.Competencia.CompareTo(de) >= 0);

        if (!string.IsNullOrEmpty(ate))
            query = query.Where(m => m.Competencia.CompareTo(ate) <= 0);

        // Admin filtra por escritório; demais papéis por cliente (o query filter
        // global já limita ao próprio tenancy, então um escritorioId alheio não vaza)
        if (escritorioId.HasValue)
            query = query.Where(m => m.Cliente!.EscritorioId == escritorioId.Value);

        if (clienteId.HasValue)
            query = query.Where(m => m.ClienteId == clienteId.Value);

        // O eixo X do gráfico é a competência (mês); escritorioId/clienteId acima
        // já restringem a série a UMA entidade por vez, então a barra de cada mês
        // soma só o que o filtro deixou passar.
        var dados = await query
            .GroupBy(m => new { m.Competencia, m.Tipo })
            .Select(g => new
            {
                competencia = g.Key.Competencia,
                tipo = g.Key.Tipo.ToString(),
                qtd = g.Sum(x => x.QtdBaixadas),
            })
            .OrderBy(x => x.competencia)
            .ThenBy(x => x.tipo)
            .ToListAsync();

        return Results.Ok(dados);
    }

    private static async Task<IResult> RankingAsync(
        AppDbContext db,
        TenantContext tenant)
    {
        // Admin: ranking agregado por escritório; escritório/usuário: por cliente
        if (tenant.IsAdmin)
        {
            var ranking = await db.ExecucaoMetricas
                .GroupBy(m => new { m.Cliente!.EscritorioId, EscritorioNome = m.Cliente!.Escritorio.Nome })
                .Select(g => new
                {
                    clienteId = g.Key.EscritorioId,
                    nome = g.Key.EscritorioNome,
                    codigo = (string?)null,
                    total = g.Sum(x => x.QtdBaixadas),
                })
                .OrderByDescending(x => x.total)
                .Take(20)
                .ToListAsync();

            return Results.Ok(ranking);
        }

        var rankingClientes = await db.ExecucaoMetricas
            .GroupBy(m => new { m.ClienteId, m.Cliente.Nome, m.Cliente.Codigo })
            .Select(g => new
            {
                clienteId = g.Key.ClienteId,
                nome = g.Key.Nome,
                codigo = g.Key.Codigo,
                total = g.Sum(x => x.QtdBaixadas),
            })
            .OrderByDescending(x => x.total)
            .Take(20)
            .ToListAsync();

        return Results.Ok(rankingClientes);
    }

    private static async Task<IResult> CertificadosAsync(
        AppDbContext db,
        TenantContext tenant)
    {
        var hoje = DateOnly.FromDateTime(DateTime.UtcNow);
        var limite = hoje.AddDays(30);

        // Vencidos e vencendo em 30 dias, mais urgente primeiro. Mesmo limiar
        // usado no KPI (certificadosVencendo30d) e no AlertaJob.
        var certificados = await db.Clientes
            .Where(c => c.CertificadoValidade != null && c.CertificadoValidade <= limite)
            .OrderBy(c => c.CertificadoValidade)
            .Select(c => new
            {
                clienteId = c.Id,
                codigo = c.Codigo,
                nome = c.Nome,
                certificadoValidade = c.CertificadoValidade,
            })
            .Take(50)
            .ToListAsync();

        return Results.Ok(certificados);
    }
}
