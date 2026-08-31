using FluentValidation;
using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Security;

namespace ContabOne.Api.Features.Clientes;

public static class ClientesEndpoints
{
    public static RouteGroupBuilder MapClientesEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/", ListarAsync);
        group.MapGet("/proximo-codigo", ProximoCodigoAsync);
        group.MapPost("/", CriarAsync);
        group.MapPut("/{id:guid}", AtualizarAsync);
        group.MapDelete("/{id:guid}", ExcluirAsync);
        return group;
    }

    /// <summary>
    /// Deriva hash e máscara do CNPJ cru quando informado — o hash é HMAC com
    /// segredo que só o servidor tem, então quem cadastra não consegue
    /// calculá-lo sozinho. Sem CNPJ cru, preserva o que veio pronto no
    /// request (compatibilidade com o cadastro atual, que só envia a máscara).
    /// </summary>
    private static (string mascarado, string hash) DerivarCnpj(
        string? cnpjCru, string? mascaradoAtual, string? hashAtual, IConfiguration config)
    {
        if (string.IsNullOrWhiteSpace(cnpjCru))
            return (mascaradoAtual ?? string.Empty, hashAtual ?? string.Empty);

        var limpo = CnpjHasher.Limpar(cnpjCru);
        if (limpo.Length != 14)
            return (mascaradoAtual ?? string.Empty, hashAtual ?? string.Empty);

        var hmacKey = config["HMAC_CNPJ_KEY"]!;
        return (CnpjHasher.Mascarar(limpo), CnpjHasher.Hash(limpo, hmacKey));
    }

    private static async Task<IResult> ProximoCodigoAsync(
        Guid? escritorioId,
        AppDbContext db,
        TenantContext tenant)
    {
        var escopo = tenant.IsAdmin ? escritorioId : tenant.EscritorioId;
        if (escopo == null)
            return Results.BadRequest(new { erro = "Escritório é obrigatório" });

        var codigosUsados = (await db.Clientes
                .Where(c => c.EscritorioId == escopo)
                .Select(c => c.Codigo)
                .ToListAsync())
            .Where(c => c.Length == 4 && c.All(char.IsDigit))
            .Select(int.Parse)
            .ToHashSet();

        var proximo = 1;
        while (codigosUsados.Contains(proximo))
            proximo++;

        return Results.Ok(new { codigo = proximo.ToString("D4") });
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
        TenantContext tenant,
        IConfiguration config)
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

        var (cnpjMascarado, cnpjHash) = DerivarCnpj(req.Cnpj, req.CnpjMascarado, req.CnpjHash, config);

        // Origem "Importacao" só quando o próprio caller pede — o cadastro
        // manual pela tela continua Manual mesmo informando CNPJ cru agora.
        var origem = string.Equals(req.Origem, nameof(OrigemCliente.Importacao), StringComparison.OrdinalIgnoreCase)
            ? OrigemCliente.Importacao
            : OrigemCliente.Manual;

        var cliente = new Cliente
        {
            EscritorioId = escritorioId,
            Codigo = req.Codigo,
            Nome = req.Nome,
            CnpjMascarado = cnpjMascarado,
            CnpjHash = cnpjHash,
            CertificadoValidade = req.CertificadoValidade,
            Origem = origem,
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
        TenantContext tenant,
        IConfiguration config)
    {
        var validation = await validator.ValidateAsync(req);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        var cliente = await db.Clientes.FindAsync(id);
        if (cliente == null)
            return Results.NotFound();

        cliente.Nome = req.Nome;
        var (cnpjMascarado, cnpjHash) = DerivarCnpj(req.Cnpj, req.CnpjMascarado, req.CnpjHash, config);
        if (!string.IsNullOrEmpty(cnpjMascarado))
            cliente.CnpjMascarado = cnpjMascarado;
        if (!string.IsNullOrEmpty(cnpjHash))
            cliente.CnpjHash = cnpjHash;
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

    /// <summary>
    /// CNPJ completo, opcional. Quando informado, hash e máscara são
    /// derivados no servidor e o valor cru é descartado — nunca persistido.
    /// Ganha prioridade sobre <see cref="CnpjMascarado"/>/<see cref="CnpjHash"/>.
    /// </summary>
    public string? Cnpj { get; init; }
    public string? CnpjMascarado { get; init; }
    public string? CnpjHash { get; init; }
    public DateOnly? CertificadoValidade { get; init; }
    public Guid? EscritorioId { get; init; }

    /// <summary>"Importacao" quando o cliente nasce da importação de um documento; qualquer outro valor (ou ausência) é Manual.</summary>
    public string? Origem { get; init; }
}

public class ClienteRequestValidator : AbstractValidator<ClienteRequest>
{
    public ClienteRequestValidator()
    {
        RuleFor(x => x.Codigo).NotEmpty().MaximumLength(20);
        RuleFor(x => x.Nome).NotEmpty().MaximumLength(200);
        RuleFor(x => x.Cnpj)
            .Must(c => string.IsNullOrWhiteSpace(c) || CnpjHasher.Limpar(c).Length == 14)
            .WithMessage("CNPJ deve ter 14 dígitos");
    }
}
