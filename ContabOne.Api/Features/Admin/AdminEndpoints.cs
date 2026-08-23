using System.Security.Claims;
using System.Text.Json;
using FluentValidation;
using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Security;

namespace ContabOne.Api.Features.Admin;

public static class AdminEndpoints
{
    public static RouteGroupBuilder MapAdminEndpoints(this RouteGroupBuilder group)
    {
        // Escritórios
        group.MapGet("/escritorios", ListarEscritoriosAsync);
        group.MapGet("/escritorios/{id:guid}", ObterEscritorioAsync);
        group.MapPost("/escritorios", CriarEscritorioAsync);
        group.MapPut("/escritorios/{id:guid}", AtualizarEscritorioAsync);

        // Planos
        group.MapGet("/planos", ListarPlanosAsync);
        group.MapPost("/planos", CriarPlanoAsync);
        group.MapPut("/planos/{id:guid}", AtualizarPlanoAsync);

        // Regras
        group.MapGet("/regras", ListarRegrasAsync);
        group.MapGet("/regras/{id:guid}", ObterRegraAsync);
        group.MapPost("/regras", CriarRegraAsync);

        // Visão geral
        group.MapGet("/visao-geral", VisaoGeralAsync);

        return group;
    }

    // ── Escritórios ──

    private static async Task<IResult> ListarEscritoriosAsync(AppDbContext db)
    {
        var escritorios = await db.Escritorios
            .IgnoreQueryFilters()
            .Include(e => e.Plano)
            .OrderBy(e => e.Nome)
            .Select(e => new
            {
                e.Id,
                e.Nome,
                e.CnpjMascarado,
                Status = e.Status.ToString(), // frontend espera string (o agente envia inteiros no protocolo dele)
                e.PlanoId,
                PlanoNome = e.Plano != null ? e.Plano.Nome : null,
                e.CriadoEm,
                totalClientes = e.Clientes.Count,
                totalAgentes = e.Agentes.Count(a => a.RevogadoEm == null),
            })
            .ToListAsync();

        return Results.Ok(escritorios);
    }

    private static async Task<IResult> ObterEscritorioAsync(
        Guid id,
        AppDbContext db)
    {
        var escritorio = await db.Escritorios
            .IgnoreQueryFilters()
            .Include(e => e.Plano)
            .FirstOrDefaultAsync(e => e.Id == id);

        if (escritorio == null)
            return Results.NotFound();

        return Results.Ok(new
        {
            escritorio.Id,
            escritorio.Nome,
            escritorio.CnpjMascarado,
            Status = escritorio.Status.ToString(),
            escritorio.PlanoId,
            PlanoNome = escritorio.Plano?.Nome,
            escritorio.CriadoEm,
            totalClientes = escritorio.Clientes.Count,
            totalAgentes = escritorio.Agentes.Count(a => a.RevogadoEm == null),
        });
    }

    private static async Task<IResult> CriarEscritorioAsync(
        CriarEscritorioRequest req,
        IValidator<CriarEscritorioRequest> validator,
        AppDbContext db)
    {
        var validation = await validator.ValidateAsync(req);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        // Cadastro manual não gera hash HMAC (só o agente gera). Sem CNPJ, um
        // valor único evita violar o índice único de CnpjHash ("" colidiria).
        var cnpjHash = !string.IsNullOrWhiteSpace(req.CnpjHash)
            ? req.CnpjHash
            : $"manual-{Guid.NewGuid():N}";

        var status = StatusEscritorio.Ativo;
        if (!string.IsNullOrEmpty(req.Status))
            Enum.TryParse<StatusEscritorio>(req.Status, true, out status);

        var escritorio = new Escritorio
        {
            Nome = req.Nome,
            CnpjMascarado = req.CnpjMascarado ?? string.Empty,
            CnpjHash = cnpjHash,
            PlanoId = req.PlanoId,
            Status = status,
        };

        db.Escritorios.Add(escritorio);
        await db.SaveChangesAsync();

        return Results.Created($"/api/admin/escritorios/{escritorio.Id}",
            new { escritorio.Id, escritorio.Nome });
    }

    private static async Task<IResult> AtualizarEscritorioAsync(
        Guid id,
        AtualizarEscritorioRequest req,
        IValidator<AtualizarEscritorioRequest> validator,
        AppDbContext db,
        ILogger<Program> logger,
        ClaimsPrincipal admin)
    {
        var validation = await validator.ValidateAsync(req);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        var escritorio = await db.Escritorios
            .IgnoreQueryFilters()
            .FirstOrDefaultAsync(e => e.Id == id);

        if (escritorio == null)
            return Results.NotFound();

        if (!string.IsNullOrEmpty(req.Nome))
            escritorio.Nome = req.Nome;
        if (!string.IsNullOrEmpty(req.CnpjMascarado))
            escritorio.CnpjMascarado = req.CnpjMascarado;
        if (!string.IsNullOrEmpty(req.CnpjHash))
            escritorio.CnpjHash = req.CnpjHash;
        if (req.PlanoId.HasValue)
            escritorio.PlanoId = req.PlanoId;
        if (!string.IsNullOrEmpty(req.Status) &&
            Enum.TryParse<StatusEscritorio>(req.Status, true, out var novoStatus) &&
            novoStatus != escritorio.Status)
        {
            logger.LogInformation(
                "Escritorio {EscritorioId} status alterado de {StatusAnterior} para {StatusNovo} por admin {AdminId}",
                escritorio.Id, escritorio.Status, novoStatus,
                admin.FindFirstValue(ClaimTypes.NameIdentifier));
            escritorio.Status = novoStatus;
        }

        escritorio.AtualizadoEm = DateTime.UtcNow;
        await db.SaveChangesAsync();

        return Results.Ok(new { escritorio.Id, Status = escritorio.Status.ToString() });
    }

    // ── Planos ──

    private static async Task<IResult> ListarPlanosAsync(AppDbContext db)
    {
        var planos = await db.Planos.OrderBy(p => p.Nome).ToListAsync();
        return Results.Ok(planos);
    }

    private static async Task<IResult> CriarPlanoAsync(
        PlanoRequest req,
        IValidator<PlanoRequest> validator,
        AppDbContext db)
    {
        var validation = await validator.ValidateAsync(req);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        var plano = new Plano
        {
            Nome = req.Nome,
            MaxClientes = req.MaxClientes,
            MaxAgentes = req.MaxAgentes,
            PermiteEmitidas = req.PermiteEmitidas,
            PrecoMensal = req.PrecoMensal,
        };

        db.Planos.Add(plano);
        await db.SaveChangesAsync();
        return Results.Created($"/api/admin/planos/{plano.Id}", plano);
    }

    private static async Task<IResult> AtualizarPlanoAsync(
        Guid id,
        PlanoRequest req,
        IValidator<PlanoRequest> validator,
        AppDbContext db)
    {
        var validation = await validator.ValidateAsync(req);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        var plano = await db.Planos.FindAsync(id);
        if (plano == null)
            return Results.NotFound();

        plano.Nome = req.Nome;
        plano.MaxClientes = req.MaxClientes;
        plano.MaxAgentes = req.MaxAgentes;
        plano.PermiteEmitidas = req.PermiteEmitidas;
        plano.PrecoMensal = req.PrecoMensal;

        await db.SaveChangesAsync();
        return Results.Ok(plano);
    }

    // ── Regras (§8) ──

    private static async Task<IResult> ListarRegrasAsync(AppDbContext db)
    {
        var regras = await db.RegraColetas
            .OrderByDescending(r => r.Versao)
            .ToListAsync();

        var resultado = regras.Select(r => new
        {
            r.Id,
            r.Versao,
            r.PublicadaEm,
            r.Ativa,
            tamanhoConteudo = r.Conteudo?.Length ?? 0,
        });

        return Results.Ok(resultado);
    }

    private static async Task<IResult> ObterRegraAsync(
        Guid id,
        AppDbContext db)
    {
        var regra = await db.RegraColetas
            .FirstOrDefaultAsync(r => r.Id == id);

        if (regra == null)
            return Results.NotFound();

        return Results.Ok(new RegraDetalheDto(
            regra.Id,
            regra.Versao,
            regra.PublicadaEm,
            regra.Ativa,
            regra.Conteudo?.Length ?? 0,
            regra.Conteudo ?? "{}"));
    }

    private static async Task<IResult> CriarRegraAsync(
        PublicarRegraRequest req,
        AppDbContext db)
    {
        // Portão de usabilidade, não fronteira de segurança: o agente continua
        // sendo a autoridade (regras.validar_bundle rejeita e preserva a versão
        // anterior). Sem este gate, qualquer JSON bem-formado era publicado e
        // silenciosamente rejeitado por todos os agentes no próximo handshake.
        var erros = RegraColetaValidator.Validar(req.Conteudo);
        if (erros.Count > 0)
            return Results.ValidationProblem(new Dictionary<string, string[]>
            {
                ["conteudo"] = erros.ToArray(),
            });

        // Deactivate current active rule
        var ativas = await db.RegraColetas
            .Where(r => r.Ativa)
            .ToListAsync();

        foreach (var r in ativas)
            r.Ativa = false;

        // Numeração sobre TODAS as versões, não só as ativas: um rollback fora do
        // endpoint (desativar a vN na mão) faria a próxima publicação reutilizar
        // um número já existente e violar o índice único.
        var novaVersao = (await db.RegraColetas.MaxAsync(r => (int?)r.Versao) ?? 0) + 1;

        var nova = new RegraColeta
        {
            Versao = novaVersao,
            Conteudo = req.Conteudo,
            PublicadaEm = DateTime.UtcNow,
            Ativa = true,
        };

        db.RegraColetas.Add(nova);
        await db.SaveChangesAsync();

        return Results.Created($"/api/admin/regras/{nova.Id}",
            new { nova.Id, nova.Versao, nova.PublicadaEm });
    }

    // ── Visão geral ──

    private static async Task<IResult> VisaoGeralAsync(AppDbContext db)
    {
        var trintaDiasAtras = DateTime.UtcNow.AddDays(-30);

        var totalEscritorios = await db.Escritorios.IgnoreQueryFilters().CountAsync();
        var totalAtivos = await db.Escritorios.IgnoreQueryFilters()
            .CountAsync(e => e.Status == StatusEscritorio.Ativo);

        var execucoesRecentes = await db.Execucoes
            .IgnoreQueryFilters()
            .Where(e => e.IniciadoEm >= trintaDiasAtras)
            .CountAsync();

        var escritoriosComAtividade = await db.Execucoes
            .IgnoreQueryFilters()
            .Where(e => e.IniciadoEm >= trintaDiasAtras)
            .Select(e => e.EscritorioId)
            .Distinct()
            .CountAsync();

        return Results.Ok(new
        {
            totalEscritorios,
            totalAtivos,
            execucoesUltimos30d = execucoesRecentes,
            escritoriosAtivos30d = escritoriosComAtividade,
        });
    }
}

// ── DTOs ──

public record CriarEscritorioRequest
{
    public string Nome { get; init; } = string.Empty;
    public string? CnpjMascarado { get; init; }
    public string? CnpjHash { get; init; }
    public Guid? PlanoId { get; init; }
    // String em vez de enum: o frontend envia "Ativo"/"Suspenso" (sem JsonStringEnumConverter)
    public string? Status { get; init; }
}

public class CriarEscritorioRequestValidator : AbstractValidator<CriarEscritorioRequest>
{
    public CriarEscritorioRequestValidator(AppDbContext db)
    {
        RuleFor(x => x.Nome).NotEmpty().MaximumLength(200);
        RuleFor(x => x.PlanoId)
            .MustAsync(async (planoId, ct) => !planoId.HasValue || await db.Planos.AnyAsync(p => p.Id == planoId.Value, ct))
            .WithMessage("PlanoId informado não existe");
    }
}

public record AtualizarEscritorioRequest
{
    public string? Nome { get; init; }
    public string? CnpjMascarado { get; init; }
    public string? CnpjHash { get; init; }
    public Guid? PlanoId { get; init; }
    // String em vez de enum: o frontend envia "Ativo"/"Suspenso"... e o
    // protocolo sem JsonStringEnumConverter rejeitaria string → enum.
    public string? Status { get; init; }
}

public class AtualizarEscritorioRequestValidator : AbstractValidator<AtualizarEscritorioRequest>
{
    public AtualizarEscritorioRequestValidator(AppDbContext db)
    {
        RuleFor(x => x.Nome).MaximumLength(200).When(x => x.Nome != null);
        RuleFor(x => x.PlanoId)
            .MustAsync(async (planoId, ct) => !planoId.HasValue || await db.Planos.AnyAsync(p => p.Id == planoId.Value, ct))
            .WithMessage("PlanoId informado não existe");
    }
}

public record PlanoRequest
{
    public string Nome { get; init; } = string.Empty;
    public int MaxClientes { get; init; }
    public int MaxAgentes { get; init; }
    public bool PermiteEmitidas { get; init; }
    public decimal PrecoMensal { get; init; }
}

public class PlanoRequestValidator : AbstractValidator<PlanoRequest>
{
    public PlanoRequestValidator()
    {
        RuleFor(x => x.Nome).NotEmpty().MaximumLength(100);
        RuleFor(x => x.MaxClientes).GreaterThanOrEqualTo(0);
        RuleFor(x => x.MaxAgentes).GreaterThanOrEqualTo(0);
        RuleFor(x => x.PrecoMensal).GreaterThanOrEqualTo(0);
    }
}

public record PublicarRegraRequest
{
    public string Conteudo { get; init; } = "{}";
}

public record RegraDetalheDto(
    Guid Id,
    int Versao,
    DateTime PublicadaEm,
    bool Ativa,
    int TamanhoConteudo,
    string Conteudo);
