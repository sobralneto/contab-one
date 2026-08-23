using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Dashboard;

public static class ConfiguracaoEndpoints
{
    public static RouteGroupBuilder MapConfiguracaoEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/", ObterAsync);
        group.MapPut("/", SalvarAsync);
        return group;
    }

    private static async Task<IResult> ObterAsync(
        Guid? escritorioId,
        AppDbContext db,
        TenantContext tenant)
    {
        // Escritório/usuário são escopados pelo tenancy; admin precisa indicar o alvo
        var escId = tenant.EscritorioId ?? escritorioId;
        if (escId == null)
            return Results.BadRequest(new { erro = "EscritorioId é obrigatório para admin da plataforma" });

        var configs = await db.ConfiguracoesEscritorio
            .Where(c => c.EscritorioId == escId.Value)
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
        Guid? escritorioId,
        AppDbContext db,
        TenantContext tenant)
    {
        var escId = tenant.EscritorioId ?? escritorioId;
        if (escId == null)
            return Results.BadRequest(new { erro = "EscritorioId é obrigatório para admin da plataforma" });

        // Remove existing configs for this escritorio
        var existing = await db.ConfiguracoesEscritorio
            .Where(c => c.EscritorioId == escId.Value)
            .ToListAsync();
        db.ConfiguracoesEscritorio.RemoveRange(existing);

        // Insert new ones
        foreach (var (chave, valor) in configs)
        {
            db.ConfiguracoesEscritorio.Add(new ConfiguracaoEscritorio
            {
                EscritorioId = escId.Value,
                Chave = chave,
                Valor = valor,
            });
        }

        await db.SaveChangesAsync();
        return Results.Ok(new { salvas = configs.Count });
    }
}
