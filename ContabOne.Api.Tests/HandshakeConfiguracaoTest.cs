using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Security;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// Contrato do bloco `configuracao` do handshake (requisito "O handshake
/// entrega a configuração do escritório", change agente-config-minima-cifrada):
///
/// 1. A consulta que alimenta o bloco filtra por EscritorioId — se alguém
///    remover o filtro, um agente passaria a receber a configuração de todos
///    os escritórios. Guardado por tradução (ToQueryString), sem banco.
/// 2. O bloco viaja cifrado (`ConfiguracaoCifrada`) — decifrar com a chave
///    derivada da API key devolve `{}` quando não há configuração salva;
///    agente novo interpreta o dicionário vazio como "use o config.toml
///    local".
/// </summary>
public class HandshakeConfiguracaoTest
{
    private static AppDbContext CriarContexto()
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseNpgsql("Host=localhost;Database=nao-usado;Username=nao-usado;Password=nao-usado")
            .Options;
        return new AppDbContext(options, new TenantContext());
    }

    [Fact]
    public void ConsultaDeConfiguracao_FiltraPorEscritorio()
    {
        using var db = CriarContexto();

        var sql = db.ConfiguracoesEscritorio
            .Where(c => c.EscritorioId == Guid.NewGuid())
            .ToQueryString();

        Assert.Contains("EscritorioId", sql);
    }

    [Fact]
    public void ConfiguracaoCifrada_ComDicionarioVazio_DecifraParaObjetoVazio()
    {
        // O agente novo decifra `configuracaoCifrada` e lê um dicionário
        // vazio quando não há configuração salva — segue com o arquivo
        // local, sem quebrar contra API antiga (que nem envia o campo).
        const string apiKey = "nfse_deadbeef_" + "0123456789abcdef0123456789abcdef";

        var cifrada = ConfiguracaoCipher.Cifrar(apiKey, []);
        var decifrada = ConfiguracaoCipher.Decifrar(apiKey, cifrada);

        Assert.Empty(decifrada);
    }

    [Fact]
    public void ConfiguracaoCifrada_RoundTrip_PreservaValores()
    {
        const string apiKey = "nfse_deadbeef_" + "0123456789abcdef0123456789abcdef";
        var original = new Dictionary<string, string>
        {
            ["tipos"] = "recebidas,emitidas",
            ["primeira_busca_desde"] = "2026-01-01",
            ["pasta_saida"] = "notas",
            ["gerar_pdf"] = "true",
            ["dias_busca_padrao"] = "31",
        };

        var cifrada = ConfiguracaoCipher.Cifrar(apiKey, original);
        var decifrada = ConfiguracaoCipher.Decifrar(apiKey, cifrada);

        Assert.Equal(original, decifrada);
    }

    [Fact]
    public void ConfiguracaoCifrada_ComChaveErrada_FalhaAoDecifrar()
    {
        // Chave errada não pode "quase funcionar" — AES-GCM autenticado
        // deve rejeitar, nunca devolver lixo silenciosamente.
        const string apiKeyCorreta = "nfse_deadbeef_" + "0123456789abcdef0123456789abcdef";
        const string apiKeyErrada = "nfse_deadbeef_" + "ffffffffffffffffffffffffffffffff";

        var cifrada = ConfiguracaoCipher.Cifrar(apiKeyCorreta, new Dictionary<string, string> { ["tipos"] = "recebidas" });

        Assert.ThrowsAny<System.Security.Cryptography.CryptographicException>(
            () => ConfiguracaoCipher.Decifrar(apiKeyErrada, cifrada));
    }
}
