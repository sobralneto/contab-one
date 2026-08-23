using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using ContabOne.Api.Infra;
using ContabOne.Api.Tests.TestSupport;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// Emissão e validação de JWT têm que ler a MESMA configuração de emissor e
/// destinatário.
///
/// O defeito que este teste tranca: a validação lia JWT_ISSUER/JWT_AUDIENCE da
/// configuração, mas a emissão caía num literal embutido. Sem nenhuma das duas
/// variáveis definidas, os valores coincidiam por acaso e tudo funcionava —
/// definir JWT_ISSUER em produção fazia a API rejeitar os próprios tokens e
/// derrubava todo mundo. Um teste sem as variáveis definidas nunca pegaria
/// isso; por isso a fábrica abaixo as define.
/// </summary>
public class FabricaComEmissorConfigurado : ApiFactory
{
    public const string Issuer = "contab-one-api";
    public const string Audience = "contab-one-frontend";

    public FabricaComEmissorConfigurado(PostgresFixture banco) : base(banco) { }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        base.ConfigureWebHost(builder);
        builder.ConfigureAppConfiguration((_, config) =>
        {
            config.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["JWT_ISSUER"] = Issuer,
                ["JWT_AUDIENCE"] = Audience,
            });
        });
    }
}

[Trait("Category", "Banco")]
[Collection("Banco")]
public class TokenIssuerTest
{
    private readonly PostgresFixture _banco;
    private readonly string _sufixo = Guid.NewGuid().ToString("N")[..8];

    public TokenIssuerTest(PostgresFixture banco) => _banco = banco;

    [Fact]
    public async Task ComEmissorConfigurado_ApiAceitaOProprioToken()
    {
        using var factory = new FabricaComEmissorConfigurado(_banco);
        var client = factory.CreateClient();

        Guid escritorioId;
        using (var scope = factory.Services.CreateScope())
        {
            var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
            escritorioId = DataHelpers.CriarEscritorio(db, $"Escritório Emissor {_sufixo}").Id;
        }

        await AuthHelpers.GarantirRoles(factory.Services);
        var email = $"emissor_{_sufixo}@nfse.local";
        await AuthHelpers.CriarUsuario(factory.Services, email, "Senha123!", "EscritorioAdmin", escritorioId);

        var token = await AuthHelpers.Login(client, email, "Senha123!");

        var req = new HttpRequestMessage(HttpMethod.Get, "/api/clientes");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        var resposta = await client.SendAsync(req);

        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
    }

    [Fact]
    public async Task ComEmissorConfigurado_RefreshTokenContinuaValido()
    {
        using var factory = new FabricaComEmissorConfigurado(_banco);
        var client = factory.CreateClient();

        Guid escritorioId;
        using (var scope = factory.Services.CreateScope())
        {
            var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
            escritorioId = DataHelpers.CriarEscritorio(db, $"Escritório Refresh {_sufixo}").Id;
        }

        await AuthHelpers.GarantirRoles(factory.Services);
        var email = $"refresh_{_sufixo}@nfse.local";
        await AuthHelpers.CriarUsuario(factory.Services, email, "Senha123!", "EscritorioAdmin", escritorioId);

        var login = await client.PostAsync("/api/auth/login",
            new StringContent(JsonSerializer.Serialize(new { email, password = "Senha123!" }),
                Encoding.UTF8, "application/json"));
        Assert.Equal(HttpStatusCode.OK, login.StatusCode);

        // O cookie de refresh volta no Set-Cookie; reenviá-lo tem que render
        // um access token novo — emitido e validado com o mesmo emissor.
        var cookie = login.Headers.GetValues("Set-Cookie")
            .First(c => c.StartsWith("refresh_token=", StringComparison.Ordinal))
            .Split(';')[0];

        var req = new HttpRequestMessage(HttpMethod.Post, "/api/auth/refresh");
        req.Headers.Add("Cookie", cookie);
        var resposta = await client.SendAsync(req);

        Assert.Equal(HttpStatusCode.OK, resposta.StatusCode);
        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        Assert.False(string.IsNullOrEmpty(doc.RootElement.GetProperty("accessToken").GetString()));
    }
}
