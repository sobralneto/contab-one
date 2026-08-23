using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace ContabOne.Api.Security;

/// <summary>
/// Cifra o bloco `configuracao` do handshake com uma chave simétrica
/// derivada da própria API key do agente (design.md, Decisão 2/3 do change
/// agente-config-minima-cifrada) — nenhum segredo novo em config.toml ou nas
/// variáveis de ambiente da API. A API só vê a API key bruta em memória, no
/// próprio request autenticado; nunca a persiste (mesma garantia de
/// <see cref="ApiKeyHasher"/>, que só guarda o hash).
///
/// Chave: HMAC-SHA256(key = API key bruta, msg = rótulo fixo).
/// Envelope: base64(nonce[12] ‖ ciphertext ‖ tag[16]) — AES-256-GCM.
/// </summary>
public static class ConfiguracaoCipher
{
    private static readonly byte[] Rotulo = Encoding.UTF8.GetBytes("nfse-configuracao-v1");
    private const int NonceLength = 12;
    private const int TagLength = 16;

    public static byte[] DerivarChave(string apiKeyBruta)
    {
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(apiKeyBruta));
        return hmac.ComputeHash(Rotulo);
    }

    public static string Cifrar(string apiKeyBruta, Dictionary<string, string> configuracao)
    {
        var chave = DerivarChave(apiKeyBruta);
        var plaintext = JsonSerializer.SerializeToUtf8Bytes(configuracao);

        var nonce = RandomNumberGenerator.GetBytes(NonceLength);
        var ciphertext = new byte[plaintext.Length];
        var tag = new byte[TagLength];

        using (var aesGcm = new AesGcm(chave, TagLength))
        {
            aesGcm.Encrypt(nonce, plaintext, ciphertext, tag);
        }

        var envelope = new byte[NonceLength + ciphertext.Length + TagLength];
        Buffer.BlockCopy(nonce, 0, envelope, 0, NonceLength);
        Buffer.BlockCopy(ciphertext, 0, envelope, NonceLength, ciphertext.Length);
        Buffer.BlockCopy(tag, 0, envelope, NonceLength + ciphertext.Length, TagLength);

        return Convert.ToBase64String(envelope);
    }

    /// <summary>
    /// Só usado pela suíte de testes (o agente Python é quem decifra de
    /// verdade em produção) — confirma o round-trip do envelope contra a
    /// mesma derivação de chave.
    /// </summary>
    public static Dictionary<string, string> Decifrar(string apiKeyBruta, string envelopeBase64)
    {
        var chave = DerivarChave(apiKeyBruta);
        var envelope = Convert.FromBase64String(envelopeBase64);

        var nonce = envelope[..NonceLength];
        var tag = envelope[^TagLength..];
        var ciphertext = envelope[NonceLength..^TagLength];
        var plaintext = new byte[ciphertext.Length];

        using (var aesGcm = new AesGcm(chave, TagLength))
        {
            aesGcm.Decrypt(nonce, ciphertext, tag, plaintext);
        }

        return JsonSerializer.Deserialize<Dictionary<string, string>>(plaintext) ?? [];
    }
}
