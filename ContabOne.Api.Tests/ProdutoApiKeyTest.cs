using System.Net;
using System.Text;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Security;
using ContabOne.Api.Tests.TestSupport;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// A chave de API declara qual ferramenta do hub ela habilita
/// (`nfse_…`, `det_…`), e o catálogo de ferramentas é uma TABELA.
///
/// O risco que vem junto de catálogo mutável é o motivo desta suíte existir:
/// se a autenticação consultasse a tabela `Produtos`, uma linha alterada ou
/// removida derrubaria agentes em campo. Ela não consulta — compara o código
/// da chave com o `Produto.Codigo` do próprio agente, que vem no mesmo JOIN.
/// Os testes abaixo trancam exatamente essa propriedade.
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

    // ── O catálogo semeado pela migration ──

    [Fact]
    public void MigrationSemeiaOsProdutosQueOEnumRepresentava()
    {
        using var db = NovoDbContext();

        var codigos = db.Produtos.Select(p => p.Codigo).ToList();
        Assert.Contains("nfse", codigos);
        Assert.Contains("det", codigos);

        // Todo código semeado tem que passar pela mesma regra que o cadastro
        // impõe — senão o seed produziria chave que o parser não valida.
        Assert.All(codigos, c => Assert.True(ProdutoCodigo.Valido(c), $"código inválido no seed: {c}"));
    }

    [Theory]
    [InlineData("nfse")]
    [InlineData("det")]
    public async Task Handshake_ChaveDoProprioProduto_Autentica(string codigoProduto)
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório {codigoProduto}");
        DataHelpers.CriarPlano(db);
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, $"Agente {codigoProduto}", codigoProduto);

        Assert.StartsWith(codigoProduto + "_", chave);
        Assert.Equal(HttpStatusCode.OK, (await Handshake(chave)).StatusCode);
    }

    [Fact]
    public async Task Handshake_CodigoDaChaveDivergeDoAgente_Devolve401()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Produto Trocado");
        DataHelpers.CriarPlano(db);
        var (_, chaveNfse) = DataHelpers.CriarAgente(db, esc.Id, "Agente NFS-e", "nfse");

        // Mesmo prefixo8 e mesmo segredo — só o campo do produto trocado. O
        // lookup ENCONTRA o agente (busca por prefixo + hash do segredo); quem
        // recusa é a conferência contra o produto do próprio agente.
        var partes = chaveNfse.Split('_');
        var chaveForjada = $"det_{partes[1]}_{partes[2]}";
        Assert.Equal(ApiKeyHasher.HashApiKey(chaveNfse), ApiKeyHasher.HashApiKey(chaveForjada));

        Assert.Equal(HttpStatusCode.Unauthorized, (await Handshake(chaveForjada)).StatusCode);
    }

    [Fact]
    public async Task Handshake_CodigoDeProdutoInexistente_Devolve401()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Produto Inexistente");
        DataHelpers.CriarPlano(db);
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente", "nfse");

        var partes = chave.Split('_');
        Assert.Equal(HttpStatusCode.Unauthorized,
            (await Handshake($"folha_{partes[1]}_{partes[2]}")).StatusCode);
    }

    // ── As duas propriedades que protegem quem já está em campo ──

    /// <summary>
    /// Desativar um produto no catálogo é decisão comercial (parar de emitir
    /// chave nova), não revogação. Agente em campo com produto inativo tem que
    /// continuar autenticando — para cortar acesso existe revogar a chave.
    /// </summary>
    [Fact]
    public async Task Handshake_ProdutoDesativadoNoCatalogo_AgenteEmCampoSegueAutenticando()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Produto Desativado");
        DataHelpers.CriarPlano(db);

        var produto = DataHelpers.CriarProduto(db, "descontinuado", "Descontinuado");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente", "descontinuado");

        Assert.Equal(HttpStatusCode.OK, (await Handshake(chave)).StatusCode);

        produto.Ativo = false;
        db.SaveChanges();

        Assert.Equal(HttpStatusCode.OK, (await Handshake(chave)).StatusCode);
    }

    /// <summary>
    /// Um produto novo no catálogo passa a valer sem deploy: ninguém precisa
    /// recompilar para que `<codigo>_…` autentique. É o ponto todo de o
    /// catálogo ser tabela.
    /// </summary>
    [Fact]
    public async Task Handshake_ProdutoCadastradoEmRuntime_JaAutentica()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Produto Novo");
        DataHelpers.CriarPlano(db);

        DataHelpers.CriarProduto(db, "sped", "SPED");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente SPED", "sped");

        Assert.StartsWith("sped_", chave);
        Assert.Equal(HttpStatusCode.OK, (await Handshake(chave)).StatusCode);
    }

    /// <summary>
    /// A FK é Restrict: apagar um produto que tem agente invalidaria as chaves
    /// que estão nos config.toml dos clientes, então o banco tem que recusar.
    ///
    /// A remoção roda num contexto que NÃO carregou os agentes de propósito.
    /// Com eles rastreados, quem barra é o change tracker do EF (lançando
    /// InvalidOperationException já no Remove) e o teste não chegaria a provar
    /// nada sobre o schema. Contexto limpo manda o DELETE ao Postgres e é a
    /// constraint que responde — que é a garantia real, válida também para
    /// quem apagar por SQL direto.
    /// </summary>
    [Fact]
    public void ApagarProdutoComAgenteEmCampo_ERecusadoPeloBanco()
    {
        Guid produtoId;
        using (var db = NovoDbContext())
        {
            var esc = DataHelpers.CriarEscritorio(db, "Escritório FK Restrict");
            DataHelpers.CriarPlano(db);
            produtoId = DataHelpers.CriarProduto(db, "efdreinf", "EFD-Reinf").Id;
            DataHelpers.CriarAgente(db, esc.Id, "Agente EFD", "efdreinf");
        }

        using var limpo = NovoDbContext();
        limpo.Produtos.Remove(limpo.Produtos.Find(produtoId)!);

        var erro = Assert.Throws<DbUpdateException>(() => limpo.SaveChanges());
        Assert.IsType<Npgsql.PostgresException>(erro.InnerException);
    }
}
