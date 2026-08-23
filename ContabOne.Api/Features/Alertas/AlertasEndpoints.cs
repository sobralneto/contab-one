using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Alertas;

public static class AlertasEndpoints
{
    public static RouteGroupBuilder MapAlertasEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/", ListarAsync);
        group.MapPost("/{id:guid}/resolver", ResolverAsync);
        return group;
    }

    private static async Task<IResult> ListarAsync(AppDbContext db, TenantContext tenant)
    {
        var alertas = await db.Alertas
            .Include(a => a.Cliente)
            .OrderByDescending(a => a.ResolvidoEm == null) // a.Aberto (propriedade computada) não traduz em OrderBy
            .ThenByDescending(a => a.CriadoEm)
            .Take(50)
            .Select(a => new AlertaDto
            {
                Id = a.Id,
                Tipo = a.Tipo.ToString(),
                Severidade = a.Severidade.ToString(),
                Mensagem = a.Mensagem,
                CriadoEm = a.CriadoEm,
                ResolvidoEm = a.ResolvidoEm,
                ClienteNome = a.Cliente != null ? a.Cliente.Nome : null,
                Aberto = a.Aberto,
            })
            .ToListAsync();

        return Results.Ok(alertas);
    }

    private static async Task<IResult> ResolverAsync(
        Guid id,
        AppDbContext db,
        TenantContext tenant)
    {
        var alerta = await db.Alertas.FindAsync(id);
        if (alerta == null)
            return Results.NotFound();

        alerta.ResolvidoEm = DateTime.UtcNow;
        await db.SaveChangesAsync();

        return Results.Ok(new { alerta.Id, resolvido = true });
    }
}

public record AlertaDto
{
    public Guid Id { get; init; }
    public string Tipo { get; init; } = string.Empty;
    public string Severidade { get; init; } = string.Empty;
    public string Mensagem { get; init; } = string.Empty;
    public DateTime CriadoEm { get; init; }
    public DateTime? ResolvidoEm { get; init; }
    public string? ClienteNome { get; init; }
    public bool Aberto { get; init; }
}
