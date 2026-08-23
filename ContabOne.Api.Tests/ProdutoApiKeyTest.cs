using System.Net;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Security;
using ContabOne.Api.Tests.TestSupport;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// A chave de API declara qual ferramenta do hub ela habilita
/// (`nfse_…`, `det_…`). O que esta suíte tranca:
///
/// 1. Cada produto autentica com o próprio prefixo — nada no caminho de
///    autenticação assume NFS-e.
/// 2. O produto declarado pela chave tem que bater com o gravado no agente.
///    O lookup é por (prefixo8, hash-do-segredo) e nenhum dos dois envolve o
///    produto, então sem esse guarda uma chave com o primeiro campo trocado
///    passaria como se fosse de outra ferramenta.
/// 3. Chave existente `nfse_…` continua válida — a coluna Produto nasceu com
///    default 0 (= Nfse) justamente para não invalidar quem já está em campo.
/// </summary>
[Trait("Category", "Banco")]
[Collection("Banco")]
public class ProdutoApiKeyTest : IClassFixture<ApiFactory>
{
    private readonly ApiFactory _factory;
    private readonly HttpClient _client;

    public ProdutoApiKeyTest(ApiFactory factory, PostgresFixture banco)
    {
        _factory = factory;
        _client = factory.CreateClient();
    }

    private AppDbContext NovoDbContext()
        => _factory.Services.CreateScope().ServiceProvider.GetRequiredService<AppDbContext>();

    private async Task<HttpResponseMessage> Handshake(string apiKey)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, "/api/agent/handshake")
        {
            Content = new StringContent(
                JsonSerializer.Serialize(new { versaoAgente = "2.0.0", regrasVersaoLocal = 0 }),
                Encoding.UTF8, "application/json"),
        };
        req.Headers.Add("X-Api-Key", apiKey);
        return await _client.SendAsync(req);
    }

    [Theory]
    [InlineData(Produto.Nfse, "nfse_")]
    [InlineData(Produto.Det, "det_")]
    public async Task Handshake_ChaveDoProprioProduto_Autentica(Produto produto, string prefixoEsperado)
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório {produto}");
        DataHelpers.CriarPlano(db);
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, $"Agente {produto}", produto);

        Assert.StartsWith(prefixoEsperado, chave);

        var resposta = await Handshake(chave);
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
    }

    [Fact]
    public async Task Handshake_ProdutoDaChaveDivergeDoAgente_Devolve401()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Produto Trocado");
        DataHelpers.CriarPlano(db);
        var (_, chaveNfse) = DataHelpers.CriarAgente(db, esc.Id, "Agente NFS-e", Produto.Nfse);

        // Mesmo prefixo8 e mesmo segredo — só o campo do produto trocado. O
        // lookup no banco ENCONTRA o agente (busca por prefixo + hash do
        // segredo); quem recusa é a conferência de produto.
        var partes = chaveNfse.Split('_');
        var chaveForjada = $"det_{partes[1]}_{partes[2]}";
        Assert.Equal(ApiKeyHasher.HashApiKey(chaveNfse), ApiKeyHasher.HashApiKey(chaveForjada));

        var resposta = await Handshake(chaveForjada);
        Assert.Equal(HttpStatusCode.Unauthorized, resposta.StatusCode);
    }

    [Fact]
    public async Task Handshake_PrefixoDeProdutoDesconhecido_Devolve401()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Produto Inexistente");
        DataHelpers.CriarPlano(db);
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente", Produto.Nfse);

        var partes = chave.Split('_');
        var resposta = await Handshake($"folha_{partes[1]}_{partes[2]}");
        Assert.Equal(HttpStatusCode.Unauthorized, resposta.StatusCode);
    }

    /// <summary>
    /// Regressão da compatibilidade: linha de agente gravada como estava antes
    /// da coluna existir (Produto no default 0) tem que continuar autenticando
    /// com a chave `nfse_…` que já está no config.toml do cliente.
    /// </summary>
    [Fact]
    public async Task Handshake_AgenteLegadoComProdutoNoDefault_ContinuaAutenticando()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Legado");
        DataHelpers.CriarPlano(db);

        var (chave, prefixo, hash) = ApiKeyHasher.Gerar(Produto.Nfse);
        db.Agentes.Add(new Agente
        {
            EscritorioId = esc.Id,
            Nome = "Agente Legado",
            ApiKeyHash = hash,
            ApiKeyPrefixo = prefixo,
            // Produto não atribuído de propósito — vale o default do CLR e da
            // coluna, que é exatamente o estado das linhas pré-migration.
        });
        db.SaveChanges();

        var resposta = await Handshake(chave);
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
    }
}
