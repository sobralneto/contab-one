using System.Security.Cryptography;
using ContabOne.Api.Domain;

namespace ContabOne.Api.Security;

/// <summary>
/// API key format: &lt;produto&gt;_&lt;prefixo8&gt;_&lt;segredo32&gt; — por exemplo
/// `nfse_a1b2c3d4_…` ou `det_a1b2c3d4_…`.
/// Only SHA-256(segredo) + prefixo (clear) are stored.
/// High-entropy random secret → SHA-256 is enough; no bcrypt needed (§7).
///
/// O primeiro campo diz QUAL ferramenta do hub a chave habilita. Ele não
/// participa da busca nem do hash (o lookup é prefixo8 + hash) — é gate de
/// formato e identificação: em log e no suporte dá para saber de onde veio a
/// chave sem consultar o banco, e o handler recusa chave cujo produto não
/// bate com o gravado no agente.
///
/// A lista de prefixos válidos é derivada de <see cref="Produto"/>, não
/// mantida à mão: prefixo é o nome do valor em minúsculas. Um produto novo no
/// enum já passa a ser aceito aqui.
/// </summary>
public static class ApiKeyHasher
{
    private const int PrefixoLength = 8;
    private const int SegredoLength = 32;

    // Derivada uma vez do enum. Comparação exata em minúsculas de propósito:
    // Enum.TryParse com ignoreCase aceitaria também a forma numérica ("0_…"),
    // que não é chave que este código jamais emitiu.
    private static readonly (string Prefixo, Produto Produto)[] Prefixos =
        Enum.GetValues<Produto>()
            .Select(p => (p.ToString().ToLowerInvariant(), p))
            .ToArray();

    public static string PrefixoDe(Produto produto)
        => produto.ToString().ToLowerInvariant();

    public static (string chaveCompleta, string prefixo, string hash) Gerar(Produto produto)
    {
        var prefixo = Convert.ToHexString(RandomNumberGenerator.GetBytes(PrefixoLength / 2)).ToLower();
        var segredo = Convert.ToHexString(RandomNumberGenerator.GetBytes(SegredoLength / 2)).ToLower();
        var chaveCompleta = $"{PrefixoDe(produto)}_{prefixo}_{segredo}";
        var hash = HashSegredo(segredo);
        return (chaveCompleta, prefixo, hash);
    }

    public static string HashApiKey(string chaveCompleta)
    {
        var parts = chaveCompleta.Split('_');
        if (parts.Length != 3 || !TentarProduto(parts[0], out _) || parts[2].Length != SegredoLength)
            throw new ArgumentException("Formato de API key inválido");
        return HashSegredo(parts[2]);
    }

    public static string ExtrairPrefixo(string chaveCompleta)
    {
        var parts = chaveCompleta.Split('_');
        return parts.Length == 3 ? parts[1] : string.Empty;
    }

    /// <summary>
    /// Produto declarado pela chave crua. `false` para chave malformada ou de
    /// produto desconhecido — quem chama trata como formato inválido.
    /// </summary>
    public static bool TentarExtrairProduto(string chaveCompleta, out Produto produto)
    {
        var parts = chaveCompleta.Split('_');
        if (parts.Length == 3)
            return TentarProduto(parts[0], out produto);

        produto = default;
        return false;
    }

    private static bool TentarProduto(string prefixoProduto, out Produto produto)
    {
        foreach (var (prefixo, valor) in Prefixos)
        {
            if (prefixo == prefixoProduto)
            {
                produto = valor;
                return true;
            }
        }

        produto = default;
        return false;
    }

    private static string HashSegredo(string segredo)
        => Convert.ToHexString(SHA256.HashData(
            System.Text.Encoding.UTF8.GetBytes(segredo))).ToLower();
}
