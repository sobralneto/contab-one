using System.Net;
using System.Net.Http.Headers;
using Microsoft.Extensions.DependencyInjection;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Tests.TestSupport;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// `GET /api/execucoes` escopado por ferramenta via `produtoCodigo`
/// (`Agente.ProdutoId`) — a tela de Execuções de uma ferramenta não pode
/// misturar execuções da outra. `produtoCodigo` é opcional: sem ele, o
/// comportamento é o de sempre (todas as execuções do escritório), usado
/// pelo resumo da visão geral.
/// </summary>
[Trait("Category", "Banco")]
[Collection("Banco")]
public class ExecucoesPorFerramentaTest : IClassFixture<ApiFactory>
{
    private readonly ApiFactory _factory;
    private readonly HttpClient _client;
    private readonly string _sufixo;

    public ExecucoesPorFerramentaTest(ApiFactory factory)
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
        var email = $"execucoes-{_sufixo}@teste.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "EscritorioUsuario", escritorioId);
        return await AuthHelpers.Login(_client, email, "Senha123!");
    }

    private async Task<HttpResponseMessage> GetComTokenAsync(string url, string token)
    {
        var req = new HttpRequestMessage(HttpMethod.Get, url);
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        return await _client.SendAsync(req);
    }

    private static Guid CriarExecucao(AppDbContext db, Guid escritorioId, Guid agenteId)
    {
        var execucao = new Execucao
        {
            EscritorioId = escritorioId,
            AgenteId = agenteId,
            IniciadoEm = DateTime.UtcNow,
        };
        db.Execucoes.Add(execucao);
        db.SaveChanges();
        return execucao.Id;
    }

    [Fact]
    public async Task ListaPlana_ComProdutoCodigo_SoTrazExecucoesDaquelaFerramenta()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Execuções {_sufixo}");
        var (agenteNfse, _) = DataHelpers.CriarAgente(db, esc.Id, "Agente NFS-e", "nfse");
        var (agenteDet, _) = DataHelpers.CriarAgente(db, esc.Id, "Agente DET", "det");
        var idNfse = CriarExecucao(db, esc.Id, agenteNfse.Id);
        var idDet = CriarExecucao(db, esc.Id, agenteDet.Id);
        var token = await TokenEscritorioAsync(esc.Id);

        var respNfse = await GetComTokenAsync("/api/execucoes?produtoCodigo=nfse", token);
        var docNfse = System.Text.Json.JsonDocument.Parse(await respNfse.Content.ReadAsStringAsync());
        var idsNfse = docNfse.RootElement.GetProperty("dados").EnumerateArray()
            .Select(e => e.GetProperty("id").GetGuid()).ToList();

        Assert.Contains(idNfse, idsNfse);
        Assert.DoesNotContain(idDet, idsNfse);
    }

    [Fact]
    public async Task ListaPlana_SemProdutoCodigo_TrazTodasAsFerramentas()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Execuções Sem Filtro {_sufixo}");
        var (agenteNfse, _) = DataHelpers.CriarAgente(db, esc.Id, "Agente NFS-e", "nfse");
        var (agenteDet, _) = DataHelpers.CriarAgente(db, esc.Id, "Agente DET", "det");
        var idNfse = CriarExecucao(db, esc.Id, agenteNfse.Id);
        var idDet = CriarExecucao(db, esc.Id, agenteDet.Id);
        var token = await TokenEscritorioAsync(esc.Id);

        var resposta = await GetComTokenAsync("/api/execucoes", token);
        var doc = System.Text.Json.JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        var ids = doc.RootElement.GetProperty("dados").EnumerateArray()
            .Select(e => e.GetProperty("id").GetGuid()).ToList();

        Assert.Contains(idNfse, ids);
        Assert.Contains(idDet, ids);
    }

    [Fact]
    public async Task AgrupadoPorCliente_ComProdutoCodigo_SoContaExecucoesDaquelaFerramenta()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Execuções Cliente {_sufixo}");
        var cliente = DataHelpers.CriarCliente(db, esc.Id);
        var (agenteNfse, _) = DataHelpers.CriarAgente(db, esc.Id, "Agente NFS-e", "nfse");
        var (agenteDet, _) = DataHelpers.CriarAgente(db, esc.Id, "Agente DET", "det");

        var execNfse = CriarExecucao(db, esc.Id, agenteNfse.Id);
        var execDet = CriarExecucao(db, esc.Id, agenteDet.Id);
        db.ExecucaoMetricas.Add(new ExecucaoMetrica { ExecucaoId = execNfse, ClienteId = cliente.Id, Tipo = TipoNota.Recebidas, Competencia = "2026-08", QtdBaixadas = 3 });
        db.ExecucaoMetricas.Add(new ExecucaoMetrica { ExecucaoId = execDet, ClienteId = cliente.Id, Tipo = TipoNota.Recebidas, Competencia = "2026-08", QtdBaixadas = 5 });
        db.SaveChanges();

        var token = await TokenEscritorioAsync(esc.Id);
        var resposta = await GetComTokenAsync("/api/execucoes?agruparPor=cliente&produtoCodigo=nfse", token);
        var doc = System.Text.Json.JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        var grupo = doc.RootElement.GetProperty("grupos").EnumerateArray()
            .First(g => g.GetProperty("clienteId").GetGuid() == cliente.Id);

        Assert.Equal(1, grupo.GetProperty("total").GetInt32());
        Assert.Equal(3, grupo.GetProperty("totalBaixadas").GetInt32());
    }

    [Fact]
    public async Task ComFerramentaInexistente_Devolve400()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, $"Escritório Execuções Inexistente {_sufixo}");
        var token = await TokenEscritorioAsync(esc.Id);

        var resposta = await GetComTokenAsync("/api/execucoes?produtoCodigo=inexistente", token);

        Assert.Equal(HttpStatusCode.BadRequest, resposta.StatusCode);
    }
}
