using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using ContabOne.Api.Infra;
using ContabOne.Api.Security;
using ContabOne.Api.Tests.TestSupport;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// Configuração é por (escritório, ferramenta), não só por escritório —
/// período de busca, tipos de nota e afins são próprios de cada ferramenta.
/// O que se tranca aqui: salvar a configuração de uma ferramenta não afeta a
/// outra, e o handshake do agente só recebe a configuração da SUA própria
/// ferramenta.
/// </summary>
[Trait("Category", "Banco")]
[Collection("Banco")]
public class ConfiguracaoPorFerramentaTest : IClassFixture<ApiFactory>
{
    private readonly ApiFactory _factory;
    private readonly HttpClient _client;
    private readonly string _sufixo;

    public ConfiguracaoPorFerramentaTest(ApiFactory factory)
    {
        _factory = factory;
        _client = factory.CreateClient();
        _sufixo = Guid.NewGuid().ToString("N")[..8];
    }

    private AppDbContext NovoDbContext()
        => _factory.Services.CreateScope().ServiceProvider.GetRequiredService<AppDbContext>();

    private async Task<string> TokenEscritorioAsync(Guid escritorioId)
    {
        await AuthHelpers.GarantirRoles(_factory.Services);
        var email = $"config-{_sufixo}@teste.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "EscritorioAdmin", escritorioId);
        return await AuthHelpers.Login(_client, email, "Senha123!");
    }

    private static HttpRequestMessage ComToken(HttpMethod metodo, string url, string token, object? corpo = null)
    {
        var req = new HttpRequestMessage(metodo, url);
        if (corpo != null)
            req.Content = new StringContent(JsonSerializer.Serialize(corpo), Encoding.UTF8, "application/json");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        return req;
    }

    [Fact]
    public async Task SalvarConfiguracaoDoNfse_NaoAfetaAConfiguracaoDoDet()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Config {_sufixo}");
        var token = await TokenEscritorioAsync(esc.Id);

        var salvarNfse = await _client.SendAsync(ComToken(HttpMethod.Put,
            "/api/configuracao?produtoCodigo=nfse", token,
            new { dias_busca_padrao = "10" }));
        Assert.Equal(HttpStatusCode.OK, salvarNfse.StatusCode);

        var salvarDet = await _client.SendAsync(ComToken(HttpMethod.Put,
            "/api/configuracao?produtoCodigo=det", token,
            new { dias_busca_padrao = "45" }));
        Assert.Equal(HttpStatusCode.OK, salvarDet.StatusCode);

        var respNfse = await _client.SendAsync(ComToken(HttpMethod.Get, "/api/configuracao?produtoCodigo=nfse", token));
        var respDet = await _client.SendAsync(ComToken(HttpMethod.Get, "/api/configuracao?produtoCodigo=det", token));

        var docNfse = JsonDocument.Parse(await respNfse.Content.ReadAsStringAsync());
        var docDet = JsonDocument.Parse(await respDet.Content.ReadAsStringAsync());

        Assert.Equal("10", docNfse.RootElement.GetProperty("valores").GetProperty("dias_busca_padrao").GetString());
        Assert.Equal("45", docDet.RootElement.GetProperty("valores").GetProperty("dias_busca_padrao").GetString());
    }

    [Fact]
    public async Task Obter_ComFerramentaInexistente_Devolve400()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Config Inexistente {_sufixo}");
        var token = await TokenEscritorioAsync(esc.Id);

        var resposta = await _client.SendAsync(ComToken(HttpMethod.Get, "/api/configuracao?produtoCodigo=inexistente", token));

        Assert.Equal(HttpStatusCode.BadRequest, resposta.StatusCode);
    }

    [Fact]
    public async Task Obter_SemProdutoCodigo_Devolve400()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Config Sem Produto {_sufixo}");
        var token = await TokenEscritorioAsync(esc.Id);

        var resposta = await _client.SendAsync(ComToken(HttpMethod.Get, "/api/configuracao", token));

        Assert.Equal(HttpStatusCode.BadRequest, resposta.StatusCode);
    }

    [Fact]
    public async Task Handshake_SoRecebeAConfiguracaoDaPropriaFerramenta()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Handshake Config {_sufixo}");
        DataHelpers.CriarPlano(db);
        var (_, chaveNfse) = DataHelpers.CriarAgente(db, esc.Id, "Agente NFS-e", "nfse");
        var (_, chaveDet) = DataHelpers.CriarAgente(db, esc.Id, "Agente DET", "det");
        var token = await TokenEscritorioAsync(esc.Id);

        await _client.SendAsync(ComToken(HttpMethod.Put, "/api/configuracao?produtoCodigo=nfse", token,
            new { dias_busca_padrao = "10" }));
        await _client.SendAsync(ComToken(HttpMethod.Put, "/api/configuracao?produtoCodigo=det", token,
            new { dias_busca_padrao = "45" }));

        async Task<string> HandshakeAsync(string chave)
        {
            var req = new HttpRequestMessage(HttpMethod.Post, "/api/agent/handshake")
            {
                Content = new StringContent(
                    JsonSerializer.Serialize(new { versaoAgente = "2.0.0", regrasVersaoLocal = 0 }),
                    Encoding.UTF8, "application/json"),
            };
            req.Headers.Add("X-Api-Key", chave);
            var resp = await _client.SendAsync(req);
            Assert.Equal(HttpStatusCode.OK, resp.StatusCode);
            var doc = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
            return doc.RootElement.GetProperty("configuracaoCifrada").GetString()!;
        }

        var cifradaNfse = await HandshakeAsync(chaveNfse);
        var cifradaDet = await HandshakeAsync(chaveDet);

        var configNfse = ConfiguracaoCipher.Decifrar(chaveNfse, cifradaNfse);
        var configDet = ConfiguracaoCipher.Decifrar(chaveDet, cifradaDet);

        Assert.Equal("10", configNfse["dias_busca_padrao"]);
        Assert.Equal("45", configDet["dias_busca_padrao"]);
    }
}
