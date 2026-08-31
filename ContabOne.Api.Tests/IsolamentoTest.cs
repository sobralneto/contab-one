using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Tests.TestSupport;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// Isolamento multi-tenant: os query filters globais precisam impedir que um
/// escritório enxergue dados de outro — em todos os caminhos (agente por
/// X-Api-Key, usuário por JWT, e o parâmetro de query que tenta furar o
/// filtro). A quebra disso seria o pior defeito possível neste produto.
/// </summary>
[Trait("Category", "Banco")]
[Collection("Banco")]
public class IsolamentoTest : IClassFixture<ApiFactory>
{
    private readonly ApiFactory _factory;
    private readonly HttpClient _client;
    private readonly string _sufixo;

    public IsolamentoTest(ApiFactory factory)
    {
        _factory = factory;
        _client = factory.CreateClient();
        _sufixo = Guid.NewGuid().ToString("N")[..8];
    }

    private AppDbContext NovoDbContext()
        => _factory.Services.CreateScope().ServiceProvider.GetRequiredService<AppDbContext>();

    private async Task<(Guid escA, Guid escB, string chaveA)> CriarCenarioDoisEscritorios()
    {
        using var db = NovoDbContext();
        var escA = DataHelpers.CriarEscritorio(db, $"Escritório A {_sufixo}");
        var escB = DataHelpers.CriarEscritorio(db, $"Escritório B {_sufixo}");
        var (_, chaveA) = DataHelpers.CriarAgente(db, escA.Id, $"Agente A {_sufixo}");
        DataHelpers.CriarAgente(db, escB.Id, $"Agente B {_sufixo}");
        return (escA.Id, escB.Id, chaveA);
    }

    private static async Task<HttpResponseMessage> EnviarJson(
        HttpClient client, HttpMethod metodo, string url, string json, string apiKey)
    {
        var req = new HttpRequestMessage(metodo, url)
        {
            Content = new StringContent(json, Encoding.UTF8, "application/json"),
        };
        req.Headers.Add("X-Api-Key", apiKey);
        return await client.SendAsync(req);
    }

    // ── 7.1: agente de A não alcança dados de B em /api/agent ──

    [Fact]
    public async Task AgenteNaoFinalizaExecucaoDeOutroEscritorio()
    {
        var (escA, escB, chaveA) = await CriarCenarioDoisEscritorios();
        using var db = NovoDbContext();
        var (_, chaveB) = DataHelpers.CriarAgente(db, escB, $"Agente B2 {_sufixo}");

        // Agente B abre a execução; agente A tenta finalizá-la.
        var aberta = await EnviarJson(_client, HttpMethod.Post, "/api/agent/execucoes", "{}", chaveB);
        var doc = JsonDocument.Parse(await aberta.Content.ReadAsStringAsync());
        var execucaoId = doc.RootElement.GetProperty("execucaoId").GetString()!;

        var finalizar = await EnviarJson(_client, HttpMethod.Post,
            $"/api/agent/execucoes/{execucaoId}/finalizar", """{"status": 0}""", chaveA);

        Assert.Equal(HttpStatusCode.NotFound, finalizar.StatusCode);

        using var db2 = NovoDbContext();
        var gravada = db2.Execucoes.IgnoreQueryFilters().First(e => e.Id == Guid.Parse(execucaoId));
        Assert.Null(gravada.FinalizadoEm); // B não teve a execução finalizada por A
    }

    [Fact]
    public async Task AgenteUpsertNaoAtualizaClienteDeOutroEscritorio()
    {
        var (escA, escB, chaveA) = await CriarCenarioDoisEscritorios();
        using var db = NovoDbContext();
        var clienteB = DataHelpers.CriarCliente(db, escB, "0001", "Cliente Original de B");

        // Agente de A faz upsert do MESMO código 0001 — deve criar o de A,
        // não atualizar o de B.
        var json = """{"clientes": [{"codigo": "0001", "nome": "Cliente de A", "cnpjMascarado": "00.000.***/**00", "cnpjHash": "ha"}]}""";
        var resposta = await EnviarJson(_client, HttpMethod.Post, "/api/agent/clientes", json, chaveA);
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);

        using var db2 = NovoDbContext();
        // Escopado aos dois escritórios deste teste — o container é
        // compartilhado pela coleção e outros testes também usam código 0001.
        var todos = db2.Clientes.IgnoreQueryFilters()
            .Where(c => (c.EscritorioId == escA || c.EscritorioId == escB) && c.Codigo == "0001")
            .ToList();
        Assert.Equal(2, todos.Count);
        Assert.Contains(todos, c => c.EscritorioId == escA && c.Nome == "Cliente de A");
        var bAinda = db2.Clientes.IgnoreQueryFilters().First(c => c.Id == clienteB.Id);
        Assert.Equal("Cliente Original de B", bAinda.Nome);
    }

    // ── 7.2: usuário JWT de A não vê dados de B ──

    [Fact]
    public async Task UsuarioDeEscritorioNaoVeDadosDeOutro()
    {
        var (escA, escB, _) = await CriarCenarioDoisEscritorios();
        using var db = NovoDbContext();
        DataHelpers.CriarCliente(db, escA, "1001", "Cliente de A");
        DataHelpers.CriarCliente(db, escB, "2001", "Cliente de B");
        db.Alertas.Add(new Alerta { EscritorioId = escA, Tipo = TipoAlerta.ExecucaoFalhou, Severidade = SeveridadeAlerta.Critico, Mensagem = "alerta A" });
        db.Alertas.Add(new Alerta { EscritorioId = escB, Tipo = TipoAlerta.ExecucaoFalhou, Severidade = SeveridadeAlerta.Critico, Mensagem = "alerta B" });
        db.SaveChanges();

        await AuthHelpers.GarantirRoles(_factory.Services);
        var email = $"usuarioA_{_sufixo}@nfse.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "EscritorioUsuario", escA);
        var token = await AuthHelpers.Login(_client, email, "Senha123!");
        _client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

        // clientes: só os de A
        var clientes = await _client.GetAsync("/api/clientes");
        var docClientes = JsonDocument.Parse(await clientes.Content.ReadAsStringAsync());
        var nomes = docClientes.RootElement.GetProperty("dados").EnumerateArray()
            .Select(c => c.GetProperty("nome").GetString()).ToList();
        Assert.DoesNotContain("Cliente de B", nomes);
        Assert.Contains("Cliente de A", nomes);

        // alertas: só os de A
        var alertas = await _client.GetAsync("/api/alertas");
        var docAlertas = JsonDocument.Parse(await alertas.Content.ReadAsStringAsync());
        var mensagens = docAlertas.RootElement.EnumerateArray()
            .Select(a => a.GetProperty("mensagem").GetString()).ToList();
        Assert.DoesNotContain("alerta B", mensagens);
        Assert.Contains("alerta A", mensagens);

        // execuções: só as de A
        var execucoes = await _client.GetAsync("/api/execucoes?pagina=1&tamanho=10");
        Assert.Equal(HttpStatusCode.OK, execucoes.StatusCode);
    }

    // ── 7.3: usuário de escritório não alcança /api/admin ──

    [Fact]
    public async Task UsuarioDeEscritorioNaoAlcancaAdmin()
    {
        var (escA, _, _) = await CriarCenarioDoisEscritorios();
        await AuthHelpers.GarantirRoles(_factory.Services);
        var email = $"usuarioAdmin_{_sufixo}@nfse.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "EscritorioAdmin", escA);
        var token = await AuthHelpers.Login(_client, email, "Senha123!");

        var req = new HttpRequestMessage(HttpMethod.Get, "/api/admin/escritorios");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        var resposta = await _client.SendAsync(req);

        Assert.Equal(HttpStatusCode.Forbidden, resposta.StatusCode);
    }

    // ── 7.4: PlatformAdmin vê todos os escritórios ──

    [Fact]
    public async Task PlatformAdminEnxergaTodosOsEscritorios()
    {
        var (escA, escB, _) = await CriarCenarioDoisEscritorios();
        await AuthHelpers.GarantirRoles(_factory.Services);
        var email = $"platform_{_sufixo}@nfse.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "PlatformAdmin", null);
        var token = await AuthHelpers.Login(_client, email, "Senha123!");

        var req = new HttpRequestMessage(HttpMethod.Get, "/api/admin/escritorios");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        var resposta = await _client.SendAsync(req);
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);

        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        var nomes = doc.RootElement.EnumerateArray()
            .Select(e => e.GetProperty("nome").GetString()).ToList();
        Assert.Contains($"Escritório A {_sufixo}", nomes);
        Assert.Contains($"Escritório B {_sufixo}", nomes);
    }

    // ── 7.5: parâmetro escritorioId de outro escritório não vaza ──

    [Fact]
    public async Task ParametroEscritorioIdDeOutroEscritorioNaoVaza()
    {
        var (escA, escB, _) = await CriarCenarioDoisEscritorios();
        using var db = NovoDbContext();
        DataHelpers.CriarCliente(db, escA, "3001", "Cliente Sigiloso de A");
        DataHelpers.CriarCliente(db, escB, "3002", "Cliente de B");

        await AuthHelpers.GarantirRoles(_factory.Services);
        var email = $"usuarioVaza_{_sufixo}@nfse.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "EscritorioUsuario", escA);
        var token = await AuthHelpers.Login(_client, email, "Senha123!");

        // Usuário de A pede clientes de B pelo parâmetro — o query filter
        // global continua valendo e nada de B aparece.
        var req = new HttpRequestMessage(HttpMethod.Get, $"/api/clientes?escritorioId={escB}");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        var resposta = await _client.SendAsync(req);

        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        var nomes = doc.RootElement.GetProperty("dados").EnumerateArray()
            .Select(c => c.GetProperty("nome").GetString()).ToList();
        Assert.DoesNotContain("Cliente de B", nomes);
    }

    // ── 7.6: métricas não podem referenciar clienteId de outro escritório ──

    [Fact]
    public async Task MetricasNaoPodemReferenciarClienteDeOutroEscritorio()
    {
        var (escA, escB, chaveA) = await CriarCenarioDoisEscritorios();
        using var db = NovoDbContext();
        var clienteB = DataHelpers.CriarCliente(db, escB, "4001", "Cliente de B");

        var aberta = await EnviarJson(_client, HttpMethod.Post, "/api/agent/execucoes", "{}", chaveA);
        var doc = JsonDocument.Parse(await aberta.Content.ReadAsStringAsync());
        var execucaoId = doc.RootElement.GetProperty("execucaoId").GetString()!;

        var json = JsonSerializer.Serialize(new
        {
            metricas = new[]
            {
                new { clienteId = clienteB.Id, tipo = 0, competencia = "2026-07",
                      qtdBaixadas = 1, qtdPuladas = 0, qtdFalhas = 0, duracaoMs = 50 },
            },
        });
        var resposta = await EnviarJson(_client, HttpMethod.Post,
            $"/api/agent/execucoes/{execucaoId}/metricas", json, chaveA);

        using var db2 = NovoDbContext();
        var metricas = db2.ExecucaoMetricas.IgnoreQueryFilters()
            .Where(m => m.ExecucaoId == Guid.Parse(execucaoId)).ToList();

        // Contrato esperado: o agente de A não consegue gravar métrica
        // referenciando cliente de B. Se a API aceitar hoje, este teste falha
        // e documenta um defeito a corrigir (a métrica ficaria órfã de
        // tenancy: execução de A apontando para cliente de B).
        Assert.Empty(metricas);
    }

    // ── 7.7: usuário de papel de escritório sem nenhum vínculo → login recusado ──

    [Fact]
    public async Task UsuarioDeEscritorioSemVinculo_LoginRecusado()
    {
        var (escA, escB, _) = await CriarCenarioDoisEscritorios();
        using var db = NovoDbContext();
        DataHelpers.CriarCliente(db, escA, "9001", "Cliente Sigiloso de A");
        DataHelpers.CriarCliente(db, escB, "9002", "Cliente de B");

        await AuthHelpers.GarantirRoles(_factory.Services);

        // Usuário com papel de escritório criado direto no banco sem nenhum
        // vínculo: o login deve recusá-lo (todo usuário de escritório tem ao
        // menos um vínculo), em vez de emitir um token sem foco.
        var email = $"semEscritorio_{_sufixo}@nfse.local";
        var usuario = new Usuario
        {
            UserName = email.Split('@')[0],
            Nome = "Sem Escritório",
            Email = email,
            Papel = PapelUsuario.EscritorioUsuario,
            Ativo = true,
            EmailConfirmed = true,
        };
        using (var scope = _factory.Services.CreateScope())
        {
            var userManager = scope.ServiceProvider.GetRequiredService<UserManager<Usuario>>();
            await userManager.CreateAsync(usuario, "Senha123!");
            await userManager.AddToRoleAsync(usuario, "EscritorioUsuario");
        }

        var loginResp = await _client.PostAsync("/api/auth/login",
            new StringContent(JsonSerializer.Serialize(new { email, password = "Senha123!" }),
                Encoding.UTF8, "application/json"));
        Assert.Equal(HttpStatusCode.Unauthorized, loginResp.StatusCode);
    }

    // ── 7.8: a segunda camada — o filtro em si, sem passar pelo middleware ──

    /// <summary>
    /// O teste acima cobre a rejeição no middleware. Este cobre a camada de
    /// baixo: mesmo que algum caminho futuro escape do middleware e chegue ao
    /// banco com tenant não resolvido, o query filter não pode devolver nada.
    /// São duas defesas de propósito (design D1/D2) — testar só a de cima
    /// deixaria a de baixo apodrecer sem ninguém perceber.
    /// </summary>
    [Fact]
    public async Task FiltroFailClosed_SemTenantResolvido_NaoDevolveNenhumaLinha()
    {
        var (escA, escB, chaveA) = await CriarCenarioDoisEscritorios();
        using (var db = NovoDbContext())
        {
            DataHelpers.CriarCliente(db, escA, $"9101{_sufixo}", "Cliente A fail-closed");
            DataHelpers.CriarCliente(db, escB, $"9102{_sufixo}", "Cliente B fail-closed");
            db.Alertas.Add(new Alerta
            {
                EscritorioId = escA,
                Tipo = TipoAlerta.ExecucaoFalhou,
                Severidade = SeveridadeAlerta.Critico,
                Mensagem = $"alerta fail-closed {_sufixo}",
            });
            db.SaveChanges();
        }

        // Escopo novo: o TenantContext nasce vazio — é exatamente o estado que
        // antes significava "vê tudo".
        using var semTenant = NovoDbContext();
        Assert.Empty(semTenant.Clientes.ToList());
        Assert.Empty(semTenant.Alertas.ToList());
        Assert.Empty(semTenant.Agentes.ToList());
        Assert.Empty(semTenant.ConfiguracoesEscritorio.ToList());

        // As linhas existem — o que o filtro tirou foi a visibilidade, não o dado.
        using var ignorandoFiltro = NovoDbContext();
        Assert.True(ignorandoFiltro.Clientes.IgnoreQueryFilters()
            .Any(c => c.EscritorioId == escA && c.Codigo == $"9101{_sufixo}"));
    }
}
