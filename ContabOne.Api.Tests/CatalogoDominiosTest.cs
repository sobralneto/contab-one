using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using ContabOne.Api.Infra;
using ContabOne.Api.Tests.TestSupport;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// Catálogo de ferramentas com domínio e páginas — a base de dado que o
/// frontend usa para agrupar o menu e montar o hub. O que se tranca aqui:
/// escritório só vê o que contratou, admin vê o catálogo inteiro marcado com
/// o que foi contratado, e o cadastro recusa domínio ou página inexistente.
/// </summary>
[Trait("Category", "Banco")]
[Collection("Banco")]
public class CatalogoDominiosTest : IClassFixture<ApiFactory>
{
    private readonly ApiFactory _factory;
    private readonly HttpClient _client;
    private readonly string _sufixo;

    public CatalogoDominiosTest(ApiFactory factory)
    {
        _factory = factory;
        _client = factory.CreateClient();
        _sufixo = Guid.NewGuid().ToString("N")[..8];
    }

    private AppDbContext NovoDbContext()
        => _factory.Services.CreateScope().ServiceProvider.GetRequiredService<AppDbContext>();

    private async Task<string> TokenAdminAsync()
    {
        await AuthHelpers.GarantirRoles(_factory.Services);
        var email = $"admin-catalogo-{_sufixo}@teste.local";
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

    // ── O catálogo da sessão de escritório ──

    /// <summary>
    /// O catálogo do escritório é o ativo INTEIRO, não só o contratado — é o
    /// que permite o hub mostrar a ferramenta não contratada como card
    /// informativo (navegacao-por-dominio). O seletor de chave de agente é
    /// quem filtra por `contratado` no frontend, não o endpoint.
    /// </summary>
    [Fact]
    public async Task Escritorio_VeCatalogoInteiroComFlagContratado()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Um Produto {_sufixo}");
        var nfse = DataHelpers.ObterProduto(db, "nfse");
        DataHelpers.HabilitarProduto(db, esc.Id, nfse.Id);

        await AuthHelpers.GarantirRoles(_factory.Services);
        var email = $"usuario-catalogo-{_sufixo}@teste.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "EscritorioUsuario", esc.Id);
        var token = await AuthHelpers.Login(_client, email, "Senha123!");

        var req = new HttpRequestMessage(HttpMethod.Get, "/api/produtos");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        var resposta = await _client.SendAsync(req);

        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        var itens = doc.RootElement.EnumerateArray().ToList();

        // Catálogo ativo inteiro (nfse e det), não só o contratado.
        Assert.Contains(itens, p => p.GetProperty("codigo").GetString() == "nfse");
        Assert.Contains(itens, p => p.GetProperty("codigo").GetString() == "det");

        var itemNfse = itens.First(p => p.GetProperty("codigo").GetString() == "nfse");
        var itemDet = itens.First(p => p.GetProperty("codigo").GetString() == "det");
        Assert.True(itemNfse.GetProperty("contratado").GetBoolean());
        Assert.False(itemDet.GetProperty("contratado").GetBoolean());
        Assert.Equal("fiscal", itemNfse.GetProperty("dominio").GetProperty("codigo").GetString());
    }

    // ── O catálogo do admin ──

    [Fact]
    public async Task Admin_ComEscritorioEmFoco_VeCatalogoInteiroComFlagContratado()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Admin Foco {_sufixo}");
        var nfse = DataHelpers.ObterProduto(db, "nfse");
        DataHelpers.HabilitarProduto(db, esc.Id, nfse.Id);

        var req = new HttpRequestMessage(HttpMethod.Get, $"/api/produtos?escritorioId={esc.Id}");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", await TokenAdminAsync());
        var resposta = await _client.SendAsync(req);

        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        var itens = doc.RootElement.EnumerateArray().ToList();

        // Catálogo ativo inteiro (nfse e det), não só o contratado.
        Assert.Contains(itens, p => p.GetProperty("codigo").GetString() == "nfse");
        Assert.Contains(itens, p => p.GetProperty("codigo").GetString() == "det");

        var itemNfse = itens.First(p => p.GetProperty("codigo").GetString() == "nfse");
        var itemDet = itens.First(p => p.GetProperty("codigo").GetString() == "det");
        Assert.True(itemNfse.GetProperty("contratado").GetBoolean());
        Assert.False(itemDet.GetProperty("contratado").GetBoolean());
    }

    [Fact]
    public async Task Admin_SemEscritorioEmFoco_VeCatalogoTodoComoNaoContratado()
    {
        var req = new HttpRequestMessage(HttpMethod.Get, "/api/produtos");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", await TokenAdminAsync());
        var resposta = await _client.SendAsync(req);

        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        var itens = doc.RootElement.EnumerateArray().ToList();

        Assert.NotEmpty(itens);
        Assert.All(itens, p => Assert.False(p.GetProperty("contratado").GetBoolean()));
    }

    /// <summary>
    /// O escopo NUNCA vem da query string para usuário de escritório — o
    /// parâmetro escritorioId só é honrado para PlatformAdmin (§5, IDOR).
    /// </summary>
    [Fact]
    public async Task Escritorio_NaoConsegueForcarEscopoPelaQueryString()
    {
        using var db = NovoDbContext();
        var escA = DataHelpers.CriarEscritorio(db, $"Escritório A Catalogo {_sufixo}");
        var escB = DataHelpers.CriarEscritorio(db, $"Escritório B Catalogo {_sufixo}");
        DataHelpers.HabilitarProduto(db, escB.Id, DataHelpers.ObterProduto(db, "det").Id);

        await AuthHelpers.GarantirRoles(_factory.Services);
        var email = $"usuario-idor-{_sufixo}@teste.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "EscritorioUsuario", escA.Id);
        var token = await AuthHelpers.Login(_client, email, "Senha123!");

        var req = new HttpRequestMessage(HttpMethod.Get, $"/api/produtos?escritorioId={escB.Id}");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        var resposta = await _client.SendAsync(req);

        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        // O catálogo ativo inteiro ainda aparece (é público, não é dado de
        // tenant), mas o DET que B contratou NÃO aparece como contratado
        // para a sessão de A — o parâmetro na query string não fura o escopo.
        var itemDet = doc.RootElement.EnumerateArray()
            .First(p => p.GetProperty("codigo").GetString() == "det");
        Assert.False(itemDet.GetProperty("contratado").GetBoolean());
    }

    // ── Cadastro: domínio e página ──

    [Fact]
    public async Task CriarProduto_ComDominioInexistente_Devolve400ComMotivo()
    {
        var resposta = await PostComoAdminAsync("/api/admin/produtos", new
        {
            codigo = $"prod{_sufixo[..6]}",
            nome = "Produto Teste",
            dominioCodigo = "inexistente",
        });

        Assert.Equal(HttpStatusCode.BadRequest, resposta.StatusCode);
        var corpo = await resposta.Content.ReadAsStringAsync();
        Assert.Contains("dominioCodigo", corpo, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task CriarProduto_ComPaginaDesconhecida_Devolve400ComMotivo()
    {
        var resposta = await PostComoAdminAsync("/api/admin/produtos", new
        {
            codigo = $"prod{_sufixo[..6]}",
            nome = "Produto Teste",
            dominioCodigo = "fiscal",
            paginas = new[] { "pagina-que-nao-existe" },
        });

        Assert.Equal(HttpStatusCode.BadRequest, resposta.StatusCode);
        var corpo = await resposta.Content.ReadAsStringAsync();
        Assert.Contains("desconhecida", corpo, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task CriarProduto_ComDominioEPaginasValidos_ECriado()
    {
        var codigo = $"prod{_sufixo[..6]}";
        var resposta = await PostComoAdminAsync("/api/admin/produtos", new
        {
            codigo,
            nome = "Produto Válido",
            dominioCodigo = "contabil",
            paginas = new[] { "visao-geral", "execucoes" },
        });

        Assert.Equal(HttpStatusCode.Created, resposta.StatusCode);

        using var db = NovoDbContext();
        var produto = db.Produtos.First(p => p.Codigo == codigo);
        Assert.Equal("contabil", produto.DominioCodigo);
        Assert.Equal(["execucoes", "visao-geral"], produto.Paginas.Order());
    }

    [Fact]
    public async Task ListarDominios_DevolveOsTresSeedados()
    {
        var req = new HttpRequestMessage(HttpMethod.Get, "/api/admin/dominios");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", await TokenAdminAsync());
        var resposta = await _client.SendAsync(req);

        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        var codigos = doc.RootElement.EnumerateArray()
            .Select(d => d.GetProperty("codigo").GetString()).ToList();

        Assert.Equal(["fiscal", "dp", "contabil"], codigos);
    }
}
