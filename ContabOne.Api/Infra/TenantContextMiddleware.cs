using System.Security.Claims;

namespace ContabOne.Api.Infra;

/// <summary>
/// Populates TenantContext from JWT claims (for web users) on every request.
/// Agent flows are handled directly by ApiKeyAuthenticationHandler.
/// Must run AFTER authentication, BEFORE authorization.
/// </summary>
public class TenantContextMiddleware
{
    private readonly RequestDelegate _next;

    public TenantContextMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context, TenantContext tenantContext)
    {
        var user = context.User;

        if (user.Identity?.IsAuthenticated == true)
        {
            var papel = user.FindFirstValue(ClaimTypes.Role);
            var usuarioIdStr = user.FindFirstValue(ClaimTypes.NameIdentifier);
            var escritorioIdStr = user.FindFirstValue("escritorio_id");

            if (papel == "PlatformAdmin" && Guid.TryParse(usuarioIdStr, out var adminId))
            {
                tenantContext.FromAdmin(adminId);
            }
            else if (papel == "Agente")
            {
                // Already set by ApiKeyAuthenticationHandler — skip
            }
            else if (papel is "EscritorioAdmin" or "EscritorioUsuario")
            {
                if (Guid.TryParse(escritorioIdStr, out var escritorioId) &&
                    Guid.TryParse(usuarioIdStr, out var usuarioId))
                {
                    tenantContext.FromUsuario(escritorioId, usuarioId, papel);
                }
                else
                {
                    // Usuário com papel de escritório sem escritorio_id
                    // resolvível: é o cenário que reproduziu o achado de
                    // isolamento. Rejeitar aqui, em vez de deixar seguir com
                    // contexto vazio e o filtro abrir (ou, com o fail-closed,
                    // parecer tela vazia sem explicação).
                    context.Response.StatusCode = StatusCodes.Status401Unauthorized;
                    context.Response.ContentType = "application/json; charset=utf-8";
                    await context.Response.WriteAsync(
                        "{\"erro\":\"Sessão inválida: escritório não identificado. Refaça o login.\"}");
                    return;
                }
            }
        }

        await _next(context);
    }
}
