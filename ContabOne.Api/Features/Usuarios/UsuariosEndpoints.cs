using FluentValidation;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Usuarios;

/// <summary>
/// Gestão de usuários do painel. Antes disto, o único caminho para criar
/// usuário era /api/seed/*, que só existe em Development — ou seja, uma base
/// de produção nova não tinha como cadastrar ninguém.
///
/// ATENÇÃO ao escopo de tenant: <see cref="Usuario"/> e <see cref="UsuarioEscritorio"/>
/// são entidades sem query filter global no <see cref="AppDbContext"/> (o UserManager
/// precisa encontrar o usuário no login, antes de existir tenant resolvido). Todo
/// handler daqui aplica o escopo na mão — ver <see cref="EscritoriosVisiveisAsync"/>.
/// </summary>
public static class UsuariosEndpoints
{
    public static RouteGroupBuilder MapUsuariosEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/", ListarAsync);
        group.MapPost("/", CriarAsync);
        group.MapPut("/{id:guid}", AtualizarAsync);
        group.MapPost("/{id:guid}/senha", ResetarSenhaAsync);
        group.MapPatch("/{id:guid}/ativo", AlterarAtivoAsync);
        return group;
    }

    // ── Listagem ──

    private static async Task<IResult> ListarAsync(AppDbContext db, TenantContext tenant)
    {
        var visiveis = await EscritoriosVisiveisAsync(db, tenant);

        // PlatformAdmin sem foco vê todos os usuários com todos os vínculos;
        // os demais, só usuários com vínculo em comum e, de cada um, apenas os
        // vínculos que o solicitante também enxerga (senão listar usuários
        // viraria jeito indireto de descobrir a carteira de um colega).
        if (visiveis == null)
        {
            var todos = await db.Users
                .OrderBy(u => u.Nome)
                .Select(u => new UsuarioListaDto(
                    u.Id, u.Nome, u.Email!, u.Papel.ToString(),
                    u.Escritorios.OrderBy(v => v.Escritorio.Nome)
                        .Select(v => new EscritorioVinculoDto(v.EscritorioId, v.Escritorio.Nome)).ToList(),
                    u.Ativo, u.DeveTrocarSenha, u.UltimoLoginEm))
                .ToListAsync();
            return Results.Ok(todos);
        }

        var usuarios = await db.Users
            .Where(u => u.Escritorios.Any(v => visiveis.Contains(v.EscritorioId)))
            .OrderBy(u => u.Nome)
            .Select(u => new UsuarioListaDto(
                u.Id, u.Nome, u.Email!, u.Papel.ToString(),
                u.Escritorios.Where(v => visiveis.Contains(v.EscritorioId))
                    .OrderBy(v => v.Escritorio.Nome)
                    .Select(v => new EscritorioVinculoDto(v.EscritorioId, v.Escritorio.Nome)).ToList(),
                u.Ativo, u.DeveTrocarSenha, u.UltimoLoginEm))
            .ToListAsync();

        return Results.Ok(usuarios);
    }

    // ── Criação ──

    private static async Task<IResult> CriarAsync(
        CriarUsuarioRequest req,
        IValidator<CriarUsuarioRequest> validator,
        UserManager<Usuario> userManager,
        RoleManager<IdentityRole<Guid>> roleManager,
        AppDbContext db,
        TenantContext tenant)
    {
        var validation = await validator.ValidateAsync(req);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        if (!Enum.TryParse<PapelUsuario>(req.Papel, true, out var papel))
            return Erro("papel", "Papel inválido");

        // Escalação de privilégio: só a plataforma concede o papel PlatformAdmin.
        if (papel == PapelUsuario.PlatformAdmin && !tenant.IsAdmin)
            return Results.Json(
                new { erro = "Apenas o admin da plataforma pode conceder o papel PlatformAdmin" },
                statusCode: StatusCodes.Status403Forbidden);

        var visiveis = await EscritoriosVisiveisAsync(db, tenant);

        var escritorios = (req.Escritorios ?? []).Distinct().ToList();

        if (papel != PapelUsuario.PlatformAdmin && escritorios.Count == 0)
            return Erro("escritorios", "O usuário precisa de ao menos um escritório");

        // Admin de escritório só vincula aos próprios escritórios; PlatformAdmin
        // (sem foco, visiveis == null) vincula a qualquer um.
        if (visiveis != null && escritorios.Any(e => !visiveis.Contains(e)))
            return Results.Json(
                new { erro = "Você só pode vincular usuários aos seus próprios escritórios" },
                statusCode: StatusCodes.Status403Forbidden);

        var usuario = new Usuario
        {
            // UserName recebe o e-mail: AllowedUserNameCharacters do Identity
            // rejeita espaço e acento, então nome de pessoa não cabe aqui.
            UserName = req.Email,
            Email = req.Email,
            Nome = req.Nome,
            Papel = papel,
            Ativo = true,
            EmailConfirmed = true,
            // Senha definida por outra pessoa nunca é senha final.
            DeveTrocarSenha = true,
        };

        var criado = await userManager.CreateAsync(usuario, req.Senha);
        if (!criado.Succeeded)
            return Results.ValidationProblem(MapearErrosIdentity(criado));

        await AtribuirPapelAsync(userManager, roleManager, usuario, papel);

        foreach (var escritorioId in escritorios)
        {
            db.UsuariosEscritorios.Add(new UsuarioEscritorio { UsuarioId = usuario.Id, EscritorioId = escritorioId });
        }
        await db.SaveChangesAsync();

        return Results.Created($"/api/usuarios/{usuario.Id}", new
        {
            usuario.Id,
            usuario.Nome,
            usuario.Email,
            Papel = papel.ToString(),
        });
    }

    // ── Atualização ──

    private static async Task<IResult> AtualizarAsync(
        Guid id,
        AtualizarUsuarioRequest req,
        IValidator<AtualizarUsuarioRequest> validator,
        UserManager<Usuario> userManager,
        RoleManager<IdentityRole<Guid>> roleManager,
        AppDbContext db,
        TenantContext tenant)
    {
        var validation = await validator.ValidateAsync(req);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        var usuario = await BuscarNoEscopoAsync(db, tenant, id);
        if (usuario == null)
            return Results.NotFound();

        if (!string.IsNullOrWhiteSpace(req.Nome))
            usuario.Nome = req.Nome;

        var papel = usuario.Papel;
        if (!string.IsNullOrEmpty(req.Papel))
        {
            if (!Enum.TryParse<PapelUsuario>(req.Papel, true, out var novoPapel))
                return Erro("papel", "Papel inválido");

            // Escalação de privilégio: só a plataforma concede o papel PlatformAdmin.
            if (novoPapel == PapelUsuario.PlatformAdmin && !tenant.IsAdmin)
                return Results.Json(
                    new { erro = "Apenas o admin da plataforma pode conceder o papel PlatformAdmin" },
                    statusCode: StatusCodes.Status403Forbidden);

            // Rebaixar a si mesmo tira o acesso a esta própria tela — e se for o
            // único admin do escritório, ninguém consegue desfazer.
            if (novoPapel != usuario.Papel && id == tenant.UsuarioId)
                return Erro("papel", "Você não pode alterar o próprio papel");

            papel = novoPapel;
        }

        if (req.Escritorios != null)
        {
            var visiveis = await EscritoriosVisiveisAsync(db, tenant);

            // EscritorioAdmin só mexe nos vínculos que enxerga; o vínculo do
            // usuário com um escritório fora do alcance do solicitante permanece
            // intocado (não dá para editar o alcance de quem está fora do escopo).
            if (visiveis != null && req.Escritorios.Any(e => !visiveis.Contains(e)))
                return Results.Json(
                    new { erro = "Você só pode vincular usuários aos seus próprios escritórios" },
                    statusCode: StatusCodes.Status403Forbidden);

            var atuais = await db.UsuariosEscritorios
                .Where(v => v.UsuarioId == id).Select(v => v.EscritorioId).ToListAsync();
            var foraDoAlcance = visiveis == null ? [] : atuais.Where(x => !visiveis.Contains(x)).ToList();

            var novos = req.Escritorios.Distinct().Concat(foraDoAlcance).Distinct().ToList();

            if (papel != PapelUsuario.PlatformAdmin && novos.Count == 0)
                return Erro("escritorios", "O usuário precisa de ao menos um escritório ou de mudança de papel");

            var existentes = await db.UsuariosEscritorios.Where(v => v.UsuarioId == id).ToListAsync();
            db.UsuariosEscritorios.RemoveRange(existentes);
            foreach (var escritorioId in novos)
            {
                db.UsuariosEscritorios.Add(new UsuarioEscritorio { UsuarioId = id, EscritorioId = escritorioId });
            }
        }

        if (papel != usuario.Papel)
        {
            usuario.Papel = papel;
            await AtribuirPapelAsync(userManager, roleManager, usuario, papel);
        }

        var atualizado = await userManager.UpdateAsync(usuario);
        if (!atualizado.Succeeded)
            return Results.ValidationProblem(MapearErrosIdentity(atualizado));

        return Results.Ok(new
        {
            usuario.Id,
            usuario.Nome,
            Papel = usuario.Papel.ToString(),
        });
    }

    // ── Reset de senha ──

    private static async Task<IResult> ResetarSenhaAsync(
        Guid id,
        ResetarSenhaRequest req,
        IValidator<ResetarSenhaRequest> validator,
        UserManager<Usuario> userManager,
        AppDbContext db,
        TenantContext tenant)
    {
        var validation = await validator.ValidateAsync(req);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        var usuario = await BuscarNoEscopoAsync(db, tenant, id);
        if (usuario == null)
            return Results.NotFound();

        var token = await userManager.GeneratePasswordResetTokenAsync(usuario);
        var resultado = await userManager.ResetPasswordAsync(usuario, token, req.NovaSenha);
        if (!resultado.Succeeded)
            return Results.ValidationProblem(MapearErrosIdentity(resultado));

        // Senha definida por um admin volta a ser provisória.
        usuario.DeveTrocarSenha = true;
        await userManager.UpdateAsync(usuario);

        return Results.Ok(new { usuario.Id, senhaRedefinida = true });
    }

    // ── Ativar / desativar ──

    private static async Task<IResult> AlterarAtivoAsync(
        Guid id,
        AlterarAtivoRequest req,
        UserManager<Usuario> userManager,
        AppDbContext db,
        TenantContext tenant)
    {
        var usuario = await BuscarNoEscopoAsync(db, tenant, id);
        if (usuario == null)
            return Results.NotFound();

        // Desativar a si mesmo derruba o próprio acesso no próximo login/refresh.
        if (!req.Ativo && id == tenant.UsuarioId)
            return Erro("ativo", "Você não pode desativar o próprio usuário");

        usuario.Ativo = req.Ativo;
        var atualizado = await userManager.UpdateAsync(usuario);
        if (!atualizado.Succeeded)
            return Results.ValidationProblem(MapearErrosIdentity(atualizado));

        return Results.Ok(new { usuario.Id, usuario.Ativo });
    }

    // ── Apoio ──

    /// <summary>
    /// Escritórios que o solicitante pode enxergar para gestão de usuários:
    /// <c>null</c> para PlatformAdmin sem foco (todos); o escritório em foco
    /// para PlatformAdmin com foco; e o conjunto dos vínculos do próprio
    /// EscritorioAdmin. Sem escopo resolvido, lista vazia (fail-closed).
    /// </summary>
    private static async Task<List<Guid>?> EscritoriosVisiveisAsync(AppDbContext db, TenantContext tenant)
    {
        if (tenant.VeTodosOsEscritorios)
            return null;

        if (tenant.IsAdmin)
            return tenant.EscritorioId.HasValue ? [tenant.EscritorioId.Value] : [];

        if (tenant.UsuarioId == null)
            return [];

        return await db.UsuariosEscritorios
            .Where(v => v.UsuarioId == tenant.UsuarioId.Value)
            .Select(v => v.EscritorioId)
            .ToListAsync();
    }

    /// <summary>
    /// Busca escopada ao tenant. Devolve null (→ 404) quando o alvo é de outro
    /// escritório: 404 em vez de 403 para não confirmar que o usuário existe.
    /// </summary>
    private static async Task<Usuario?> BuscarNoEscopoAsync(AppDbContext db, TenantContext tenant, Guid id)
    {
        var visiveis = await EscritoriosVisiveisAsync(db, tenant);
        if (visiveis == null)
            return await db.Users.FirstOrDefaultAsync(u => u.Id == id);

        return await db.Users
            .Where(u => u.Id == id && u.Escritorios.Any(v => visiveis.Contains(v.EscritorioId)))
            .FirstOrDefaultAsync();
    }

    /// <summary>
    /// Grava a coluna Papel e a role do Identity em par, removendo as anteriores.
    /// O login resolve o papel efetivo por <c>roles.FirstOrDefault()</c>, então
    /// deixar duas roles ativas tornaria o papel não-determinístico.
    /// </summary>
    private static async Task AtribuirPapelAsync(
        UserManager<Usuario> userManager,
        RoleManager<IdentityRole<Guid>> roleManager,
        Usuario usuario,
        PapelUsuario papel)
    {
        var nomePapel = papel.ToString();

        // O seed que cria as roles é dev-only: numa base de produção nova a
        // tabela de roles está vazia e o AddToRoleAsync falharia calado.
        if (!await roleManager.RoleExistsAsync(nomePapel))
            await roleManager.CreateAsync(new IdentityRole<Guid>(nomePapel));

        var atuais = await userManager.GetRolesAsync(usuario);
        if (atuais.Count > 0)
            await userManager.RemoveFromRolesAsync(usuario, atuais);

        await userManager.AddToRoleAsync(usuario, nomePapel);
    }

    private static IResult Erro(string campo, string mensagem)
        => Results.ValidationProblem(new Dictionary<string, string[]> { [campo] = [mensagem] });

    /// <summary>
    /// Erros do Identity (e-mail duplicado, senha fraca) no mesmo formato de
    /// ValidationProblem que o FluentValidation produz, agrupados pelo campo que
    /// o formulário mostra. Sem isso, um e-mail repetido virava 500.
    /// </summary>
    private static Dictionary<string, string[]> MapearErrosIdentity(IdentityResult resultado)
    {
        var porCampo = new Dictionary<string, List<string>>();

        foreach (var erro in resultado.Errors)
        {
            // UserName carrega o e-mail, então erro de UserName é erro de e-mail.
            var campo = erro.Code.Contains("Password", StringComparison.Ordinal) ? "senha"
                      : erro.Code.Contains("Email", StringComparison.Ordinal) ? "email"
                      : erro.Code.Contains("UserName", StringComparison.Ordinal) ? "email"
                      : "usuario";

            if (!porCampo.TryGetValue(campo, out var lista))
                porCampo[campo] = lista = [];

            lista.Add(TraduzirErroIdentity(erro));
        }

        return porCampo.ToDictionary(p => p.Key, p => p.Value.ToArray());
    }

    private static string TraduzirErroIdentity(IdentityError erro) => erro.Code switch
    {
        "DuplicateEmail" or "DuplicateUserName" => "Já existe um usuário com este e-mail",
        "InvalidEmail" => "E-mail inválido",
        "PasswordTooShort" => "A senha deve ter ao menos 8 caracteres",
        "PasswordRequiresDigit" => "A senha deve conter ao menos um número",
        "PasswordRequiresLower" => "A senha deve conter ao menos uma letra minúscula",
        "PasswordRequiresUpper" => "A senha deve conter ao menos uma letra maiúscula",
        _ => erro.Description,
    };
}

// ── DTOs ──

public record EscritorioVinculoDto(Guid Id, string Nome);

public record UsuarioListaDto(
    Guid Id,
    string Nome,
    string Email,
    string Papel,
    IReadOnlyList<EscritorioVinculoDto> Escritorios,
    bool Ativo,
    bool DeveTrocarSenha,
    DateTime? UltimoLoginEm);

public record CriarUsuarioRequest
{
    public string Nome { get; init; } = string.Empty;
    public string Email { get; init; } = string.Empty;
    public string Senha { get; init; } = string.Empty;
    // String em vez de enum: o frontend envia "EscritorioAdmin" e a API não
    // registra JsonStringEnumConverter (mesmo motivo documentado em AdminEndpoints).
    public string Papel { get; init; } = string.Empty;
    public List<Guid>? Escritorios { get; init; }
}

public record AtualizarUsuarioRequest
{
    public string? Nome { get; init; }
    public string? Papel { get; init; }
    public List<Guid>? Escritorios { get; init; }
}

public record ResetarSenhaRequest(string NovaSenha);

public record AlterarAtivoRequest(bool Ativo);

// ── Validators ──

internal static class RegrasSenha
{
    /// <summary>
    /// Espelha as regras de Identity de Program.cs (mínimo 8, dígito, minúscula
    /// e maiúscula; caractere especial não é exigido). Duplicadas aqui de
    /// propósito: rejeitam antes do round-trip e com mensagem em português.
    /// </summary>
    public static IRuleBuilderOptions<T, string> SenhaForte<T>(this IRuleBuilder<T, string> regra) =>
        regra.NotEmpty().WithMessage("Informe a senha")
             .MinimumLength(8).WithMessage("A senha deve ter ao menos 8 caracteres")
             .Matches("[A-Z]").WithMessage("A senha deve conter ao menos uma letra maiúscula")
             .Matches("[a-z]").WithMessage("A senha deve conter ao menos uma letra minúscula")
             .Matches("[0-9]").WithMessage("A senha deve conter ao menos um número");
}

public class CriarUsuarioRequestValidator : AbstractValidator<CriarUsuarioRequest>
{
    public CriarUsuarioRequestValidator(AppDbContext db)
    {
        RuleFor(x => x.Nome).NotEmpty().WithMessage("Informe o nome").MaximumLength(200);
        RuleFor(x => x.Email).NotEmpty().WithMessage("Informe o e-mail").EmailAddress().MaximumLength(256);
        RuleFor(x => x.Senha).SenhaForte();
        RuleFor(x => x.Papel).NotEmpty().WithMessage("Informe o papel");
        RuleFor(x => x.Escritorios)
            .MustAsync(async (escritorios, ct) =>
            {
                if (escritorios == null || escritorios.Count == 0)
                    return true;
                var distintos = escritorios.Distinct().ToList();
                return await db.Escritorios.IgnoreQueryFilters()
                    .CountAsync(e => distintos.Contains(e.Id), ct) == distintos.Count;
            })
            .WithMessage("Um dos escritórios informados não existe");
    }
}

public class AtualizarUsuarioRequestValidator : AbstractValidator<AtualizarUsuarioRequest>
{
    public AtualizarUsuarioRequestValidator(AppDbContext db)
    {
        RuleFor(x => x.Nome).MaximumLength(200).When(x => x.Nome != null);
        RuleFor(x => x.Escritorios)
            .MustAsync(async (escritorios, ct) =>
            {
                if (escritorios == null || escritorios.Count == 0)
                    return true;
                var distintos = escritorios.Distinct().ToList();
                return await db.Escritorios.IgnoreQueryFilters()
                    .CountAsync(e => distintos.Contains(e.Id), ct) == distintos.Count;
            })
            .WithMessage("Um dos escritórios informados não existe");
    }
}

public class ResetarSenhaRequestValidator : AbstractValidator<ResetarSenhaRequest>
{
    public ResetarSenhaRequestValidator()
    {
        RuleFor(x => x.NovaSenha).SenhaForte();
    }
}
