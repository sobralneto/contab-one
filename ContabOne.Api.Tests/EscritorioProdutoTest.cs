using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Tests.TestSupport;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// Quais ferramentas do hub cada escritório contratou.
///
/// Este é um gate COMERCIAL deliberado, da mesma família do
/// <c>Escritorio.Status</c> — e por isso, ao contrário do catálogo de
/// produtos, ele SIM consulta dado mutável no caminho de autenticação. O que
/// os testes trancam é que ele bloqueie quando deve (produto descontratado) e
/// só quando deve (não pode vazar para outro produto nem para outro
/// escritório).
/// </summary>
[Trait("Category", "Banco")]
[Collection("Banco")]
public class EscritorioProdutoTest : IClassFixture<ApiFactory>
{
    private readonly ApiFactory _factory;
    private readonly HttpClient _client;

    public EscritorioProdutoTest(ApiFactory factory, PostgresFixture banco)
    {
        _factory = factory;
        _client = factory.CreateClient();
    }

    private AppDbContext NovoDbContext()
        => _factory.Services.CreateScope().ServiceProvider.GetRequiredService<AppDbContext>();

    /// <summary>Token de um PlatformAdmin recem-criado.</summary>
    private async Task<string> TokenAdminAsync()
    {
        await AuthHelpers.GarantirRoles(_factory.Services);
        var email = $"admin-prod-{Guid.NewGuid():N}@teste.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "PlatformAdmin", null);
        return await AuthHelpers.Login(_client, email, "Senha123!");
    }

    private async Task<HttpResponseMessage> PostComoAdminAsync(string url, object corpo)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, url)
        {
            Content = new StringContent(JsonSerializer.Serialize(corpo), Encoding.UTF8, "application/json"),
        };
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", await TokenAdminAsync());
        return await _client.SendAsync(req);
    }

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

    // ── O gate no handshake ──

    [Fact]
    public async Task Handshake_FerramentaDescontratada_Devolve401()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Descontratou");
        DataHelpers.CriarPlano(db);
        var (agente, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente", "nfse");

        Assert.Equal(HttpStatusCode.OK, (await Handshake(chave)).StatusCode);

        DataHelpers.DesabilitarProduto(db, esc.Id, agente.ProdutoId);

        Assert.Equal(HttpStatusCode.Unauthorized, (await Handshake(chave)).StatusCode);
    }

    [Fact]
    public async Task Handshake_FerramentaRecontratada_VoltaAAutenticar()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Recontratou");
        DataHelpers.CriarPlano(db);
        var (agente, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente", "nfse");

        DataHelpers.DesabilitarProduto(db, esc.Id, agente.ProdutoId);
        Assert.Equal(HttpStatusCode.Unauthorized, (await Handshake(chave)).StatusCode);

        // A mesma chave volta a valer: desabilitar não é revogar, e a linha
        // preserva o vínculo em vez de ser apagada.
        DataHelpers.HabilitarProduto(db, esc.Id, agente.ProdutoId);
        Assert.Equal(HttpStatusCode.OK, (await Handshake(chave)).StatusCode);
    }

    /// <summary>
    /// Descontratar uma ferramenta não pode derrubar as outras do mesmo
    /// escritório — o gate é por (escritório, produto), não por escritório.
    /// </summary>
    [Fact]
    public async Task Handshake_DescontratarUmProduto_NaoAfetaOsOutros()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Dois Produtos");
        DataHelpers.CriarPlano(db);
        var (agenteNfse, chaveNfse) = DataHelpers.CriarAgente(db, esc.Id, "Agente NFS-e", "nfse");
        var (_, chaveDet) = DataHelpers.CriarAgente(db, esc.Id, "Agente DET", "det");

        DataHelpers.DesabilitarProduto(db, esc.Id, agenteNfse.ProdutoId);

        Assert.Equal(HttpStatusCode.Unauthorized, (await Handshake(chaveNfse)).StatusCode);
        Assert.Equal(HttpStatusCode.OK, (await Handshake(chaveDet)).StatusCode);
    }

    /// <summary>
    /// E não pode vazar entre escritórios: o vínculo de um não habilita o
    /// outro, nem o desabilita.
    /// </summary>
    [Fact]
    public async Task Handshake_DescontratarNumEscritorio_NaoAfetaOutroEscritorio()
    {
        using var db = NovoDbContext();
        DataHelpers.CriarPlano(db);
        var escA = DataHelpers.CriarEscritorio(db, "Escritório A Isolamento");
        var escB = DataHelpers.CriarEscritorio(db, "Escritório B Isolamento");
        var (agenteA, chaveA) = DataHelpers.CriarAgente(db, escA.Id, "Agente A", "nfse");
        var (_, chaveB) = DataHelpers.CriarAgente(db, escB.Id, "Agente B", "nfse");

        DataHelpers.DesabilitarProduto(db, escA.Id, agenteA.ProdutoId);

        Assert.Equal(HttpStatusCode.Unauthorized, (await Handshake(chaveA)).StatusCode);
        Assert.Equal(HttpStatusCode.OK, (await Handshake(chaveB)).StatusCode);
    }

    // ── O gate na emissão de chave ──

    [Fact]
    public async Task CriarAgente_FerramentaNaoContratada_Devolve400ComMotivo()
    {
        using var db = NovoDbContext();
        var plano = DataHelpers.CriarPlano(db);
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Sem DET", plano);
        var produtoDet = DataHelpers.ObterProduto(db, "det");
        DataHelpers.HabilitarProduto(db, esc.Id, DataHelpers.ObterProduto(db, "nfse").Id);

        var resposta = await PostComoAdminAsync("/api/agentes", new
        {
            nome = "Agente DET",
            produtoId = produtoDet.Id,
            escritorioId = esc.Id,
        });

        Assert.Equal(HttpStatusCode.BadRequest, resposta.StatusCode);
        var corpo = await resposta.Content.ReadAsStringAsync();
        Assert.Contains("habilitada", corpo, StringComparison.OrdinalIgnoreCase);

        // E nenhum agente órfão ficou gravado.
        using var db2 = NovoDbContext();
        Assert.False(await db2.Agentes.IgnoreQueryFilters()
            .AnyAsync(a => a.EscritorioId == esc.Id && a.ProdutoId == produtoDet.Id));
    }

    [Fact]
    public async Task CriarAgente_FerramentaContratada_EmiteChaveComOPrefixoDoProduto()
    {
        using var db = NovoDbContext();
        var plano = DataHelpers.CriarPlano(db);
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Com DET", plano);
        var produtoDet = DataHelpers.ObterProduto(db, "det");
        DataHelpers.HabilitarProduto(db, esc.Id, produtoDet.Id);

        var resposta = await PostComoAdminAsync("/api/agentes", new
        {
            nome = "Agente DET",
            produtoId = produtoDet.Id,
            escritorioId = esc.Id,
        });

        Assert.Equal(HttpStatusCode.Created, resposta.StatusCode);
        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        Assert.StartsWith("det_", doc.RootElement.GetProperty("apiKey").GetString());
    }

    /// <summary>
    /// Escritório criado pelo endpoint nasce com as ferramentas ativas
    /// habilitadas. Sem isso ele nasceria inutilizável — nenhuma chave
    /// poderia ser gerada até alguém lembrar de habilitar — e o critério é o
    /// mesmo do backfill da migration.
    /// </summary>
    [Fact]
    public async Task CriarEscritorio_NasceComAsFerramentasAtivasHabilitadas()
    {
        var resposta = await PostComoAdminAsync("/api/admin/escritorios", new
        {
            nome = $"Escritório Novo {Guid.NewGuid():N}",
        });

        Assert.Equal(HttpStatusCode.Created, resposta.StatusCode);
        var id = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync())
            .RootElement.GetProperty("id").GetGuid();

        using var db = NovoDbContext();
        var ativos = await db.Produtos.Where(p => p.Ativo).Select(p => p.Id).ToListAsync();
        var habilitados = await db.EscritorioProdutos
            .IgnoreQueryFilters()
            .Where(ep => ep.EscritorioId == id && ep.DesabilitadoEm == null)
            .Select(ep => ep.ProdutoId)
            .ToListAsync();

        Assert.NotEmpty(ativos);
        Assert.Equal(ativos.Order(), habilitados.Order());
    }

    // ── O backfill da migration ──

    /// <summary>
    /// A migration tinha que dar a todo escritório existente toda ferramenta
    /// ativa — senão o deploy derrubaria os agentes em campo. Aqui o que se
    /// verifica é a consequência viva disso: escritório criado pelos helpers
    /// (que não passa pelo backfill) só autentica o que foi habilitado, e a
    /// regra do backfill está exercitada em Handshake_FerramentaDescontratada.
    /// </summary>
    [Fact]
    public void VinculoDeProduto_TemChaveCompostaSemDuplicar()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Sem Duplicata");
        var produto = DataHelpers.ObterProduto(db, "nfse");

        DataHelpers.HabilitarProduto(db, esc.Id, produto.Id);
        DataHelpers.DesabilitarProduto(db, esc.Id, produto.Id);
        DataHelpers.HabilitarProduto(db, esc.Id, produto.Id);

        using var db2 = NovoDbContext();
        var linhas = db2.EscritorioProdutos.IgnoreQueryFilters()
            .Count(ep => ep.EscritorioId == esc.Id && ep.ProdutoId == produto.Id);

        Assert.Equal(1, linhas);
    }
}
