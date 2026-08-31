using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Dashboard;

/// <summary>
/// `produtoCodigo` é OPCIONAL de propósito: a tela de Execuções de uma
/// ferramenta sempre manda (via <see cref="Agente.ProdutoId"/>, resolvido
/// pelo código), mas o resumo da visão geral do dashboard continua
/// consultando sem filtro, exatamente como antes de existir mais de uma
/// ferramenta.
/// </summary>
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
        string? produtoCodigo,
        int pagina = 1,
        int tamanho = 20,
        AppDbContext db = null!)
    {
        // produtoCodigo é opcional: quem chama sem ele (hoje, só o resumo da
        // visão geral) continua vendo todas as execuções do escritório,
        // comportamento anterior a esta ferramenta ter mais de um produto.
        Guid? produtoId = null;
        if (produtoCodigo != null)
        {
            produtoId = await db.Produtos
                .Where(p => p.Codigo == produtoCodigo)
                .Select(p => (Guid?)p.Id)
                .FirstOrDefaultAsync();
            if (produtoId == null)
                return Results.BadRequest(new { erro = $"Ferramenta '{produtoCodigo}' não existe" });
        }

        // Agrupamento por escritório (admin) ou por cliente (escritório/usuário).
        // Sem `agruparPor`, mantém o formato plano original (usado pelo dashboard).
        if (agruparPor == "escritorio")
        {
            var grupos = await AgruparPorEscritorioAsync(db, produtoId);
            return Results.Ok(new { grupos });
        }

        if (agruparPor == "cliente")
        {
            var grupos = await AgruparPorClienteAsync(db, produtoId);
            return Results.Ok(new { grupos });
        }

        tamanho = Math.Clamp(tamanho, 1, 100);
        var baseQuery = produtoId == null
            ? db.Execucoes.AsQueryable()
            : db.Execucoes.Where(e => e.Agente.ProdutoId == produtoId.Value);

        var total = await baseQuery.CountAsync();

        var execucoes = await baseQuery
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

    private static async Task<List<object>> AgruparPorEscritorioAsync(AppDbContext db, Guid? produtoId)
    {
        var execucoes = await (produtoId == null
                ? db.Execucoes.AsQueryable()
                : db.Execucoes.Where(e => e.Agente.ProdutoId == produtoId.Value))
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
                // A execuções já vêm ordenadas por IniciadoEm desc (query acima) —
                // o status exibido no resumo é o da execução mais recente, não a
                // contagem de todas.
                ultimoStatus = g.OrderByDescending(e => e.IniciadoEm).First().Status,
                falha = g.Count(e => e.Status == StatusExecucao.Falha.ToString()),
                execucoes = g,
            })
            .OrderByDescending(x => x.total)
            .Select(x => (object)x)
            .ToList();
    }

    private static async Task<List<object>> AgruparPorClienteAsync(AppDbContext db, Guid? produtoId)
    {
        var linhas = await (produtoId == null
                ? db.ExecucaoMetricas.AsQueryable()
                : db.ExecucaoMetricas.Where(m => m.Execucao.Agente.ProdutoId == produtoId.Value))
            .GroupBy(m => new { m.ClienteId, m.Cliente.Nome, m.ExecucaoId, m.Execucao.Status, m.Execucao.IniciadoEm })
            .Select(g => new
            {
                g.Key.ClienteId,
                g.Key.Nome,
                g.Key.ExecucaoId,
                g.Key.Status,
                g.Key.IniciadoEm,
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
                // Status da execução mais recente do cliente, não a contagem de todas.
                ultimoStatus = g.OrderByDescending(l => l.IniciadoEm).First().Status.ToString(),
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
            metricas = execucao.Metricas
                .OrderBy(m => m.Cliente?.Nome)
                .ThenBy(m => m.Competencia)
                .ThenBy(m => m.Tipo)
                .Select(m => new
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
