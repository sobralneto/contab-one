using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Seed;

/// <summary>
/// One-time seed endpoints — DEVELOPMENT ONLY.
/// Remove before production deploy.
/// </summary>
public static class SeedEndpoints
{
    public static void MapSeedEndpoints(this WebApplication app)
    {
        // ── Diagnostic: list all users and escritorios (dev only) ──
        app.MapGet("/api/seed/status", async (
            UserManager<Usuario> userManager,
            AppDbContext db,
            IHostEnvironment env) =>
        {
            if (!env.IsDevelopment())
                return Results.NotFound();

            var users = await userManager.Users
                .Select(u => new { u.Email, u.Papel, u.EscritorioId, u.Ativo })
                .ToListAsync();

            // Raw SQL — bypass any EF/UserManager caching
            var rawUsers = await db.Database
                .SqlQueryRaw<RawUser>("SELECT \"Email\", \"UserName\", \"Papel\", \"EscritorioId\", \"Ativo\" FROM \"AspNetUsers\"")
                .ToListAsync();

            var escritorios = await db.Escritorios
                .IgnoreQueryFilters()
                .Select(e => new { e.Id, e.Nome, e.Status })
                .ToListAsync();

            var roles = new List<object>();
            foreach (var u in users)
            {
                var user = await userManager.FindByEmailAsync(u.Email);
                if (user != null)
                    roles.Add(new { u.Email, Roles = await userManager.GetRolesAsync(user) });
            }

            return Results.Ok(new { users, rawUsers, escritorios, roles });
        }).AllowAnonymous();

        // ── PlatformAdmin only ──
        app.MapPost("/api/seed/admin", async (
            SeedAdminRequest req,
            UserManager<Usuario> userManager,
            RoleManager<IdentityRole<Guid>> roleManager,
            IHostEnvironment env) =>
        {
            if (!env.IsDevelopment())
                return Results.NotFound();

            await EnsureRoles(roleManager);

            var user = new Usuario
            {
                UserName = req.Email, // UserName não aceita espaço/acento — o nome humano vai em Nome
                Nome = req.Nome,
                Email = req.Email,
                Papel = PapelUsuario.PlatformAdmin,
                Ativo = true,
                EmailConfirmed = true,
            };

            var result = await userManager.CreateAsync(user, req.Senha);
            if (!result.Succeeded)
                return Results.BadRequest(result.Errors);

            await userManager.AddToRoleAsync(user, "PlatformAdmin");

            return Results.Ok(new { user.Id, user.Email, message = "PlatformAdmin created" });
        }).AllowAnonymous();

        // ── Full dev seed: escritório + 3 usuários ──
        app.MapPost("/api/seed/dev", async (
            UserManager<Usuario> userManager,
            RoleManager<IdentityRole<Guid>> roleManager,
            AppDbContext db,
            IHostEnvironment env) =>
        {
            if (!env.IsDevelopment())
                return Results.NotFound();

            var errors = new List<string>();
            var created = new List<string>();

            await EnsureRoles(roleManager);

            // 1. Create Escritorio (tenant) if not exists
            var escritorio = await db.Escritorios
                .IgnoreQueryFilters()
                .FirstOrDefaultAsync(e => e.Nome == "Contabilidade Silva ME");

            if (escritorio == null)
            {
                escritorio = new Escritorio
                {
                    Nome = "Contabilidade Silva ME",
                    CnpjMascarado = "00.000.***/**00",
                    CnpjHash = "dev-hash",
                    Status = StatusEscritorio.Ativo,
                };
                db.Escritorios.Add(escritorio);
                await db.SaveChangesAsync();
            }

            // Contrata toda ferramenta ativa — mesmo critério do backfill da
            // migration EscritorioProdutoContratado. Sem isto, um escritório
            // de seed criado depois daquela migration nasce sem nenhuma
            // ferramenta contratada, e /api/produtos devolve tudo com
            // `contratado: false`: nenhuma página de ferramenta fica
            // alcançável, nem pelo seletor de chave de agente.
            var idsAtivos = await db.Produtos.Where(p => p.Ativo).Select(p => p.Id).ToListAsync();
            var jaContratados = await db.EscritorioProdutos
                .IgnoreQueryFilters()
                .Where(ep => ep.EscritorioId == escritorio.Id && ep.DesabilitadoEm == null)
                .Select(ep => ep.ProdutoId)
                .ToListAsync();
            foreach (var produtoId in idsAtivos.Except(jaContratados))
            {
                db.EscritorioProdutos.Add(new EscritorioProduto
                {
                    EscritorioId = escritorio.Id,
                    ProdutoId = produtoId,
                });
            }
            await db.SaveChangesAsync();

            // 2. PlatformAdmin
            var admin = await userManager.FindByEmailAsync("admin@nfse.local");
            if (admin == null)
            {
                admin = new Usuario { UserName = "admin", Nome = "Admin da Plataforma", Email = "admin@nfse.local", Papel = PapelUsuario.PlatformAdmin, EscritorioId = null, Ativo = true, EmailConfirmed = true };
                var r = await userManager.CreateAsync(admin, "Admin123!");
                if (r.Succeeded) { await userManager.AddToRoleAsync(admin, "PlatformAdmin"); created.Add("PlatformAdmin: admin@nfse.local / Admin123!"); }
                else errors.AddRange(r.Errors.Select(e => $"admin: {e.Description}"));
            }

            // 3. EscritorioAdmin
            var escAdmin = await userManager.FindByEmailAsync("escritorio@nfse.local");
            if (escAdmin == null)
            {
                escAdmin = new Usuario { UserName = "escritorio", Nome = "Admin do Escritório", Email = "escritorio@nfse.local", Papel = PapelUsuario.EscritorioAdmin, EscritorioId = escritorio.Id, Ativo = true, EmailConfirmed = true };
                var r = await userManager.CreateAsync(escAdmin, "Admin123!");
                if (r.Succeeded) { await userManager.AddToRoleAsync(escAdmin, "EscritorioAdmin"); created.Add("EscritorioAdmin: escritorio@nfse.local / Admin123!"); }
                else errors.AddRange(r.Errors.Select(e => $"escritorio: {e.Description}"));
            }

            // 4. EscritorioUsuario
            var escUser = await userManager.FindByEmailAsync("usuario@nfse.local");
            if (escUser == null)
            {
                escUser = new Usuario { UserName = "usuario", Nome = "Usuário do Escritório", Email = "usuario@nfse.local", Papel = PapelUsuario.EscritorioUsuario, EscritorioId = escritorio.Id, Ativo = true, EmailConfirmed = true };
                var r = await userManager.CreateAsync(escUser, "Admin123!");
                if (r.Succeeded) { await userManager.AddToRoleAsync(escUser, "EscritorioUsuario"); created.Add("EscritorioUsuario: usuario@nfse.local / Admin123!"); }
                else errors.AddRange(r.Errors.Select(e => $"usuario: {e.Description}"));
            }

            return Results.Ok(new
            {
                message = errors.Count == 0 ? "Dev seed complete" : "Dev seed completed with errors",
                escritorio = escritorio.Nome,
                usuarios = created,
                erros = errors,
            });
        }).AllowAnonymous();
    }

    private static async Task EnsureRoles(RoleManager<IdentityRole<Guid>> roleManager)
    {
        foreach (var role in new[] { "PlatformAdmin", "EscritorioAdmin", "EscritorioUsuario" })
        {
            if (!await roleManager.RoleExistsAsync(role))
                await roleManager.CreateAsync(new IdentityRole<Guid>(role));
        }
    }
}

public record SeedAdminRequest(string Nome, string Email, string Senha);

// Used by raw SQL query in status endpoint
public class RawUser
{
    public string Email { get; set; } = string.Empty;
    public string UserName { get; set; } = string.Empty;
    public int Papel { get; set; }
    public Guid? EscritorioId { get; set; }
    public bool Ativo { get; set; }
}
