using System.Security.Cryptography;

namespace ContabOne.Api.Security;

/// <summary>
/// API key format: &lt;codigoProduto&gt;_&lt;prefixo8&gt;_&lt;segredo32&gt; — por
/// exemplo `nfse_a1b2c3d4_…` ou `det_a1b2c3d4_…`.
/// Only SHA-256(segredo) + prefixo (clear) are stored.
/// High-entropy random secret → SHA-256 is enough; no bcrypt needed (§7).
///
/// O primeiro campo diz QUAL ferramenta do hub a chave habilita. Ele não
/// participa da busca nem do hash (o lookup é prefixo8 + hash do segredo) —
/// serve para identificar a origem da chave em log e no suporte sem ir ao
/// banco, e para o handler recusar chave cujo produto não bate com o do
/// agente.
///
/// Repare no que este arquivo NÃO faz: validar o código contra o catálogo de
/// produtos. É deliberado. Se a validação de formato dependesse da tabela
/// `Produtos`, o caminho de autenticação passaria a depender de dado mutável
/// — uma linha apagada ou renomeada derrubaria todos os agentes daquele
/// produto. Em vez disso o handler compara o código apresentado contra o
/// `Produto.Codigo` do PRÓPRIO agente encontrado, que já vem no mesmo JOIN.
/// Chave com código inexistente simplesmente não acha agente e toma 401.
/// </summary>
public static class ApiKeyHasher
{
    private const int PrefixoLength = 8;
    private const int SegredoLength = 32;

    public static (string chaveCompleta, string prefixo, string hash) Gerar(string codigoProduto)
    {
        ArgumentException.ThrowIfNullOrEmpty(codigoProduto);

        var prefixo = Convert.ToHexString(RandomNumberGenerator.GetBytes(PrefixoLength / 2)).ToLower();
        var segredo = Convert.ToHexString(RandomNumberGenerator.GetBytes(SegredoLength / 2)).ToLower();
        var chaveCompleta = $"{codigoProduto}_{prefixo}_{segredo}";
        var hash = HashSegredo(segredo);
        return (chaveCompleta, prefixo, hash);
    }

    public static string HashApiKey(string chaveCompleta)
    {
        var parts = chaveCompleta.Split('_');
        if (parts.Length != 3 || parts[0].Length == 0 || parts[2].Length != SegredoLength)
            throw new ArgumentException("Formato de API key inválido");
        return HashSegredo(parts[2]);
    }

    public static string ExtrairPrefixo(string chaveCompleta)
    {
        var parts = chaveCompleta.Split('_');
        return parts.Length == 3 ? parts[1] : string.Empty;
    }

    /// <summary>
    /// Código de produto declarado pela chave crua — o que o handler compara
    /// contra o produto do agente. Vazio para chave malformada.
    /// </summary>
    public static string ExtrairCodigoProduto(string chaveCompleta)
    {
        var parts = chaveCompleta.Split('_');
        return parts.Length == 3 ? parts[0] : string.Empty;
    }

    private static string HashSegredo(string segredo)
        => Convert.ToHexString(SHA256.HashData(
            System.Text.Encoding.UTF8.GetBytes(segredo))).ToLower();
}
