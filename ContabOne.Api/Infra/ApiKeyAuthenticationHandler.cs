using System.Security.Claims;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using ContabOne.Api.Domain;
using ContabOne.Api.Security;

namespace ContabOne.Api.Infra;

/// <summary>
/// Authenticates agent requests via X-Api-Key header.
/// Sets claims from agent/escritorio, populates TenantContext.
/// </summary>
public class ApiKeyAuthenticationHandler : AuthenticationHandler<AuthenticationSchemeOptions>
{
    private readonly AppDbContext _db;
    private readonly TenantContext _tenantContext;

    public ApiKeyAuthenticationHandler(
        IOptionsMonitor<AuthenticationSchemeOptions> options,
        ILoggerFactory logger,
        UrlEncoder encoder,
        AppDbContext db,
        TenantContext tenantContext)
        : base(options, logger, encoder)
    {
        _db = db;
        _tenantContext = tenantContext;
    }

    protected override async Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.TryGetValue("X-Api-Key", out var header))
            return AuthenticateResult.NoResult();

        var apiKey = header.ToString();

        string prefixo, hash;
        Produto produtoDaChave;
        try
        {
            prefixo = ApiKeyHasher.ExtrairPrefixo(apiKey);
            hash = ApiKeyHasher.HashApiKey(apiKey);
            if (string.IsNullOrEmpty(prefixo))
                return AuthenticateResult.Fail("Formato de API key inválido");
            if (!ApiKeyHasher.TentarExtrairProduto(apiKey, out produtoDaChave))
                return AuthenticateResult.Fail("Formato de API key inválido");
        }
        catch
        {
            return AuthenticateResult.Fail("Formato de API key inválido");
        }

        var agente = await _db.Agentes
            .IgnoreQueryFilters() // agent lookup must cross tenants
            .Include(a => a.Escritorio)
            .FirstOrDefaultAsync(a => a.ApiKeyPrefixo == prefixo && a.ApiKeyHash == hash);

        if (agente == null)
            return AuthenticateResult.Fail("API key inválida");

        if (!agente.Ativo)
            return AuthenticateResult.Fail("API key revogada");

        // O produto declarado pela chave tem que bater com o gravado no
        // agente. Com prefixo8 aleatório a divergência é praticamente
        // inalcançável por acaso — o que este guarda tranca é a chave de uma
        // ferramenta valendo como se fosse de outra caso a linha seja
        // adulterada ou migrada errado.
        if (agente.Produto != produtoDaChave)
            return AuthenticateResult.Fail("API key inválida");

        if (agente.Escritorio.Status != StatusEscritorio.Ativo)
            return AuthenticateResult.Fail("Escritório não está ativo");

        // Update last contact
        agente.UltimoContatoEm = DateTime.UtcNow;
        await _db.SaveChangesAsync();

        // Populate tenant context
        _tenantContext.FromAgente(agente.EscritorioId, agente.Id);

        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, agente.Id.ToString()),
            new Claim("escritorio_id", agente.EscritorioId.ToString()),
            new Claim("agente_id", agente.Id.ToString()),
            new Claim("produto", agente.Produto.ToString()),
            new Claim(ClaimTypes.Role, "Agente"),
        };

        var identity = new ClaimsIdentity(claims, Scheme.Name);
        var principal = new ClaimsPrincipal(identity);
        var ticket = new AuthenticationTicket(principal, Scheme.Name);

        return AuthenticateResult.Success(ticket);
    }
}
