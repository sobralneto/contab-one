using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Security;

namespace ContabOne.Api.Features.Dashboard;

public static class AgentesManagementEndpoints
{
    public static RouteGroupBuilder MapAgentesManagementEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/", ListarAsync);
        group.MapPost("/", CriarAsync);
        group.MapDelete("/{id:guid}", RevogarAsync);
        return group;
    }

    private static async Task<IResult> ListarAsync(
        AppDbContext db,
        TenantContext tenant)
    {
        var agentes = await db.Agentes
            .Select(a => new
            {
                a.Id,
                a.Nome,
                Produto = a.Produto.ToString(), // frontend espera string, como Papel e Status
                a.ApiKeyPrefixo,
                a.VersaoAgente,
                a.UltimoContatoEm,
                a.CriadoEm,
                Ativo = a.RevogadoEm == null,
                a.RevogadoEm,
                EscritorioNome = a.Escritorio.Nome,
            })
            .OrderByDescending(a => a.CriadoEm) // mais recentes primeiro
            .ToListAsync();

        return Results.Ok(agentes);
    }

    private static async Task<IResult> CriarAsync(
        CriarAgenteRequest req,
        AppDbContext db,
        TenantContext tenant)
    {
        var escId = tenant.EscritorioId ?? req.EscritorioId;
        if (escId == null)
            return Results.BadRequest(new { erro = "EscritorioId é obrigatório para admin da plataforma" });

        // Ausente = Nfse: mantém compatível quem já chamava o endpoint sem o
        // campo, que era a única ferramenta existente. IsDefined junto do
        // TryParse porque TryParse sozinho aceita a forma numérica ("7") e
        // devolveria um Produto que não existe.
        var produto = Produto.Nfse;
        if (!string.IsNullOrEmpty(req.Produto) &&
            !(Enum.TryParse(req.Produto, ignoreCase: true, out produto) && Enum.IsDefined(produto)))
            return Results.BadRequest(new { erro = $"Produto inválido: {req.Produto}" });

        // Check plan limit
        var qtdAtivos = await db.Agentes.IgnoreQueryFilters().CountAsync(a => a.EscritorioId == escId && a.RevogadoEm == null);
        var plano = await db.Escritorios
            .IgnoreQueryFilters()
            .Where(e => e.Id == escId)
            .Select(e => e.Plano)
            .FirstOrDefaultAsync();

        if (plano != null && qtdAtivos >= plano.MaxAgentes)
            return Results.BadRequest(new { erro = "Limite de agentes do plano atingido" });

        var (chaveCompleta, prefixo, hash) = ApiKeyHasher.Gerar(produto);

        var agente = new Agente
        {
            EscritorioId = escId.Value,
            Nome = req.Nome,
            Produto = produto,
            ApiKeyHash = hash,
            ApiKeyPrefixo = prefixo,
        };

        db.Agentes.Add(agente);
        await db.SaveChangesAsync();

        // Return the full key — only time it's shown
        return Results.Created($"/api/agentes/{agente.Id}", new
        {
            agente.Id,
            agente.Nome,
            Produto = produto.ToString(),
            ApiKey = chaveCompleta, // exibida uma única vez (§7)
            Aviso = "Guarde esta chave agora. Ela não será exibida novamente.",
        });
    }

    private static async Task<IResult> RevogarAsync(
        Guid id,
        AppDbContext db,
        TenantContext tenant)
    {
        var agente = await db.Agentes.FindAsync(id);
        if (agente == null)
            return Results.NotFound();

        agente.RevogadoEm = DateTime.UtcNow;
        await db.SaveChangesAsync();

        return Results.Ok(new { agente.Id, revogado = true });
    }
}

public record CriarAgenteRequest
{
    public string Nome { get; init; } = string.Empty;
    public Guid? EscritorioId { get; init; } // only for PlatformAdmin

    /// <summary>
    /// Nome do valor de <see cref="Produto"/> ("Nfse", "Det"). Ausente = Nfse.
    /// </summary>
    public string? Produto { get; init; }
}
