using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Dashboard;

/// <summary>
/// Configuração é por (escritório, ferramenta) — `produtoCodigo` é
/// obrigatório nos dois verbos, porque não existe mais "a" configuração do
/// escritório, só a configuração dele para uma ferramenta específica.
/// </summary>
public static class ConfiguracaoEndpoints
{
    public static RouteGroupBuilder MapConfiguracaoEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/", ObterAsync);
        group.MapPut("/", SalvarAsync);
        return group;
    }

    private static async Task<IResult> ObterAsync(
        string? produtoCodigo,
        Guid? escritorioId,
        AppDbContext db,
        TenantContext tenant)
    {
        // Escritório/usuário são escopados pelo tenancy; admin precisa indicar o alvo
        var escId = tenant.EscritorioId ?? escritorioId;
        if (escId == null)
            return Results.BadRequest(new { erro = "EscritorioId é obrigatório para admin da plataforma" });

        // string (não Guid?) não tem checagem automática de "obrigatório" —
        // parâmetro ausente vira BadHttpRequestException não tratada, que o
        // handler global (Program.cs) transforma num 500 opaco. A checagem
        // manual é o que dá 400 com motivo, igual ao resto do arquivo.
        if (string.IsNullOrWhiteSpace(produtoCodigo))
            return Results.BadRequest(new { erro = "produtoCodigo é obrigatório" });

        var produtoId = await db.Produtos
            .Where(p => p.Codigo == produtoCodigo)
            .Select(p => (Guid?)p.Id)
            .FirstOrDefaultAsync();
        if (produtoId == null)
            return Results.BadRequest(new { erro = $"Ferramenta '{produtoCodigo}' não existe" });

        var configs = await db.ConfiguracoesEscritorio
            .Where(c => c.EscritorioId == escId.Value && c.ProdutoId == produtoId.Value)
            .ToListAsync();

        // Include plan limits so the frontend can disable features
        var plano = await db.Escritorios
            .Where(e => e.Id == escId.Value)
            .Select(e => e.Plano == null ? null : new
            {
                e.Plano.PermiteEmitidas,
                e.Plano.MaxClientes,
                e.Plano.MaxAgentes,
            })
            .FirstOrDefaultAsync();

        return Results.Ok(new
        {
            valores = configs.ToDictionary(c => c.Chave, c => c.Valor),
            // Sem plano atribuído → falha fechada (sem permissões/limites), não aberta.
            plano = plano ?? new { PermiteEmitidas = false, MaxClientes = 0, MaxAgentes = 0 },
        });
    }

    private static async Task<IResult> SalvarAsync(
        Dictionary<string, string> configs,
        string? produtoCodigo,
        Guid? escritorioId,
        AppDbContext db,
        TenantContext tenant)
    {
        var escId = tenant.EscritorioId ?? escritorioId;
        if (escId == null)
            return Results.BadRequest(new { erro = "EscritorioId é obrigatório para admin da plataforma" });

        if (string.IsNullOrWhiteSpace(produtoCodigo))
            return Results.BadRequest(new { erro = "produtoCodigo é obrigatório" });

        var produtoId = await db.Produtos
            .Where(p => p.Codigo == produtoCodigo)
            .Select(p => (Guid?)p.Id)
            .FirstOrDefaultAsync();
        if (produtoId == null)
            return Results.BadRequest(new { erro = $"Ferramenta '{produtoCodigo}' não existe" });

        // Remove existing configs deste escritório para ESTA ferramenta —
        // salvar a configuração do NFS-e não pode apagar a do DET.
        var existing = await db.ConfiguracoesEscritorio
            .Where(c => c.EscritorioId == escId.Value && c.ProdutoId == produtoId.Value)
            .ToListAsync();
        db.ConfiguracoesEscritorio.RemoveRange(existing);

        // Insert new ones
        foreach (var (chave, valor) in configs)
        {
            db.ConfiguracoesEscritorio.Add(new ConfiguracaoEscritorio
            {
                EscritorioId = escId.Value,
                ProdutoId = produtoId.Value,
                Chave = chave,
                Valor = valor,
            });
        }

        await db.SaveChangesAsync();
        return Results.Ok(new { salvas = configs.Count });
    }
}
