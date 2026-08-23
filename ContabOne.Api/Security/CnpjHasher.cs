using System.Security.Cryptography;
using System.Text;

namespace ContabOne.Api.Security;

/// <summary>
/// CNPJ handling: hash for equality/dedup, masked for display (§4.3).
/// Full CNPJ is NEVER persisted — only hash + masked version.
/// </summary>
public static class CnpjHasher
{
    /// <summary>
    /// HMAC-SHA256(clean_cnpj, server_secret) — stable, non-reversible.
    /// </summary>
    public static string Hash(string cnpjLimpo, string hmacKey)
    {
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(hmacKey));
        var hash = hmac.ComputeHash(Encoding.UTF8.GetBytes(cnpjLimpo));
        return Convert.ToHexString(hash).ToLower();
    }

    /// <summary>
    /// Masks: 54283546000126 → 54.283.***/**26
    /// </summary>
    public static string Mascarar(string cnpjLimpo)
    {
        if (cnpjLimpo.Length != 14)
            return cnpjLimpo; // can't mask what isn't a full CNPJ

        return $"{cnpjLimpo[..2]}.{cnpjLimpo[2..5]}.***/**{cnpjLimpo[12..]}";
    }
}
