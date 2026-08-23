using System.Security.Cryptography;

namespace ContabOne.Api.Security;

/// <summary>
/// API key format: nfse_&lt;prefixo8&gt;_&lt;segredo32&gt;
/// Only SHA-256(segredo) + prefixo (clear) are stored.
/// High-entropy random secret → SHA-256 is enough; no bcrypt needed (§7).
/// </summary>
public static class ApiKeyHasher
{
    private const string Prefix = "nfse";
    private const int PrefixoLength = 8;
    private const int SegredoLength = 32;

    public static (string chaveCompleta, string prefixo, string hash) Gerar()
    {
        var prefixo = Convert.ToHexString(RandomNumberGenerator.GetBytes(PrefixoLength / 2)).ToLower();
        var segredo = Convert.ToHexString(RandomNumberGenerator.GetBytes(SegredoLength / 2)).ToLower();
        var chaveCompleta = $"{Prefix}_{prefixo}_{segredo}";
        var hash = HashSegredo(segredo);
        return (chaveCompleta, prefixo, hash);
    }

    public static string HashApiKey(string chaveCompleta)
    {
        var parts = chaveCompleta.Split('_');
        if (parts.Length != 3 || parts[0] != Prefix || parts[2].Length != SegredoLength)
            throw new ArgumentException("Formato de API key inválido");
        return HashSegredo(parts[2]);
    }

    public static string ExtrairPrefixo(string chaveCompleta)
    {
        var parts = chaveCompleta.Split('_');
        return parts.Length == 3 ? parts[1] : string.Empty;
    }

    private static string HashSegredo(string segredo)
        => Convert.ToHexString(SHA256.HashData(
            System.Text.Encoding.UTF8.GetBytes(segredo))).ToLower();
}
