using System.Net;
using ContabOne.Api.Tests.TestSupport;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// Fumaça da infraestrutura de testes com banco: o host de teste sobe de
/// verdade (WebApplicationFactory + Program parcial), as migrations rodam no
/// container efêmero no startup — incluindo o seed da RegraColeta v1 — e o
/// /health responde.
/// </summary>
[Trait("Category", "Banco")]
[Collection("Banco")]
public class FumacaTest : IClassFixture<ApiFactory>
{
    private readonly ApiFactory _factory;
    private readonly PostgresFixture _banco;

    public FumacaTest(ApiFactory factory, PostgresFixture banco)
    {
        _factory = factory;
        _banco = banco;
    }

    [Fact]
    public void MigrationsRodaramNoContainer_ComSeedDaRegraV1()
    {
        // O seed de corrigir-integracao-tres-camadas: a v1 nasce ativa, com o
        // conteúdo do bundle de fábrica. Se as migrations não rodassem no
        // container, a tabela nem existiria.
        Assert.Equal(1, _banco.Contar("RegraColetas"));

        var (versao, ativa) = _banco.LerRegraV1();
        Assert.Equal(1, versao);
        Assert.True(ativa);
    }

    [Fact]
    public async Task Health_Responde200()
    {
        var client = _factory.CreateClient();
        var resposta = await client.GetAsync("/health");
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
    }
}
