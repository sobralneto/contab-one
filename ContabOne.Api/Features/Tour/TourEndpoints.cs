using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Tour;

/// <summary>
/// Explicação de primeira visita por página. O escopo aqui é o usuário, não o
/// escritório: dois usuários do mesmo escritório veem cada um a sua explicação.
/// O UsuarioId vem sempre do token (TenantContext), nunca da rota — aceitar da
/// rota deixaria um usuário marcar/apagar o tour de outro.
/// </summary>
public static class TourEndpoints
{
    public static RouteGroupBuilder MapTourEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/", ListarVistasAsync);
        group.MapPost("/{pagina}", MarcarVistaAsync);
        return group;
    }

    private static async Task<IResult> ListarVistasAsync(AppDbContext db, TenantContext tenant)
    {
        if (tenant.UsuarioId == null)
            return Results.Unauthorized();

        var vistas = await db.TourPaginasVistas
            .Where(t => t.UsuarioId == tenant.UsuarioId)
            .Select(t => t.Pagina)
            .ToListAsync();

        return Results.Ok(vistas);
    }

    private static async Task<IResult> MarcarVistaAsync(
        string pagina, AppDbContext db, TenantContext tenant)
    {
        if (tenant.UsuarioId == null)
            return Results.Unauthorized();

        if (string.IsNullOrWhiteSpace(pagina) || pagina.Length > 60)
            return Results.ValidationProblem(new Dictionary<string, string[]>
            {
                ["pagina"] = ["Nome de página inválido"],
            });

        // Idempotente: a tela pode reenviar (duplo clique, retry do interceptor)
        // e a chave composta transformaria a segunda gravação em 500.
        var jaExiste = await db.TourPaginasVistas
            .AnyAsync(t => t.UsuarioId == tenant.UsuarioId && t.Pagina == pagina);

        if (!jaExiste)
        {
            db.TourPaginasVistas.Add(new TourPaginaVista
            {
                UsuarioId = tenant.UsuarioId.Value,
                Pagina = pagina,
            });
            await db.SaveChangesAsync();
        }

        return Results.Ok(new { pagina, vista = true });
    }
}
