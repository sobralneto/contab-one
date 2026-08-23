using FluentValidation;
using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Clientes;

public static class ClientesEndpoints
{
    public static RouteGroupBuilder MapClientesEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/", ListarAsync);
        group.MapPost("/", CriarAsync);
        group.MapPut("/{id:guid}", AtualizarAsync);
        group.MapDelete("/{id:guid}", ExcluirAsync);
        return group;
    }

    private static async Task<IResult> ListarAsync(
        string? busca,
        Guid? escritorioId,
        int? diasVencimentoCert,
        int pagina = 1,
        int tamanho = 20,
        AppDbContext db = null!)
    {
        tamanho = Math.Clamp(tamanho, 1, 100);
        var query = db.Clientes.AsQueryable();

        if (!string.IsNullOrEmpty(busca))
        {
            query = query.Where(c =>
                c.Nome.Contains(busca) ||
                c.Codigo.Contains(busca) ||
                c.CnpjMascarado.Contains(busca));
        }

        // Admin filtra por escritório; escritório/usuário já são escopados pelos
        // query filters globais, mas aceitar o parâmetro é inofensivo (nada além
        // do próprio tenancy é retornado).
        if (escritorioId.HasValue)
            query = query.Where(c => c.EscritorioId == escritorioId.Value);

        if (diasVencimentoCert.HasValue && diasVencimentoCert.Value > 0)
        {
            var hoje = DateOnly.FromDateTime(DateTime.UtcNow);
            var limite = hoje.AddDays(diasVencimentoCert.Value);
            query = query.Where(c =>
                c.CertificadoValidade != null &&
                c.CertificadoValidade >= hoje &&
                c.CertificadoValidade <= limite);
        }

        var total = await query.CountAsync();
        var clientes = await query
            .OrderBy(c => c.Nome)
            .Skip((pagina - 1) * tamanho)
            .Take(tamanho)
            .Select(c => new ClienteDto
            {
                Id = c.Id,
                Codigo = c.Codigo,
                Nome = c.Nome,
                CnpjMascarado = c.CnpjMascarado,
                CertificadoValidade = c.CertificadoValidade,
                CertificadoNomeArquivo = c.CertificadoNomeArquivo,
                EscritorioNome = c.Escritorio.Nome,
                Origem = c.Origem.ToString(),
                AtualizadoEm = c.AtualizadoEm,
            })
            .ToListAsync();

        return Results.Ok(new { total, pagina, tamanho, dados = clientes });
    }

    private static async Task<IResult> CriarAsync(
        ClienteRequest req,
        IValidator<ClienteRequest> validator,
        AppDbContext db,
        TenantContext tenant)
    {
        var validation = await validator.ValidateAsync(req);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        // Admin (sem escritório próprio) precisa indicar o escritório de destino;
        // escritório/usuário são vinculados ao próprio tenancy.
        Guid escritorioId;
        if (tenant.IsAdmin)
        {
            if (!req.EscritorioId.HasValue)
                return Results.ValidationProblem(new Dictionary<string, string[]>
                {
                    ["escritorioId"] = ["Escritório é obrigatório para cadastro pelo admin"],
                });
            escritorioId = req.EscritorioId.Value;
        }
        else
        {
            escritorioId = tenant.EscritorioId!.Value;
        }

        var jaExiste = await db.Clientes
            .AnyAsync(c => c.EscritorioId == escritorioId && c.Codigo == req.Codigo);

        if (jaExiste)
            return Results.Conflict(new { erro = "Código já existe para este escritório" });

        var plano = await db.Escritorios
            .Where(e => e.Id == escritorioId)
            .Select(e => e.Plano)
            .FirstOrDefaultAsync();

        if (plano != null && await db.Clientes.CountAsync(c => c.EscritorioId == escritorioId) >= plano.MaxClientes)
            return Results.BadRequest(new { erro = "Limite de clientes do plano atingido" });

        var cliente = new Cliente
        {
            EscritorioId = escritorioId,
            Codigo = req.Codigo,
            Nome = req.Nome,
            CnpjMascarado = req.CnpjMascarado ?? string.Empty,
            CnpjHash = req.CnpjHash ?? string.Empty,
            CertificadoValidade = req.CertificadoValidade,
            Origem = OrigemCliente.Manual,
        };

        db.Clientes.Add(cliente);
        await db.SaveChangesAsync();

        return Results.Created($"/api/clientes/{cliente.Id}", new { cliente.Id });
    }

    private static async Task<IResult> AtualizarAsync(
        Guid id,
        ClienteRequest req,
        IValidator<ClienteRequest> validator,
        AppDbContext db,
        TenantContext tenant)
    {
        var validation = await validator.ValidateAsync(req);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        var cliente = await db.Clientes.FindAsync(id);
        if (cliente == null)
            return Results.NotFound();

        cliente.Nome = req.Nome;
        if (!string.IsNullOrEmpty(req.CnpjMascarado))
            cliente.CnpjMascarado = req.CnpjMascarado;
        if (!string.IsNullOrEmpty(req.CnpjHash))
            cliente.CnpjHash = req.CnpjHash;
        cliente.CertificadoValidade = req.CertificadoValidade;
        cliente.AtualizadoEm = DateTime.UtcNow;

        await db.SaveChangesAsync();
        return Results.Ok(new { cliente.Id });
    }

    private static async Task<IResult> ExcluirAsync(
        Guid id,
        AppDbContext db)
    {
        var cliente = await db.Clientes.FindAsync(id);
        if (cliente == null)
            return Results.NotFound();

        db.Clientes.Remove(cliente);
        await db.SaveChangesAsync();
        return Results.NoContent();
    }
}

// ── DTOs ──

public record ClienteDto
{
    public Guid Id { get; init; }
    public string Codigo { get; init; } = string.Empty;
    public string Nome { get; init; } = string.Empty;
    public string CnpjMascarado { get; init; } = string.Empty;
    public DateOnly? CertificadoValidade { get; init; }
    public string? CertificadoNomeArquivo { get; init; }
    public string? EscritorioNome { get; init; }
    public string Origem { get; init; } = string.Empty;
    public DateTime AtualizadoEm { get; init; }
}

public record ClienteRequest
{
    public string Codigo { get; init; } = string.Empty;
    public string Nome { get; init; } = string.Empty;
    public string? CnpjMascarado { get; init; }
    public string? CnpjHash { get; init; }
    public DateOnly? CertificadoValidade { get; init; }
    public Guid? EscritorioId { get; init; }
}

public class ClienteRequestValidator : AbstractValidator<ClienteRequest>
{
    public ClienteRequestValidator()
    {
        RuleFor(x => x.Codigo).NotEmpty().MaximumLength(20);
        RuleFor(x => x.Nome).NotEmpty().MaximumLength(200);
    }
}
