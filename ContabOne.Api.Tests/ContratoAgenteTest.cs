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
/// Contrato dos endpoints do agente (/api/agent/*) contra o host real e o
/// Postgres efêmero. O que importa aqui é o que o consumidor (agente Python,
/// Nfse.Agent/testes/_fake_api.py) espera: campos em camelCase, enums como
/// inteiro, mapa codigo → id no upsert de clientes. Divergir disso
/// silenciosamente é o defeito que esta suíte existe para pegar.
/// </summary>
[Trait("Category", "Banco")]
[Collection("Banco")]
public class ContratoAgenteTest : IClassFixture<ApiFactory>
{
    private readonly ApiFactory _factory;
    private readonly PostgresFixture _banco;
    private readonly HttpClient _client;

    public ContratoAgenteTest(ApiFactory factory, PostgresFixture banco)
    {
        _factory = factory;
        _banco = banco;
        _client = factory.CreateClient();
    }

    private AppDbContext NovoDbContext()
        => _factory.Services.CreateScope().ServiceProvider.GetRequiredService<AppDbContext>();

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

    private static async Task<HttpResponseMessage> Handshake(
        HttpClient client, string apiKey, string versaoAgente = "2.0.0", int regrasVersaoLocal = 0)
        => await EnviarJson(client, HttpMethod.Post, "/api/agent/handshake",
            JsonSerializer.Serialize(new { versaoAgente, regrasVersaoLocal }), apiKey);

    // ── 6.1: handshake com chave válida ──

    [Fact]
    public async Task Handshake_ChaveValida_DevolveContratoCompletoEmCamelCase()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Handshake");
        DataHelpers.CriarPlano(db);
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Handshake");

        var resposta = await Handshake(_client, chave);
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);

        var corpo = await resposta.Content.ReadAsStringAsync();
        var doc = JsonDocument.Parse(corpo);

        // Todos os campos do contrato presentes e em camelCase (o agente
        // Python lê exatamente estes nomes — ver Nfse.Agent/testes/_fake_api.py).
        foreach (var campo in new[] { "escritorio", "status", "podeExecutar",
                                      "plano", "regrasVersaoAtual", "agenteVersaoMinima",
                                      "hmacCnpjKey", "configuracaoCifrada" })
        {
            Assert.True(doc.RootElement.TryGetProperty(campo, out _),
                $"campo '{campo}' ausente no handshake");
            Assert.False(corpo.Contains(char.ToUpper(campo[0]) + campo[1..], StringComparison.Ordinal),
                $"campo '{campo}' deveria estar em camelCase");
        }

        Assert.Equal("Ativo", doc.RootElement.GetProperty("status").GetString());
        Assert.True(doc.RootElement.GetProperty("podeExecutar").GetBoolean());
        Assert.False(string.IsNullOrEmpty(doc.RootElement.GetProperty("hmacCnpjKey").GetString()));
        Assert.Equal(1, doc.RootElement.GetProperty("regrasVersaoAtual").GetInt32()); // seed da v1

        // O bloco de configuração é decifrável com a chave derivada da API
        // key usada neste handshake (ConfiguracaoCipher, change
        // agente-config-minima-cifrada) — sem configuração salva, decifra
        // para um dicionário vazio.
        var configuracaoCifrada = doc.RootElement.GetProperty("configuracaoCifrada").GetString();
        var configuracao = ContabOne.Api.Security.ConfiguracaoCipher.Decifrar(chave, configuracaoCifrada!);
        Assert.Empty(configuracao);
    }

    // ── 6.2: 401 nos três casos ──

    [Fact]
    public async Task Handshake_ChaveInexistente_Devolve401()
    {
        // Formato válido, chave que não existe — o agente trata 401 como
        // bloqueio definitivo, nunca como indisponibilidade.
        var resposta = await Handshake(_client, "nfse_01234567_" + new string('a', 32));
        Assert.Equal(HttpStatusCode.Unauthorized, resposta.StatusCode);
    }

    [Fact]
    public async Task Handshake_AgenteRevogado_Devolve401()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Revogado");
        var (agente, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Revogado");
        agente.RevogadoEm = DateTime.UtcNow;
        db.SaveChanges();

        var resposta = await Handshake(_client, chave);
        Assert.Equal(HttpStatusCode.Unauthorized, resposta.StatusCode);
    }

    [Fact]
    public async Task Handshake_EscritorioNaoAtivo_Devolve401()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Suspenso");
        esc.Status = StatusEscritorio.Suspenso;
        db.SaveChanges();
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Suspenso");

        var resposta = await Handshake(_client, chave);
        Assert.Equal(HttpStatusCode.Unauthorized, resposta.StatusCode);
    }

    // ── 6.3: handshake atualiza versão e último contato ──

    [Fact]
    public async Task Handshake_AtualizaVersaoAgenteEUltimoContato()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Contato");
        var (agente, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Contato");
        var antes = agente.UltimoContatoEm;

        await Handshake(_client, chave, versaoAgente: "9.9.9");

        using var db2 = NovoDbContext();
        var atualizado = db2.Agentes.IgnoreQueryFilters().First(a => a.Id == agente.Id);
        Assert.Equal("9.9.9", atualizado.VersaoAgente);
        Assert.NotNull(atualizado.UltimoContatoEm);
        Assert.True(antes == null || atualizado.UltimoContatoEm >= antes);
    }

    // ── 6.4: upsert devolve o mapa codigo → id ──

    [Fact]
    public async Task UpsertClientes_DevolveMapaCodigoParaId()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Upsert");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Upsert");

        var json = """{"clientes": [{"codigo": "0001", "nome": "Cliente Um", "cnpjMascarado": "00.000.***/**00", "cnpjHash": "h1", "certificadoValidade": "2027-12-31", "certificadoNomeArquivo": "0001.pfx"}, {"codigo": "0002", "nome": "Cliente Dois", "cnpjMascarado": "00.000.***/**00", "cnpjHash": "h2"}]}""";
        var resposta = await EnviarJson(_client, HttpMethod.Post, "/api/agent/clientes", json, chave);
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);

        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        var mapa = doc.RootElement.GetProperty("clientes").EnumerateArray()
            .ToDictionary(c => c.GetProperty("codigo").GetString()!, c => c.GetProperty("id").GetString()!);
        Assert.Equal(2, mapa.Count);
        Assert.Equal(2, doc.RootElement.GetProperty("novos").GetInt32());

        // Os ids correspondem às linhas gravadas no banco
        using var db2 = NovoDbContext();
        var gravados = db2.Clientes.IgnoreQueryFilters().Where(c => c.EscritorioId == esc.Id).ToList();
        Assert.Equal(2, gravados.Count);
        Assert.All(gravados, c => Assert.Equal(c.Id.ToString(), mapa[c.Codigo]));
    }

    // ── 6.5: upsert atualiza pelo par escritório + código ──

    [Fact]
    public async Task UpsertClientes_AtualizaExistenteEmVezDeDuplicar()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Upsert2");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Upsert2");

        var cliente = """{"clientes": [{"codigo": "0001", "nome": "Nome Antigo", "cnpjMascarado": "00.000.***/**00", "cnpjHash": "h1"}]}""";
        await EnviarJson(_client, HttpMethod.Post, "/api/agent/clientes", cliente, chave);

        var renomeado = """{"clientes": [{"codigo": "0001", "nome": "Nome Novo", "cnpjMascarado": "00.000.***/**00", "cnpjHash": "h1-novo"}]}""";
        await EnviarJson(_client, HttpMethod.Post, "/api/agent/clientes", renomeado, chave);

        using var db2 = NovoDbContext();
        var linhas = db2.Clientes.IgnoreQueryFilters().Where(c => c.EscritorioId == esc.Id && c.Codigo == "0001").ToList();
        Assert.Single(linhas);
        Assert.Equal("Nome Novo", linhas[0].Nome);
        Assert.Equal("h1-novo", linhas[0].CnpjHash);
    }

    // ── 6.6: respeita MaxClientes do plano ──

    [Fact]
    public async Task UpsertClientes_RespeitaMaxClientesDoPlano()
    {
        using var db = NovoDbContext();
        var plano = DataHelpers.CriarPlano(db, "Plano Pequeno", maxClientes: 2);
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Limitado", plano);
        DataHelpers.CriarCliente(db, esc.Id, "0001");
        DataHelpers.CriarCliente(db, esc.Id, "0002");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Limitado");

        // 0001 já existe (atualiza), 0003 é novo mas estoura o limite (ignorado)
        var json = """{"clientes": [{"codigo": "0001", "nome": "Atualizado", "cnpjMascarado": "00.000.***/**00", "cnpjHash": "hx"}, {"codigo": "0003", "nome": "Novo Demais", "cnpjMascarado": "00.000.***/**00", "cnpjHash": "h3"}]}""";
        var resposta = await EnviarJson(_client, HttpMethod.Post, "/api/agent/clientes", json, chave);
        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());

        Assert.Equal(1, doc.RootElement.GetProperty("atualizados").GetInt32());
        Assert.Equal(0, doc.RootElement.GetProperty("novos").GetInt32());
        Assert.Equal(1, doc.RootElement.GetProperty("limitados").GetInt32());

        using var db2 = NovoDbContext();
        Assert.Equal(2, db2.Clientes.IgnoreQueryFilters().Count(c => c.EscritorioId == esc.Id));
    }

    // ── 6.7: tipo viaja como inteiro ──

    [Fact]
    public async Task Metricas_TipoInteiro_Aceito()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Métricas");
        var cliente = DataHelpers.CriarCliente(db, esc.Id, "0001");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Métricas");
        var execucao = await AbrirExecucao(chave);

        var json = JsonSerializer.Serialize(new
        {
            metricas = new[]
            {
                new { clienteId = cliente.Id, tipo = 0, competencia = "2026-07",
                      qtdBaixadas = 2, qtdPuladas = 0, qtdFalhas = 0, duracaoMs = 100 },
            },
        });
        var resposta = await EnviarJson(_client, HttpMethod.Post,
            $"/api/agent/execucoes/{execucao}/metricas", json, chave);
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
    }

    [Fact]
    public async Task Metricas_TipoString_Rejeitado()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Métricas2");
        var cliente = DataHelpers.CriarCliente(db, esc.Id, "0001");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Métricas2");
        var execucao = await AbrirExecucao(chave);

        // O agente manda 0/1 (api_client.TIPO_NOTA); o binding de minimal API
        // rejeita a string — hoje como 500 (exceção de deserialização
        // convertida pelo exception handler), não 400. A rejeição é o
        // contrato; o 400-vs-500 é cosmético e fora de escopo (o agente nunca
        // envia string). Se um dia isso passar a ser ACEITO, este teste falha
        // e o agente Python quebraria silenciosamente.
        var json = JsonSerializer.Serialize(new
        {
            metricas = new[]
            {
                new { clienteId = cliente.Id, tipo = "recebidas", competencia = "2026-07",
                      qtdBaixadas = 2, qtdPuladas = 0, qtdFalhas = 0, duracaoMs = 100 },
            },
        });
        var resposta = await EnviarJson(_client, HttpMethod.Post,
            $"/api/agent/execucoes/{execucao}/metricas", json, chave);
        Assert.NotEqual(HttpStatusCode.OK, resposta.StatusCode);
    }

    // ── 6.8: finalizar com status inteiro persiste ──

    [Fact]
    public async Task Finalizar_StatusInteiro_PersisteStatusEMensagemETermino()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Finalizar");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Finalizar");
        var execucao = await AbrirExecucao(chave);

        // status = 2 (Falha) como inteiro — StatusExecucao viaja como número
        var json = """{"status": 2, "mensagemErro": "erro de teste"}""";
        var resposta = await EnviarJson(_client, HttpMethod.Post,
            $"/api/agent/execucoes/{execucao}/finalizar", json, chave);
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);

        using var db2 = NovoDbContext();
        var gravada = db2.Execucoes.IgnoreQueryFilters().First(e => e.Id == Guid.Parse(execucao));
        Assert.Equal(StatusExecucao.Falha, gravada.Status);
        Assert.Equal("erro de teste", gravada.MensagemErro);
        Assert.NotNull(gravada.FinalizadoEm);
    }

    // ── 6.9: falha abre alerta sem duplicar (correção já aplicada) ──

    [Fact]
    public async Task FinalizarComFalha_AbreAlerta_E_NaoDuplica()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Alertas");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Alertas");

        var execucao1 = await AbrirExecucao(chave);
        var execucao2 = await AbrirExecucao(chave);

        var json = """{"status": 2, "mensagemErro": "falhou de verdade"}""";
        var r1 = await EnviarJson(_client, HttpMethod.Post, $"/api/agent/execucoes/{execucao1}/finalizar", json, chave);
        var r2 = await EnviarJson(_client, HttpMethod.Post, $"/api/agent/execucoes/{execucao2}/finalizar", json, chave);
        Assert.Equal(HttpStatusCode.OK, r1.StatusCode);
        Assert.Equal(HttpStatusCode.OK, r2.StatusCode);

        using var db2 = NovoDbContext();
        var alertas = db2.Alertas.IgnoreQueryFilters()
            .Where(a => a.EscritorioId == esc.Id && a.Tipo == TipoAlerta.ExecucaoFalhou)
            .ToList();
        Assert.Single(alertas); // segunda falha com alerta aberto não duplica
    }

    // ── 6.10: métricas fazem upsert pela chave (execução, cliente, competência, tipo) ──

    [Fact]
    public async Task Metricas_ChaveIgual_FazUpsertEmVezDeInserir()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Upsert Métricas");
        var cliente = DataHelpers.CriarCliente(db, esc.Id, "0001");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Upsert Métricas");
        var execucao = await AbrirExecucao(chave);

        var linha = new
        {
            metricas = new[]
            {
                new { clienteId = cliente.Id, tipo = 0, competencia = "2026-07",
                      qtdBaixadas = 2, qtdPuladas = 0, qtdFalhas = 0, duracaoMs = 100 },
            },
        };
        await EnviarJson(_client, HttpMethod.Post, $"/api/agent/execucoes/{execucao}/metricas",
            JsonSerializer.Serialize(linha), chave);
        var linha2 = new
        {
            metricas = new[]
            {
                new { clienteId = cliente.Id, tipo = 0, competencia = "2026-07",
                      qtdBaixadas = 9, qtdPuladas = 1, qtdFalhas = 0, duracaoMs = 200 },
            },
        };
        await EnviarJson(_client, HttpMethod.Post, $"/api/agent/execucoes/{execucao}/metricas",
            JsonSerializer.Serialize(linha2), chave);

        using var db2 = NovoDbContext();
        var linhas = db2.ExecucaoMetricas.IgnoreQueryFilters()
            .Where(m => m.ExecucaoId == Guid.Parse(execucao) && m.ClienteId == cliente.Id).ToList();
        Assert.Single(linhas);
        Assert.Equal(9, linhas[0].QtdBaixadas);
    }

    // ── 6.11: regras — 304 quando atual, bundle quando menor ──

    [Fact]
    public async Task Regras_VersaoAtual_Devolve304()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório Regras304");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente Regras304");

        var req = new HttpRequestMessage(HttpMethod.Get, "/api/agent/regras?versao=1"); // v1 é a ativa do seed
        req.Headers.Add("X-Api-Key", chave);
        var resposta = await _client.SendAsync(req);
        Assert.Equal(HttpStatusCode.NotModified, resposta.StatusCode);
    }

    [Fact]
    public async Task Regras_VersaoMenor_DevolveBundle()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório RegrasBundle");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente RegrasBundle");

        var req = new HttpRequestMessage(HttpMethod.Get, "/api/agent/regras?versao=0");
        req.Headers.Add("X-Api-Key", chave);
        var resposta = await _client.SendAsync(req);
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);

        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        Assert.Equal(1, doc.RootElement.GetProperty("versao").GetInt32());
        Assert.True(doc.RootElement.GetProperty("conteudo").TryGetProperty("portal", out _));
    }

    // ── 6.12: regras sem regra publicada — 404 ──

    [Fact]
    public async Task Regras_SemRegraPublicada_Devolve404()
    {
        using var db = NovoDbContext();
        var esc = DataHelpers.CriarEscritorio(db, "Escritório SemRegra");
        var (_, chave) = DataHelpers.CriarAgente(db, esc.Id, "Agente SemRegra");

        // Remove a regra do seed só para este teste e devolve depois — o
        // container é compartilhado pela coleção.
        _bancoRodarSql("DELETE FROM \"RegraColetas\"");
        try
        {
            var req = new HttpRequestMessage(HttpMethod.Get, "/api/agent/regras?versao=0");
            req.Headers.Add("X-Api-Key", chave);
            var resposta = await _client.SendAsync(req);
            Assert.Equal(HttpStatusCode.NotFound, resposta.StatusCode);
        }
        finally
        {
            RestaurarRegraV1();
        }
    }

    // ── helpers ──

    private void _bancoRodarSql(string sql) => _banco.RodarSql(sql);

    private void RestaurarRegraV1()
    {
        using var db = NovoDbContext();
        var regra = db.RegraColetas.FirstOrDefault();
        if (regra == null)
        {
            db.RegraColetas.Add(new RegraColeta
            {
                Versao = 1,
                Conteudo = ContabOne.Api.Domain.RegraSeedV1.Conteudo,
                PublicadaEm = DateTime.UtcNow,
                Ativa = true,
            });
            db.SaveChanges();
        }
    }

    private async Task<string> AbrirExecucao(string chave)
    {
        var resposta = await EnviarJson(_client, HttpMethod.Post, "/api/agent/execucoes", "{}", chave);
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        return doc.RootElement.GetProperty("execucaoId").GetString()!;
    }
}
