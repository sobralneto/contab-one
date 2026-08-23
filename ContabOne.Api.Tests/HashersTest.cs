using System.Text.Json;
using ContabOne.Api.Domain;
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

    [Theory]
    [InlineData("nfse")]
    [InlineData("det")]
    public void Gerar_ProduzChaveNoFormatoEsperado_EHashCorresponde(string codigoProduto)
    {
        var (chave, prefixo, hash) = ApiKeyHasher.Gerar(codigoProduto);

        Assert.Matches($"^{codigoProduto}_[0-9a-f]{{8}}_[0-9a-f]{{32}}$", chave);
        Assert.Equal(8, prefixo.Length);
        Assert.Equal(hash, ApiKeyHasher.HashApiKey(chave));
        Assert.Equal(prefixo, ApiKeyHasher.ExtrairPrefixo(chave));
        Assert.Equal(codigoProduto, ApiKeyHasher.ExtrairCodigoProduto(chave));
    }

    /// <summary>
    /// O formato da chave NAO consulta o catalogo de produtos: catalogo e
    /// dado mutavel e nao pode estar no caminho de autenticacao. Um codigo
    /// inexistente produz chave estruturalmente valida; quem a recusa e o
    /// handler, comparando com o produto do agente encontrado (ver
    /// ProdutoApiKeyTest).
    /// </summary>
    [Fact]
    public void HashApiKey_NaoValidaCodigoContraCatalogo()
    {
        var chave = ApiKeyHasher.Gerar("produtoquenaoexiste").chaveCompleta;

        Assert.Equal("produtoquenaoexiste", ApiKeyHasher.ExtrairCodigoProduto(chave));
        Assert.Null(Record.Exception(() => ApiKeyHasher.HashApiKey(chave)));
    }

    [Theory]
    [InlineData("sem-separador")]
    [InlineData("nfse_abcdefgh")]
    [InlineData("nfse_abcdefgh_segredo_curto")]
    [InlineData("_abcdefgh_0123456789abcdef0123456789abcdef")] // codigo vazio
    public void HashApiKey_RejeitaFormatosInvalidos(string chave)
    {
        Assert.Throws<ArgumentException>(() => ApiKeyHasher.HashApiKey(chave));
    }

    // -- ProdutoCodigo: a regra que o cadastro de produto tem que impor --

    [Theory]
    [InlineData("nfse")]
    [InlineData("det")]
    [InlineData("sped2")]
    public void CodigoDeProduto_AceitaMinusculasEDigitos(string codigo)
        => Assert.True(ProdutoCodigo.Valido(codigo));

    [Theory]
    [InlineData("")]           // vazio
    [InlineData("a")]          // curto demais
    [InlineData("NFSE")]       // caixa alta: a comparacao no handler e ordinal
    [InlineData("contab_one")] // `_` e o separador da chave
    [InlineData("nfs-e")]      // hifen fora do alfabeto permitido
    [InlineData("nfse ")]      // espaco
    public void CodigoDeProduto_RecusaOQueQuebrariaAChave(string codigo)
        => Assert.False(ProdutoCodigo.Valido(codigo));

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
