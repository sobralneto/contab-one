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

        string prefixo, hash, codigoProdutoDaChave;
        try
        {
            prefixo = ApiKeyHasher.ExtrairPrefixo(apiKey);
            hash = ApiKeyHasher.HashApiKey(apiKey);
            codigoProdutoDaChave = ApiKeyHasher.ExtrairCodigoProduto(apiKey);
            if (string.IsNullOrEmpty(prefixo) || string.IsNullOrEmpty(codigoProdutoDaChave))
                return AuthenticateResult.Fail("Formato de API key inválido");
        }
        catch
        {
            return AuthenticateResult.Fail("Formato de API key inválido");
        }

        var agente = await _db.Agentes
            .IgnoreQueryFilters() // agent lookup must cross tenants
            .Include(a => a.Escritorio)
            .Include(a => a.Produto)
            .FirstOrDefaultAsync(a => a.ApiKeyPrefixo == prefixo && a.ApiKeyHash == hash);

        if (agente == null)
            return AuthenticateResult.Fail("API key inválida");

        if (!agente.Ativo)
            return AuthenticateResult.Fail("API key revogada");

        // O produto declarado pela chave tem que bater com o do agente. A
        // comparação é contra o Produto do PRÓPRIO agente (veio no mesmo
        // JOIN), nunca contra o catálogo: assim nenhuma alteração na tabela
        // `Produtos` pode abrir ou fechar autenticação de quem já está em
        // campo. Produto inativo continua autenticando de propósito —
        // desativar só tira o produto da oferta de novas chaves.
        if (!string.Equals(agente.Produto.Codigo, codigoProdutoDaChave, StringComparison.Ordinal))
            return AuthenticateResult.Fail("API key inválida");

        if (agente.Escritorio.Status != StatusEscritorio.Ativo)
            return AuthenticateResult.Fail("Escritório não está ativo");

        // Gate comercial, irmão do Status acima: o escritório precisa ter a
        // ferramenta contratada. Diferente da conferência de produto logo
        // acima (que só compara a chave com o próprio agente), este SIM
        // consulta dado mutável — de propósito, porque é exatamente o que
        // "descontratou a ferramenta" significa. O handshake é o ponto de
        // checagem de adimplência do produto inteiro.
        var contratado = await _db.EscritorioProdutos
            .IgnoreQueryFilters() // roda antes do TenantContext estar populado
            .AnyAsync(ep => ep.EscritorioId == agente.EscritorioId
                         && ep.ProdutoId == agente.ProdutoId
                         && ep.DesabilitadoEm == null);

        if (!contratado)
            return AuthenticateResult.Fail(
                $"Escritório não tem a ferramenta '{agente.Produto.Nome}' habilitada");

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
            new Claim("produto", agente.Produto.Codigo),
            new Claim(ClaimTypes.Role, "Agente"),
        };

        var identity = new ClaimsIdentity(claims, Scheme.Name);
        var principal = new ClaimsPrincipal(identity);
        var ticket = new AuthenticationTicket(principal, Scheme.Name);

        return AuthenticateResult.Success(ticket);
    }
}
