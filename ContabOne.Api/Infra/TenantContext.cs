using System.Security.Claims;

namespace ContabOne.Api.Infra;

/// <summary>
/// Resolved once per request from JWT claim or agent API key.
/// Never from route parameter or query string — that would be an IDOR vector (§5).
/// </summary>
public class TenantContext
{
    public Guid? EscritorioId { get; private set; }
    public Guid? UsuarioId { get; private set; }
    public Guid? AgenteId { get; private set; }
    public string? Papel { get; private set; }

    public bool IsAdmin => Papel == "PlatformAdmin";
    public bool IsAgent => AgenteId.HasValue;

    /// <summary>
    /// Verdadeiro somente depois de <see cref="FromAdmin"/> — é o sinal
    /// explícito de "vê todos os escritórios", separado da ausência de escopo
    /// (que antes também significava "vê tudo" — o bug de fail-open).
    /// </summary>
    public bool VeTodosOsEscritorios { get; private set; }

    public void FromUsuario(Guid escritorioId, Guid usuarioId, string papel)
    {
        EscritorioId = escritorioId;
        UsuarioId = usuarioId;
        Papel = papel;
    }

    public void FromAdmin(Guid usuarioId)
    {
        UsuarioId = usuarioId;
        Papel = "PlatformAdmin";
        VeTodosOsEscritorios = true;
        EscritorioId = null; // sem filtro — VeTodosOsEscritorios é o sinal
    }

    public void FromAgente(Guid escritorioId, Guid agenteId)
    {
        EscritorioId = escritorioId;
        AgenteId = agenteId;
        Papel = "Agente";
    }
}
