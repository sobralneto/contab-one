using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Dashboard;

public static class ExecucoesEndpoints
{
    public static RouteGroupBuilder MapExecucoesEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/", ListarAsync);
        group.MapGet("/{id:guid}", DetalheAsync);
        return group;
    }

    private static async Task<IResult> ListarAsync(
        string? agruparPor,
        int pagina = 1,
        int tamanho = 20,
        AppDbContext db = null!)
    {
        // Agrupamento por escritório (admin) ou por cliente (escritório/usuário).
        // Sem `agruparPor`, mantém o formato plano original (usado pelo dashboard).
        if (agruparPor == "escritorio")
        {
            var grupos = await AgruparPorEscritorioAsync(db);
            return Results.Ok(new { grupos });
        }

        if (agruparPor == "cliente")
        {
            var grupos = await AgruparPorClienteAsync(db);
            return Results.Ok(new { grupos });
        }

        tamanho = Math.Clamp(tamanho, 1, 100);
        var total = await db.Execucoes.CountAsync();

        var execucoes = await db.Execucoes
            .OrderByDescending(e => e.IniciadoEm)
            .Skip((pagina - 1) * tamanho)
            .Take(tamanho)
            .Select(e => new
            {
                e.Id,
                Status = e.Status.ToString(),
                e.IniciadoEm,
                e.FinalizadoEm,
                DuracaoMs = e.FinalizadoEm != null
                    ? (long)(e.FinalizadoEm.Value - e.IniciadoEm).TotalMilliseconds
                    : (long?)null,
                e.VersaoAgente,
                e.MensagemErro,
                TotalMetricas = e.Metricas.Count,
                TotalBaixadas = e.Metricas.Sum(m => m.QtdBaixadas),
                TotalFalhas = e.Metricas.Sum(m => m.QtdFalhas),
            })
            .ToListAsync();

        return Results.Ok(new { total, pagina, tamanho, dados = execucoes });
    }

    private static async Task<List<object>> AgruparPorEscritorioAsync(AppDbContext db)
    {
        var execucoes = await db.Execucoes
            .OrderByDescending(e => e.IniciadoEm)
            .Select(e => new
            {
                e.Id,
                e.EscritorioId,
                EscritorioNome = e.Escritorio.Nome,
                Status = e.Status.ToString(),
                e.IniciadoEm,
                e.FinalizadoEm,
                DuracaoMs = e.FinalizadoEm != null
                    ? (long)(e.FinalizadoEm.Value - e.IniciadoEm).TotalMilliseconds
                    : (long?)null,
                e.VersaoAgente,
                e.MensagemErro,
                TotalMetricas = e.Metricas.Count,
                TotalBaixadas = e.Metricas.Sum(m => m.QtdBaixadas),
                TotalFalhas = e.Metricas.Sum(m => m.QtdFalhas),
            })
            .ToListAsync();

        return execucoes
            .GroupBy(e => new { e.EscritorioId, e.EscritorioNome })
            .Select(g => new
            {
                escritorioId = g.Key.EscritorioId,
                escritorioNome = g.Key.EscritorioNome,
                total = g.Count(),
                sucesso = g.Count(e => e.Status == StatusExecucao.Sucesso.ToString()),
                parcial = g.Count(e => e.Status == StatusExecucao.Parcial.ToString()),
                falha = g.Count(e => e.Status == StatusExecucao.Falha.ToString()),
                execucoes = g,
            })
            .OrderByDescending(x => x.total)
            .Select(x => (object)x)
            .ToList();
    }

    private static async Task<List<object>> AgruparPorClienteAsync(AppDbContext db)
    {
        var linhas = await db.ExecucaoMetricas
            .GroupBy(m => new { m.ClienteId, m.Cliente.Nome, m.ExecucaoId, m.Execucao.Status })
            .Select(g => new
            {
                g.Key.ClienteId,
                g.Key.Nome,
                g.Key.ExecucaoId,
                g.Key.Status,
                Baixadas = g.Sum(x => x.QtdBaixadas),
            })
            .ToListAsync();

        return linhas
            .GroupBy(l => new { l.ClienteId, l.Nome })
            .Select(g => new
            {
                clienteId = g.Key.ClienteId,
                clienteNome = g.Key.Nome,
                total = g.Count(),
                sucesso = g.Count(l => l.Status == StatusExecucao.Sucesso),
                parcial = g.Count(l => l.Status == StatusExecucao.Parcial),
                falha = g.Count(l => l.Status == StatusExecucao.Falha),
                totalBaixadas = g.Sum(l => l.Baixadas),
            })
            .OrderByDescending(x => x.total)
            .Select(x => (object)x)
            .ToList();
    }

    private static async Task<IResult> DetalheAsync(
        Guid id,
        AppDbContext db)
    {
        var execucao = await db.Execucoes
            .Include(e => e.Metricas)
            .ThenInclude(m => m.Cliente)
            .FirstOrDefaultAsync(e => e.Id == id);

        if (execucao == null)
            return Results.NotFound();

        return Results.Ok(new
        {
            execucao.Id,
            Status = execucao.Status.ToString(),
            execucao.IniciadoEm,
            execucao.FinalizadoEm,
            DuracaoMs = execucao.FinalizadoEm != null
                ? (long)(execucao.FinalizadoEm.Value - execucao.IniciadoEm).TotalMilliseconds
                : (long?)null,
            execucao.VersaoAgente,
            execucao.MensagemErro,
            metricas = execucao.Metricas.Select(m => new
            {
                m.ClienteId,
                ClienteNome = m.Cliente?.Nome,
                Tipo = m.Tipo.ToString(),
                m.Competencia,
                m.QtdBaixadas,
                m.QtdPuladas,
                m.QtdFalhas,
                m.DuracaoMs,
            }),
        });
    }
}
