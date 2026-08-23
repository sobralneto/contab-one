using System.Text.Json;
using ContabOne.Api.Security;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// Funções puras de segurança: formato da API key, máscara e hash de CNPJ.
/// A paridade do hash de CNPJ com o agente Python é verificada contra o
/// arquivo compartilhado Nfse.Agent/testes/fixtures/cnpj_vetores.json — o
/// mesmo arquivo que o teste Python (teste_cnpj_vetores.py) lê.
/// </summary>
public class HashersTest
{
    // ── ApiKeyHasher ──

    [Fact]
    public void Gerar_ProduzChaveNoFormatoEsperado_EHashCorresponde()
    {
        var (chave, prefixo, hash) = ApiKeyHasher.Gerar();

        Assert.Matches("^nfse_[0-9a-f]{8}_[0-9a-f]{32}$", chave);
        Assert.Equal(8, prefixo.Length);
        Assert.Equal(hash, ApiKeyHasher.HashApiKey(chave));
        Assert.Equal(prefixo, ApiKeyHasher.ExtrairPrefixo(chave));
    }

    [Theory]
    [InlineData("sem-separador")]
    [InlineData("nfse_abcdefgh")]
    [InlineData("nfse_abcdefgh_segredo_curto")]
    [InlineData("outro_abcdefgh_0123456789abcdef0123456789abcdef")]
    public void HashApiKey_RejeitaFormatosInvalidos(string chave)
    {
        Assert.Throws<ArgumentException>(() => ApiKeyHasher.HashApiKey(chave));
    }

    // ── CnpjHasher.Mascarar ──

    [Fact]
    public void Mascarar_AplicaMascaraEm14Digitos()
    {
        Assert.Equal("54.283.***/**26", CnpjHasher.Mascarar("54283546000126"));
    }

    [Theory]
    [InlineData("123")]          // curto
    [InlineData("")]             // vazio
    [InlineData("123456789012345")] // longo
    public void Mascarar_DevolveEntradaIntactaForaDoTamanho(string cnpj)
    {
        Assert.Equal(cnpj, CnpjHasher.Mascarar(cnpj));
    }

    // ── Paridade do hash de CNPJ com o agente Python (vetores compartilhados) ──

    private static DirectoryInfo LocalizarFixtures()
    {
        var dir = new DirectoryInfo(Environment.CurrentDirectory);
        while (dir != null)
        {
            var candidato = Path.Combine(dir.FullName, "Nfse.Agent", "testes", "fixtures");
            if (Directory.Exists(candidato))
                return new DirectoryInfo(candidato);
            dir = dir.Parent;
        }
        throw new DirectoryNotFoundException(
            "Fixtures do agente não encontradas (Nfse.Agent/testes/fixtures)");
    }

    [Fact]
    public void HashCnpj_ReproduzOsVetoresCompartilhados()
    {
        var fixtures = LocalizarFixtures();
        var doc = JsonDocument.Parse(
            File.ReadAllText(Path.Combine(fixtures.FullName, "cnpj_vetores.json")));

        foreach (var vetor in doc.RootElement.GetProperty("vetores").EnumerateArray())
        {
            var cnpj = vetor.GetProperty("cnpj").GetString()!;
            var chave = vetor.GetProperty("chave").GetString()!;
            var esperado = vetor.GetProperty("hash").GetString()!;

            Assert.Equal(esperado, CnpjHasher.Hash(cnpj, chave));
        }
    }
}
