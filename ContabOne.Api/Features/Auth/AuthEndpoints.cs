using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Identity;
using Microsoft.IdentityModel.Tokens;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Auth;

public static class AuthEndpoints
{
    private const int AccessTokenMinutes = 15;
    private const int RefreshTokenDays = 7;

    public static RouteGroupBuilder MapAuthEndpoints(this RouteGroupBuilder group)
    {
        group.MapPost("/login", LoginAsync).AllowAnonymous();
        group.MapPost("/refresh", RefreshAsync).AllowAnonymous();
        group.MapPost("/logout", LogoutAsync).AllowAnonymous();
        // Único endpoint do grupo que exige sessão: quem troca a senha já está
        // autenticado (só está preso na tela de troca pela flag DeveTrocarSenha).
        group.MapPost("/trocar-senha", TrocarSenhaAsync).RequireAuthorization();
        return group;
    }

    // Hash descartável usado quando o e-mail não existe: verificar contra ele
    // gasta as mesmas ~90ms de derivação de chave que um usuário real, então o
    // tempo de resposta não revela quais e-mails existem (design §7.1).
    private const string DummyHash = "AQAAAAIAAYagAAAAEMVn2h1gKfmLxPhRkZK1HNQf9NWKL0QxqMyf0kF0AX1y3Mq0IdFNe5GXa4DqKh1F9A==";

    private static async Task<IResult> LoginAsync(
        LoginRequest req,
        UserManager<Usuario> userManager,
        IConfiguration config,
        HttpResponse response)
    {
        var user = await userManager.FindByEmailAsync(req.Email);

        // A verificação de senha vem ANTES das checagens de conta (ativo,
        // bloqueado) de propósito: sair cedo em qualquer uma delas devolveria
        // resposta instantânea e denunciaria a existência do e-mail.
        //
        // Fica uma diferença residual conhecida: senha errada de um usuário
        // que existe grava AccessFailedAsync, e esse write não acontece no
        // caminho do e-mail inexistente. É da ordem de poucos ms contra ~90ms
        // do hash, mas não é zero — fechar de vez exigiria gravar a falha fora
        // do caminho da resposta.
        var senhaOk = user != null
            ? await userManager.CheckPasswordAsync(user, req.Password)
            : userManager.PasswordHasher.VerifyHashedPassword(
                  new Usuario(), DummyHash, req.Password) == PasswordVerificationResult.Success;

        if (user == null || !user.Ativo)
            return Results.Unauthorized();

        if (await userManager.IsLockedOutAsync(user))
            return Results.Unauthorized();

        if (!senhaOk)
        {
            await userManager.AccessFailedAsync(user);
            return Results.Unauthorized();
        }

        await userManager.ResetAccessFailedCountAsync(user);

        user.UltimoLoginEm = DateTime.UtcNow;
        await userManager.UpdateAsync(user);

        var roles = await userManager.GetRolesAsync(user);
        var papel = roles.FirstOrDefault() ?? user.Papel.ToString();

        Guid? escritorioId = user.EscritorioId;
        if (papel == "PlatformAdmin")
            escritorioId = null;

        var jwtKey = config["JWT_SIGNING_KEY"]!;
        var accessToken = GenerateAccessToken(
            user.Id, escritorioId, papel, user.Email!, user.Nome, user.DeveTrocarSenha, jwtKey, config);
        var refreshToken = GenerateRefreshToken(user.Id, jwtKey, config);

        // Set refresh token as httpOnly cookie (§7)
        response.Cookies.Append("refresh_token", refreshToken, new CookieOptions
        {
            HttpOnly = true,
            Secure = true,
            SameSite = SameSiteMode.Strict,
            Expires = DateTime.UtcNow.AddDays(RefreshTokenDays),
        });

        return Results.Ok(new LoginResponse
        {
            AccessToken = accessToken,
            Usuario = new UsuarioDto
            {
                Id = user.Id,
                Email = user.Email!,
                Nome = user.Nome,
                Papel = papel,
                EscritorioId = escritorioId,
                DeveTrocarSenha = user.DeveTrocarSenha,
            }
        });
    }

    private static async Task<IResult> RefreshAsync(
        HttpRequest request,
        HttpResponse response,
        UserManager<Usuario> userManager,
        IConfiguration config)
    {
        var refreshToken = request.Cookies["refresh_token"];
        if (string.IsNullOrEmpty(refreshToken))
            return Results.Unauthorized();

        // Validate the refresh token JWT
        var principal = ValidateRefreshToken(refreshToken, config);
        if (principal == null)
            return Results.Unauthorized();

        // JwtSecurityTokenHandler remapeia "sub" para o ClaimTypes.NameIdentifier (URI longa)
        // por padrão ao validar — o mesmo padrão já usado em TenantContextMiddleware.
        var userIdStr = principal.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!Guid.TryParse(userIdStr, out var userId))
            return Results.Unauthorized();

        var user = await userManager.FindByIdAsync(userId.ToString());
        if (user == null || !user.Ativo)
            return Results.Unauthorized();

        var roles = await userManager.GetRolesAsync(user);
        var papel = roles.FirstOrDefault() ?? user.Papel.ToString();

        Guid? escritorioId = user.EscritorioId;
        if (papel == "PlatformAdmin")
            escritorioId = null;

        var jwtKey = config["JWT_SIGNING_KEY"]!;
        var accessToken = GenerateAccessToken(
            user.Id, escritorioId, papel, user.Email!, user.Nome, user.DeveTrocarSenha, jwtKey, config);
        var newRefreshToken = GenerateRefreshToken(user.Id, jwtKey, config);

        response.Cookies.Append("refresh_token", newRefreshToken, new CookieOptions
        {
            HttpOnly = true,
            Secure = true,
            SameSite = SameSiteMode.Strict,
            Expires = DateTime.UtcNow.AddDays(RefreshTokenDays),
        });

        return Results.Ok(new { accessToken });
    }

    private static async Task<IResult> LogoutAsync(HttpResponse response)
    {
        response.Cookies.Delete("refresh_token");
        return Results.Ok(new { message = "Logged out" });
    }

    private static async Task<IResult> TrocarSenhaAsync(
        TrocarSenhaRequest req,
        ClaimsPrincipal principal,
        UserManager<Usuario> userManager,
        IConfiguration config)
    {
        var userIdStr = principal.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!Guid.TryParse(userIdStr, out var userId))
            return Results.Unauthorized();

        var user = await userManager.FindByIdAsync(userId.ToString());
        if (user == null || !user.Ativo)
            return Results.Unauthorized();

        var resultado = await userManager.ChangePasswordAsync(user, req.SenhaAtual, req.NovaSenha);
        if (!resultado.Succeeded)
            return Results.ValidationProblem(IdentityErrosParaDicionario(resultado));

        user.DeveTrocarSenha = false;
        await userManager.UpdateAsync(user);

        var roles = await userManager.GetRolesAsync(user);
        var papel = roles.FirstOrDefault() ?? user.Papel.ToString();

        Guid? escritorioId = user.EscritorioId;
        if (papel == "PlatformAdmin")
            escritorioId = null;

        // Token novo já sem a flag: o access token vale 15 min e, sem trocá-lo
        // aqui, o guard do frontend continuaria devolvendo o usuário para a
        // tela de troca até o token vencer.
        var accessToken = GenerateAccessToken(
            user.Id, escritorioId, papel, user.Email!, user.Nome, false, config["JWT_SIGNING_KEY"]!, config);

        return Results.Ok(new { accessToken });
    }

    /// <summary>
    /// Traduz erros do Identity (senha fraca, senha atual errada) para o mesmo
    /// formato de ValidationProblem que o FluentValidation produz no resto da
    /// API — o frontend trata um formato só.
    /// </summary>
    internal static Dictionary<string, string[]> IdentityErrosParaDicionario(IdentityResult resultado)
        => new()
        {
            ["senha"] = resultado.Errors.Select(e => e.Description).ToArray(),
        };

    // ── Token generation ──

    // Emissor e destinatário vêm da configuração — os mesmos valores que
    // Program.cs usa para validar. `config` é parâmetro obrigatório de quem
    // emite e de quem valida de propósito: quando era opcional com literal de
    // fallback, definir JWT_ISSUER em produção fazia a API emitir com um valor
    // e validar com outro, rejeitando todos os próprios tokens.
    internal const string IssuerPadrao = "nfse-api";
    internal const string AudiencePadrao = "nfse-frontend";

    private static string Issuer(IConfiguration config) => config["JWT_ISSUER"] ?? IssuerPadrao;
    private static string Audience(IConfiguration config) => config["JWT_AUDIENCE"] ?? AudiencePadrao;

    private static string GenerateAccessToken(
        Guid usuarioId, Guid? escritorioId, string papel, string email, string nome,
        bool deveTrocarSenha, string jwtKey, IConfiguration config)
    {
        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var claims = new List<Claim>
        {
            new(JwtRegisteredClaimNames.Sub, usuarioId.ToString()),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
            new(JwtRegisteredClaimNames.Email, email),
            new("nome", nome),
            new(ClaimTypes.Role, papel),
            // Precisa viver no token, não só no corpo do login: o frontend
            // restaura a sessão decodificando o JWT (stores/auth.ts) e refaz o
            // bootstrap por refresh (router/guards.ts). Fora do token, um F5
            // apagaria a exigência de troca de senha.
            new("deve_trocar_senha", deveTrocarSenha ? "true" : "false"),
        };

        if (escritorioId.HasValue)
            claims.Add(new Claim("escritorio_id", escritorioId.Value.ToString()));

        var token = new JwtSecurityToken(
            issuer: Issuer(config),
            audience: Audience(config),
            claims: claims,
            expires: DateTime.UtcNow.AddMinutes(AccessTokenMinutes),
            signingCredentials: creds);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    private static string GenerateRefreshToken(Guid usuarioId, string jwtKey, IConfiguration config)
    {
        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var claims = new[]
        {
            new Claim(JwtRegisteredClaimNames.Sub, usuarioId.ToString()),
            new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
            new Claim("purpose", "refresh"),
        };

        var token = new JwtSecurityToken(
            issuer: Issuer(config),
            audience: Audience(config),
            claims: claims,
            expires: DateTime.UtcNow.AddDays(RefreshTokenDays),
            signingCredentials: creds);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    private static ClaimsPrincipal? ValidateRefreshToken(string token, IConfiguration config)
    {
        try
        {
            var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(config["JWT_SIGNING_KEY"]!));
            var handler = new JwtSecurityTokenHandler();
            var principal = handler.ValidateToken(token, new TokenValidationParameters
            {
                ValidateIssuerSigningKey = true,
                IssuerSigningKey = key,
                ValidIssuer = Issuer(config),
                ValidAudience = Audience(config),
                ValidateIssuer = true,
                ValidateAudience = true,
                ValidateLifetime = true,
                ClockSkew = TimeSpan.FromMinutes(1),
            }, out _);

            // Impede que um access token (mesma chave/claims sub+jti) seja reaproveitado como refresh token.
            if (principal.FindFirstValue("purpose") != "refresh")
                return null;

            return principal;
        }
        catch
        {
            return null;
        }
    }
}

// ── DTOs ──

public record LoginRequest(string Email, string Password);

public record TrocarSenhaRequest(string SenhaAtual, string NovaSenha);

public record LoginResponse
{
    public string AccessToken { get; init; } = string.Empty;
    public UsuarioDto Usuario { get; init; } = null!;
}

public record UsuarioDto
{
    public Guid Id { get; init; }
    public string Email { get; init; } = string.Empty;
    public string Nome { get; init; } = string.Empty;
    public string Papel { get; init; } = string.Empty;
    public Guid? EscritorioId { get; init; }
    public bool DeveTrocarSenha { get; init; }
}
