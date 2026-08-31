using System.Net;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.DependencyInjection;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using Xunit;

namespace ContabOne.Api.Tests.TestSupport;

/// <summary>
/// Criação de usuários reais (UserManager + roles) e login pelo endpoint
/// real — o token JWT passa pelo pipeline de verdade (geração, claims de
/// escritório, middleware de tenant).
/// </summary>
public static class AuthHelpers
{
    public static async Task GarantirRoles(IServiceProvider services)
    {
        using var scope = services.CreateScope();
        var roleManager = scope.ServiceProvider.GetRequiredService<RoleManager<IdentityRole<Guid>>>();
        foreach (var papel in new[] { "PlatformAdmin", "EscritorioAdmin", "EscritorioUsuario" })
        {
            if (!await roleManager.RoleExistsAsync(papel))
                await roleManager.CreateAsync(new IdentityRole<Guid>(papel));
        }
    }

    public static async Task<Usuario> CriarUsuario(
        IServiceProvider services, string email, string senha, string papel, Guid? escritorioId,
        string? nome = null, bool deveTrocarSenha = false)
    {
        using var scope = services.CreateScope();
        var userManager = scope.ServiceProvider.GetRequiredService<UserManager<Usuario>>();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        var usuario = new Usuario
        {
            UserName = email.Split('@')[0],
            Nome = nome ?? email.Split('@')[0],
            DeveTrocarSenha = deveTrocarSenha,
            Email = email,
            Papel = papel switch
            {
                "PlatformAdmin" => PapelUsuario.PlatformAdmin,
                "EscritorioAdmin" => PapelUsuario.EscritorioAdmin,
                _ => PapelUsuario.EscritorioUsuario,
            },
            Ativo = true,
            EmailConfirmed = true,
        };
        var criado = await userManager.CreateAsync(usuario, senha);
        if (!criado.Succeeded)
            throw new InvalidOperationException(
                $"Falha ao criar usuário {email}: {string.Join("; ", criado.Errors.Select(e => e.Description))}");
        await userManager.AddToRoleAsync(usuario, papel);

        if (escritorioId.HasValue)
        {
            db.UsuariosEscritorios.Add(new UsuarioEscritorio { UsuarioId = usuario.Id, EscritorioId = escritorioId.Value });
            await db.SaveChangesAsync();
        }
        return usuario;
    }

    /// <summary>Acrescenta um vínculo de escritório a um usuário já existente (para os testes de múltiplos vínculos).</summary>
    public static async Task VincularEscritorio(IServiceProvider services, Guid usuarioId, Guid escritorioId)
    {
        using var scope = services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        db.UsuariosEscritorios.Add(new UsuarioEscritorio { UsuarioId = usuarioId, EscritorioId = escritorioId });
        await db.SaveChangesAsync();
    }

    public static async Task<string> Login(HttpClient client, string email, string senha)
    {
        var resposta = await client.PostAsync("/api/auth/login",
            new StringContent(JsonSerializer.Serialize(new { email, password = senha }),
                Encoding.UTF8, "application/json"));
        Assert.True(resposta.StatusCode == HttpStatusCode.OK,
            $"login falhou com {resposta.StatusCode}: {await resposta.Content.ReadAsStringAsync()}");
        var doc = JsonDocument.Parse(await resposta.Content.ReadAsStringAsync());
        return doc.RootElement.GetProperty("accessToken").GetString()!;
    }
}
