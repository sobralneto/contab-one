using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using ContabOne.Api.Infra;
using ContabOne.Api.Tests.TestSupport;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// Gestão de usuários. Concentra os três riscos da feature:
///
/// 1. Isolamento — <c>Usuario</c> é a única entidade sem query filter global,
///    então o escopo por escritório é aplicado à mão em cada handler e só um
///    teste garante que ninguém esqueceu.
/// 2. Escalação de privilégio — admin de escritório não pode fabricar um
///    PlatformAdmin nem se promover.
/// 3. Papel efetivo — o login resolve o papel pela role do Identity, não pela
///    coluna Papel; criar usuário sem sincronizar as duas o deixaria com o
///    papel errado no token.
/// </summary>
[Trait("Category", "Banco")]
[Collection("Banco")]
public class UsuariosTest : IClassFixture<ApiFactory>
{
    private readonly ApiFactory _factory;
    private readonly HttpClient _client;
    private readonly string _sufixo;

    public UsuariosTest(ApiFactory factory)
    {
        _factory = factory;
        _client = factory.CreateClient();
        _sufixo = Guid.NewGuid().ToString("N")[..8];
    }

    private AppDbContext NovoDbContext()
        => _factory.Services.CreateScope().ServiceProvider.GetRequiredService<AppDbContext>();

    private static HttpRequestMessage Requisicao(HttpMethod metodo, string url, string token, object? corpo = null)
    {
        var req = new HttpRequestMessage(metodo, url);
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        if (corpo != null)
            req.Content = new StringContent(JsonSerializer.Serialize(corpo), Encoding.UTF8, "application/json");
        return req;
    }

    /// <summary>Escritório A com um admin logado, e um escritório B vizinho.</summary>
    private async Task<(Guid escA, Guid escB, string tokenAdminA)> CriarCenarioAsync()
    {
        Guid escA, escB;
        using (var db = NovoDbContext())
        {
            escA = DataHelpers.CriarEscritorio(db, $"Escritório A {_sufixo}").Id;
            escB = DataHelpers.CriarEscritorio(db, $"Escritório B {_sufixo}").Id;
        }

        await AuthHelpers.GarantirRoles(_factory.Services);
        var email = $"adminA_{_sufixo}@nfse.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "EscritorioAdmin", escA);
        var token = await AuthHelpers.Login(_client, email, "Senha123!");

        return (escA, escB, token);
    }

    // ── Isolamento ──

    [Fact]
    public async Task AdminDeEscritorioNaoVeUsuarioDeOutroEscritorio()
    {
        var (_, escB, tokenA) = await CriarCenarioAsync();
        await AuthHelpers.CriarUsuario(
            _factory.Services, $"deB_{_sufixo}@nfse.local", "Senha123!", "EscritorioUsuario", escB,
            nome: $"Fulano de B {_sufixo}");

        var resposta = await _client.SendAsync(Requisicao(HttpMethod.Get, "/api/usuarios", tokenA));
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);

        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        var nomes = doc.RootElement.EnumerateArray()
            .Select(u => u.GetProperty("nome").GetString()).ToList();

        Assert.DoesNotContain($"Fulano de B {_sufixo}", nomes);
    }

    [Fact]
    public async Task AdminDeEscritorioNaoEditaUsuarioDeOutroEscritorio()
    {
        var (_, escB, tokenA) = await CriarCenarioAsync();
        var alvo = await AuthHelpers.CriarUsuario(
            _factory.Services, $"alvoB_{_sufixo}@nfse.local", "Senha123!", "EscritorioUsuario", escB,
            nome: "Nome Original");

        var resposta = await _client.SendAsync(Requisicao(
            HttpMethod.Put, $"/api/usuarios/{alvo.Id}", tokenA, new { nome = "Invadido" }));

        // 404 e não 403: confirmar a existência já vazaria informação de B.
        Assert.Equal(HttpStatusCode.NotFound, resposta.StatusCode);

        using var db = NovoDbContext();
        var aindaIntacto = db.Users.First(u => u.Id == alvo.Id);
        Assert.Equal("Nome Original", aindaIntacto.Nome);
    }

    [Fact]
    public async Task AdminDeEscritorioNaoDesativaUsuarioDeOutroEscritorio()
    {
        var (_, escB, tokenA) = await CriarCenarioAsync();
        var alvo = await AuthHelpers.CriarUsuario(
            _factory.Services, $"desativarB_{_sufixo}@nfse.local", "Senha123!", "EscritorioUsuario", escB);

        var resposta = await _client.SendAsync(Requisicao(
            HttpMethod.Patch, $"/api/usuarios/{alvo.Id}/ativo", tokenA, new { ativo = false }));

        Assert.Equal(HttpStatusCode.NotFound, resposta.StatusCode);

        using var db = NovoDbContext();
        Assert.True(db.Users.First(u => u.Id == alvo.Id).Ativo);
    }

    [Fact]
    public async Task AdminDeEscritorioNaoVinculaUsuarioAOutroEscritorio()
    {
        var (_, escB, tokenA) = await CriarCenarioAsync();

        // Admin de A tenta criar usuário dentro de B pela lista de escritórios.
        var resposta = await _client.SendAsync(Requisicao(HttpMethod.Post, "/api/usuarios", tokenA, new
        {
            nome = "Tentativa Cross-Tenant",
            email = $"cross_{_sufixo}@nfse.local",
            senha = "Senha123!",
            papel = "EscritorioUsuario",
            escritorios = new[] { escB },
        }));

        Assert.Equal(HttpStatusCode.Forbidden, resposta.StatusCode);

        using var db = NovoDbContext();
        Assert.False(db.Users.Any(u => u.Email == $"cross_{_sufixo}@nfse.local"));
    }

    // ── Escalação de privilégio ──

    [Fact]
    public async Task AdminDeEscritorioNaoCriaPlatformAdmin()
    {
        var (_, _, tokenA) = await CriarCenarioAsync();

        var resposta = await _client.SendAsync(Requisicao(HttpMethod.Post, "/api/usuarios", tokenA, new
        {
            nome = "Tentativa de Escalação",
            email = $"escalacao_{_sufixo}@nfse.local",
            senha = "Senha123!",
            papel = "PlatformAdmin",
        }));

        Assert.Equal(HttpStatusCode.Forbidden, resposta.StatusCode);

        using var db = NovoDbContext();
        Assert.False(db.Users.Any(u => u.Email == $"escalacao_{_sufixo}@nfse.local"));
    }

    [Fact]
    public async Task AdminDeEscritorioNaoPromoveAlguemAPlatformAdmin()
    {
        var (escA, _, tokenA) = await CriarCenarioAsync();
        var comum = await AuthHelpers.CriarUsuario(
            _factory.Services, $"comum_{_sufixo}@nfse.local", "Senha123!", "EscritorioUsuario", escA);

        var resposta = await _client.SendAsync(Requisicao(
            HttpMethod.Put, $"/api/usuarios/{comum.Id}", tokenA, new { papel = "PlatformAdmin" }));

        Assert.Equal(HttpStatusCode.Forbidden, resposta.StatusCode);
    }

    [Fact]
    public async Task NaoPodeAlterarOProprioPapel()
    {
        var (escA, _, tokenA) = await CriarCenarioAsync();

        using var db = NovoDbContext();
        var eu = db.Users.First(u => u.Email == $"adminA_{_sufixo}@nfse.local");

        var resposta = await _client.SendAsync(Requisicao(
            HttpMethod.Put, $"/api/usuarios/{eu.Id}", tokenA, new { papel = "EscritorioUsuario" }));

        Assert.Equal(HttpStatusCode.BadRequest, resposta.StatusCode);
    }

    [Fact]
    public async Task NaoPodeDesativarOProprioUsuario()
    {
        var (_, _, tokenA) = await CriarCenarioAsync();

        using var db = NovoDbContext();
        var eu = db.Users.First(u => u.Email == $"adminA_{_sufixo}@nfse.local");

        var resposta = await _client.SendAsync(Requisicao(
            HttpMethod.Patch, $"/api/usuarios/{eu.Id}/ativo", tokenA, new { ativo = false }));

        Assert.Equal(HttpStatusCode.BadRequest, resposta.StatusCode);

        using var db2 = NovoDbContext();
        Assert.True(db2.Users.First(u => u.Id == eu.Id).Ativo);
    }

    // ── Validação ──

    [Fact]
    public async Task EmailDuplicadoRetornaErroDeValidacao()
    {
        var (escA, _, tokenA) = await CriarCenarioAsync();
        var email = $"duplicado_{_sufixo}@nfse.local";

        var corpo = new
        {
            nome = "Primeiro",
            email,
            senha = "Senha123!",
            papel = "EscritorioUsuario",
            escritorios = new[] { escA },
        };

        var primeira = await _client.SendAsync(Requisicao(HttpMethod.Post, "/api/usuarios", tokenA, corpo));
        Assert.Equal(HttpStatusCode.Created, primeira.StatusCode);

        var segunda = await _client.SendAsync(Requisicao(HttpMethod.Post, "/api/usuarios", tokenA, corpo));

        // 400 legível, não 500 vindo da violação de índice único.
        Assert.Equal(HttpStatusCode.BadRequest, segunda.StatusCode);
        var texto = await segunda.Content.ReadAsStringAsync();
        Assert.Contains("Já existe um usuário com este e-mail", texto);
    }

    [Fact]
    public async Task SenhaFracaRetornaErroDeValidacao()
    {
        var (_, _, tokenA) = await CriarCenarioAsync();

        var resposta = await _client.SendAsync(Requisicao(HttpMethod.Post, "/api/usuarios", tokenA, new
        {
            nome = "Senha Fraca",
            email = $"fraca_{_sufixo}@nfse.local",
            senha = "abc",
            papel = "EscritorioUsuario",
        }));

        Assert.Equal(HttpStatusCode.BadRequest, resposta.StatusCode);
    }

    // ── Nome, papel efetivo e troca de senha ──

    [Fact]
    public async Task UsuarioCriadoComNomeDeGenteLogaComPapelCorretoEExigeTrocaDeSenha()
    {
        var (escA, _, tokenA) = await CriarCenarioAsync();
        var email = $"joao_{_sufixo}@nfse.local";

        // "João Silva" tem espaço e acento: iria falhar se o nome fosse gravado
        // em UserName (AllowedUserNameCharacters do Identity).
        var criacao = await _client.SendAsync(Requisicao(HttpMethod.Post, "/api/usuarios", tokenA, new
        {
            nome = "João Silva",
            email,
            senha = "Senha123!",
            papel = "EscritorioAdmin",
            escritorios = new[] { escA },
        }));
        Assert.Equal(HttpStatusCode.Created, criacao.StatusCode);

        // O login precisa devolver o papel vindo da role do Identity.
        var resposta = await _client.PostAsync("/api/auth/login",
            new StringContent(JsonSerializer.Serialize(new { email, password = "Senha123!" }),
                Encoding.UTF8, "application/json"));
        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);

        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        var usuario = doc.RootElement.GetProperty("usuario");

        Assert.Equal("João Silva", usuario.GetProperty("nome").GetString());
        Assert.Equal("EscritorioAdmin", usuario.GetProperty("papel").GetString());
        Assert.True(usuario.GetProperty("deveTrocarSenha").GetBoolean());
    }

    [Fact]
    public async Task TrocaDeSenhaLimpaAExigenciaEDevolveTokenNovo()
    {
        var (escA, _, tokenA) = await CriarCenarioAsync();
        var email = $"troca_{_sufixo}@nfse.local";

        await _client.SendAsync(Requisicao(HttpMethod.Post, "/api/usuarios", tokenA, new
        {
            nome = "Quem Vai Trocar",
            email,
            senha = "Senha123!",
            papel = "EscritorioUsuario",
            escritorios = new[] { escA },
        }));

        var token = await AuthHelpers.Login(_client, email, "Senha123!");

        var troca = await _client.SendAsync(Requisicao(HttpMethod.Post, "/api/auth/trocar-senha", token, new
        {
            senhaAtual = "Senha123!",
            novaSenha = "OutraSenha456",
        }));
        Assert.Equal(HttpStatusCode.OK, troca.StatusCode);

        // O token devolvido precisa vir sem a flag, senão o guard do frontend
        // devolveria o usuário para a tela de troca até o token expirar.
        var docTroca = JsonDocument.Parse(await troca.Content.ReadAsStringAsync());
        var tokenNovo = docTroca.RootElement.GetProperty("accessToken").GetString()!;
        Assert.Equal("false", LerClaim(tokenNovo, "deve_trocar_senha"));

        // E a senha nova é a que passa a valer.
        var relogin = await _client.PostAsync("/api/auth/login",
            new StringContent(JsonSerializer.Serialize(new { email, password = "OutraSenha456" }),
                Encoding.UTF8, "application/json"));
        Assert.Equal(HttpStatusCode.OK, relogin.StatusCode);

        var docRelogin = JsonDocument.Parse(await relogin.Content.ReadAsStringAsync());
        Assert.False(docRelogin.RootElement.GetProperty("usuario").GetProperty("deveTrocarSenha").GetBoolean());
    }

    [Fact]
    public async Task TrocaDeSenhaComSenhaAtualErradaFalha()
    {
        var (escA, _, _) = await CriarCenarioAsync();
        var email = $"senhaerrada_{_sufixo}@nfse.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "EscritorioUsuario", escA);
        var token = await AuthHelpers.Login(_client, email, "Senha123!");

        var troca = await _client.SendAsync(Requisicao(HttpMethod.Post, "/api/auth/trocar-senha", token, new
        {
            senhaAtual = "SenhaErrada999",
            novaSenha = "OutraSenha456",
        }));

        Assert.Equal(HttpStatusCode.BadRequest, troca.StatusCode);
    }

    [Fact]
    public async Task ResetDeSenhaPeloAdminVoltaAExigirTroca()
    {
        var (escA, _, tokenA) = await CriarCenarioAsync();
        var email = $"reset_{_sufixo}@nfse.local";
        var alvo = await AuthHelpers.CriarUsuario(
            _factory.Services, email, "Senha123!", "EscritorioUsuario", escA);

        var reset = await _client.SendAsync(Requisicao(
            HttpMethod.Post, $"/api/usuarios/{alvo.Id}/senha", tokenA, new { novaSenha = "NovaSenha789" }));
        Assert.Equal(HttpStatusCode.OK, reset.StatusCode);

        var doc = JsonDocument.Parse(await (await _client.PostAsync("/api/auth/login",
            new StringContent(JsonSerializer.Serialize(new { email, password = "NovaSenha789" }),
                Encoding.UTF8, "application/json"))).Content.ReadAsStringAsync());

        Assert.True(doc.RootElement.GetProperty("usuario").GetProperty("deveTrocarSenha").GetBoolean());
    }

    // ── PlatformAdmin ──

    [Fact]
    public async Task PlatformAdminCriaPlatformAdminSemEscritorio()
    {
        await AuthHelpers.GarantirRoles(_factory.Services);
        var emailAdmin = $"plataforma_{_sufixo}@nfse.local";
        await AuthHelpers.CriarUsuario(_factory.Services, emailAdmin, "Senha123!", "PlatformAdmin", null);
        var token = await AuthHelpers.Login(_client, emailAdmin, "Senha123!");

        var email = $"novoPlataforma_{_sufixo}@nfse.local";
        var resposta = await _client.SendAsync(Requisicao(HttpMethod.Post, "/api/usuarios", token, new
        {
            nome = "Outro Admin da Plataforma",
            email,
            senha = "Senha123!",
            papel = "PlatformAdmin",
        }));

        Assert.Equal(HttpStatusCode.Created, resposta.StatusCode);

        using var db = NovoDbContext();
        var criado = db.Users.First(u => u.Email == email);
        Assert.Empty(db.UsuariosEscritorios.Where(v => v.UsuarioId == criado.Id)); // admin de plataforma não pertence a escritório
    }

    [Fact]
    public async Task UsuarioComumNaoAlcancaAGestaoDeUsuarios()
    {
        var (escA, _, _) = await CriarCenarioAsync();
        var email = $"comumSemAcesso_{_sufixo}@nfse.local";
        await AuthHelpers.CriarUsuario(_factory.Services, email, "Senha123!", "EscritorioUsuario", escA);
        var token = await AuthHelpers.Login(_client, email, "Senha123!");

        var resposta = await _client.SendAsync(Requisicao(HttpMethod.Get, "/api/usuarios", token));

        Assert.Equal(HttpStatusCode.Forbidden, resposta.StatusCode);
    }

    /// <summary>Lê uma claim do payload do JWT sem validar assinatura.</summary>
    private static string? LerClaim(string token, string claim)
    {
        var payload = token.Split('.')[1].Replace('-', '+').Replace('_', '/');
        payload = payload.PadRight(payload.Length + (4 - payload.Length % 4) % 4, '=');
        var json = Encoding.UTF8.GetString(Convert.FromBase64String(payload));
        var doc = JsonDocument.Parse(json);
        return doc.RootElement.TryGetProperty(claim, out var valor) ? valor.GetString() : null;
    }
}
