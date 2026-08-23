using System.Text.Json;
using FluentValidation;
using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Security;

namespace ContabOne.Api.Features.Agent;

public static class AgentEndpoints
{
    public static RouteGroupBuilder MapAgentEndpoints(this RouteGroupBuilder group)
    {
        group.MapPost("/handshake", HandshakeAsync);
        group.MapGet("/regras", RegrasAsync);
        group.MapPost("/execucoes", AbrirExecucaoAsync);
        group.MapPost("/execucoes/{id:guid}/metricas", EnviarMetricasAsync);
        group.MapPost("/execucoes/{id:guid}/finalizar", FinalizarExecucaoAsync);
        group.MapPost("/clientes", UpsertClientesAsync);
        return group;
    }

    // ── Guards ──

    /// <summary>
    /// Devolve (escritorioId, agenteId) se ambos estiverem resolvidos no
    /// TenantContext; senão devolve 403 com explicação. Substitui os
    /// tenant.AgenteId!.Value / tenant.EscritorioId!.Value que antes produziam
    /// 500 — proteção por exceção não é proteção (design D4).
    /// </summary>
    private static (Guid escritorioId, Guid agenteId)? ResolverIdsDoAgente(TenantContext tenant)
    {
        if (tenant.EscritorioId.HasValue && tenant.AgenteId.HasValue)
            return (tenant.EscritorioId.Value, tenant.AgenteId.Value);
        return null;
    }

    // ── Handshake (§6.1) ──

    private static async Task<IResult> HandshakeAsync(
        HandshakeRequest req,
        AppDbContext db,
        TenantContext tenant,
        IConfiguration config,
        HttpContext httpContext)
    {
        var ids = ResolverIdsDoAgente(tenant);
        if (ids == null) return Results.Forbid();
        var (escritorioId, agenteId) = ids.Value;

        var escritorio = await db.Escritorios
            .IgnoreQueryFilters()
            .Include(e => e.Plano)
            .FirstOrDefaultAsync(e => e.Id == escritorioId);

        if (escritorio == null)
            return Results.NotFound();

        // Update agent version and last contact
        var agente = await db.Agentes
            .IgnoreQueryFilters()
            .FirstOrDefaultAsync(a => a.Id == agenteId);

        if (agente != null && req.VersaoAgente != null)
        {
            agente.VersaoAgente = req.VersaoAgente;
            await db.SaveChangesAsync();
        }

        // Get current rules version
        var regraAtiva = await db.RegraColetas
            .Where(r => r.Ativa)
            .OrderByDescending(r => r.Versao)
            .FirstOrDefaultAsync();

        // Configuração do escritório — dicionário cru {chave: valor}, aditivo
        // por natureza: agente antigo ignora o bloco, agente novo conhece as
        // chaves que conhece (design.md, Decisão 5). Vazio quando nada salvo.
        var configuracao = await db.ConfiguracoesEscritorio
            .Where(c => c.EscritorioId == escritorioId)
            .ToDictionaryAsync(c => c.Chave, c => c.Valor);

        // Cifrada com a chave derivada da própria API key deste request —
        // ver ConfiguracaoCipher. O header já foi validado por
        // ApiKeyAuthenticationHandler antes de chegar aqui.
        var apiKeyBruta = httpContext.Request.Headers["X-Api-Key"].ToString();
        var configuracaoCifrada = ConfiguracaoCipher.Cifrar(apiKeyBruta, configuracao);

        var podeExecutar = escritorio.Status == StatusEscritorio.Ativo;
        var plano = escritorio.Plano;

        var mensagem = escritorio.Status switch
        {
            StatusEscritorio.Inadimplente => "Assinatura suspensa por inadimplência. Regularize para continuar.",
            StatusEscritorio.Suspenso => "Conta suspensa. Entre em contato com o suporte.",
            StatusEscritorio.Cancelado => "Conta cancelada.",
            _ => null
        };

        return Results.Ok(new HandshakeResponse
        {
            Escritorio = new EscritorioInfo
            {
                Id = escritorio.Id,
                Nome = escritorio.Nome,
            },
            Status = escritorio.Status.ToString(),
            PodeExecutar = podeExecutar,
            Mensagem = mensagem,
            Plano = plano != null ? new PlanoInfo
            {
                MaxClientes = plano.MaxClientes,
                PermiteEmitidas = plano.PermiteEmitidas,
            } : null,
            RegrasVersaoAtual = regraAtiva?.Versao ?? 0,
            AgenteVersaoMinima = "2.0.0",
            HmacCnpjKey = config["HMAC_CNPJ_KEY"]!, // same for all agents of this escritorio (§PLANO_SAAS_AGENTE §6)
            ConfiguracaoCifrada = configuracaoCifrada,
        });
    }

    // ── Rules bundle (§6.1 / §8) ──

    private static async Task<IResult> RegrasAsync(
        int? versao,
        AppDbContext db)
    {
        var regraAtiva = await db.RegraColetas
            .Where(r => r.Ativa)
            .OrderByDescending(r => r.Versao)
            .FirstOrDefaultAsync();

        if (regraAtiva == null)
            return Results.NotFound(new { erro = "Nenhuma regra publicada" });

        if (versao.HasValue && versao.Value >= regraAtiva.Versao)
            return Results.StatusCode(304); // Not Modified

        return Results.Ok(new RegrasResponse
        {
            Versao = regraAtiva.Versao,
            PublicadaEm = regraAtiva.PublicadaEm,
            Conteudo = JsonSerializer.Deserialize<JsonElement>(regraAtiva.Conteudo),
        });
    }

    // ── Status do escritório (§6.1) — HandshakeAsync já informa isso ao agente,
    // mas os endpoints de escrita não devem confiar só no agente respeitar a flag ──

    private static async Task<bool> EscritorioEstaAtivoAsync(AppDbContext db, TenantContext tenant)
    {
        if (!tenant.EscritorioId.HasValue)
            return false;

        var status = await db.Escritorios
            .IgnoreQueryFilters()
            .Where(e => e.Id == tenant.EscritorioId.Value)
            .Select(e => e.Status)
            .FirstOrDefaultAsync();

        return status == StatusEscritorio.Ativo;
    }

    // ── Execution tracking (§6.1) ──

    private static async Task<IResult> AbrirExecucaoAsync(
        AbrirExecucaoRequest req,
        AppDbContext db,
        TenantContext tenant)
    {
        var ids = ResolverIdsDoAgente(tenant);
        if (ids == null) return Results.Forbid();
        var (escritorioId, agenteId) = ids.Value;

        if (!await EscritorioEstaAtivoAsync(db, tenant))
            return Results.Forbid();

        var execucao = new Execucao
        {
            Id = Guid.NewGuid(),
            EscritorioId = escritorioId,
            AgenteId = agenteId,
            IniciadoEm = DateTime.UtcNow,
            VersaoAgente = req.VersaoAgente,
            Status = StatusExecucao.Sucesso, // default, updated at finalizar
        };

        db.Execucoes.Add(execucao);
        await db.SaveChangesAsync();

        return Results.Ok(new { execucaoId = execucao.Id });
    }

    private static async Task<IResult> EnviarMetricasAsync(
        Guid id,
        EnviarMetricasRequest req,
        AppDbContext db,
        TenantContext tenant)
    {
        var ids = ResolverIdsDoAgente(tenant);
        if (ids == null) return Results.Forbid();
        var (escritorioId, _) = ids.Value;

        if (!await EscritorioEstaAtivoAsync(db, tenant))
            return Results.Forbid();

        var execucao = await db.Execucoes
            .FirstOrDefaultAsync(e => e.Id == id);

        if (execucao == null)
            return Results.NotFound();

        var metricas = req.Metricas ?? [];

        // Só aceita métricas referenciando clientes DO PRÓPRIO escritório: o
        // agente só conhece ids que recebeu no próprio upsert, então uma linha
        // com cliente de outro tenant é dado corrompido (ou tentativa de
        // vazar) — descartada silenciosamente, no mesmo espírito do agente,
        // que pula códigos sem id mapeado (api_client._traduzir_metricas).
        var clientesDoTenant = await db.Clientes
            .Where(c => c.EscritorioId == escritorioId)
            .Select(c => c.Id)
            .ToHashSetAsync();

        // Upsert: (ClienteId, Competencia, Tipo) → upsert not insert (§PLANO_SAAS_AGENTE §10)
        foreach (var m in metricas)
        {
            if (!clientesDoTenant.Contains(m.ClienteId))
                continue;
            // Find or create the metric by key
            var existente = await db.ExecucaoMetricas
                .FirstOrDefaultAsync(em =>
                    em.ExecucaoId == id &&
                    em.ClienteId == m.ClienteId &&
                    em.Competencia == m.Competencia &&
                    em.Tipo == m.Tipo);

            if (existente != null)
            {
                existente.QtdBaixadas = m.QtdBaixadas;
                existente.QtdPuladas = m.QtdPuladas;
                existente.QtdFalhas = m.QtdFalhas;
                existente.DuracaoMs = m.DuracaoMs;
            }
            else
            {
                db.ExecucaoMetricas.Add(new ExecucaoMetrica
                {
                    ExecucaoId = id,
                    ClienteId = m.ClienteId,
                    Competencia = m.Competencia,
                    Tipo = m.Tipo,
                    QtdBaixadas = m.QtdBaixadas,
                    QtdPuladas = m.QtdPuladas,
                    QtdFalhas = m.QtdFalhas,
                    DuracaoMs = m.DuracaoMs,
                });
            }
        }

        await db.SaveChangesAsync();
        return Results.Ok(new { recebidas = metricas.Count });
    }

    private static async Task<IResult> FinalizarExecucaoAsync(
        Guid id,
        FinalizarExecucaoRequest req,
        AppDbContext db,
        TenantContext tenant)
    {
        var ids = ResolverIdsDoAgente(tenant);
        if (ids == null) return Results.Forbid();
        var (escritorioId, _) = ids.Value;

        if (!await EscritorioEstaAtivoAsync(db, tenant))
            return Results.Forbid();

        var execucao = await db.Execucoes
            .Include(e => e.Metricas)
            .FirstOrDefaultAsync(e => e.Id == id);

        if (execucao == null)
            return Results.NotFound();

        execucao.Status = req.Status;
        execucao.MensagemErro = req.MensagemErro;
        execucao.FinalizadoEm = DateTime.UtcNow;
        await db.SaveChangesAsync();

        // Check for alerts: failed execution
        if (req.Status == StatusExecucao.Falha)
        {
            var jaExiste = await db.Alertas
                .AnyAsync(AlertaExpressoes.Aberto(escritorioId, TipoAlerta.ExecucaoFalhou));

            if (!jaExiste)
            {
                db.Alertas.Add(new Alerta
                {
                    EscritorioId = escritorioId,
                    Tipo = TipoAlerta.ExecucaoFalhou,
                    Severidade = SeveridadeAlerta.Critico,
                    Mensagem = $"Execução {id} falhou: {req.MensagemErro?.Truncate(500) ?? "sem detalhes"}",
                });
                await db.SaveChangesAsync();
            }
        }

        return Results.Ok(new { status = execucao.Status.ToString() });
    }

    // ── Client upsert (§6.1 / PLANO_SAAS_AGENTE §6) ──

    private static async Task<IResult> UpsertClientesAsync(
        UpsertClientesRequest req,
        AppDbContext db,
        TenantContext tenant)
    {
        var ids = ResolverIdsDoAgente(tenant);
        if (ids == null) return Results.Forbid();
        var (escritorioId, _) = ids.Value;

        if (!await EscritorioEstaAtivoAsync(db, tenant))
            return Results.Forbid();

        var atualizados = 0;
        var novos = 0;
        var limitados = 0;
        var clientes = req.Clientes ?? [];
        // codigo → Cliente.Id: the agent only knows the local "codigo" (from the
        // .pfx filename); it has no way to learn the server-assigned Guid other
        // than reading it back here. Without this map, POST /execucoes/{id}/metricas
        // can't be built at all (ExecucaoMetrica.ClienteId is FK-enforced against
        // Cliente.Id) — see PLANO_SAAS_AGENTE.md §5/§6.
        var mapeamento = new List<ClienteIdMapeado>();

        var plano = await db.Escritorios
            .Where(e => e.Id == escritorioId)
            .Select(e => e.Plano)
            .FirstOrDefaultAsync();
        var totalAtual = await db.Clientes.CountAsync();

        foreach (var c in clientes)
        {
            var existente = await db.Clientes
                .FirstOrDefaultAsync(cl =>
                    cl.EscritorioId == escritorioId &&
                    cl.Codigo == c.Codigo);

            if (existente != null)
            {
                existente.Nome = c.Nome;
                existente.CnpjMascarado = c.CnpjMascarado;
                existente.CnpjHash = c.CnpjHash;
                existente.CertificadoValidade = c.CertificadoValidade;
                existente.CertificadoNomeArquivo = c.CertificadoNomeArquivo;
                existente.AtualizadoEm = DateTime.UtcNow;
                existente.Origem = OrigemCliente.Agente;
                atualizados++;
                mapeamento.Add(new ClienteIdMapeado(existente.Codigo, existente.Id));
            }
            else if (plano != null && totalAtual + novos >= plano.MaxClientes)
            {
                // Limite de clientes do plano atingido — novos códigos são ignorados
                // (clientes já existentes continuam sendo atualizados normalmente).
                limitados++;
            }
            else
            {
                var novo = new Cliente
                {
                    EscritorioId = escritorioId,
                    Codigo = c.Codigo,
                    Nome = c.Nome,
                    CnpjMascarado = c.CnpjMascarado,
                    CnpjHash = c.CnpjHash,
                    CertificadoValidade = c.CertificadoValidade,
                    CertificadoNomeArquivo = c.CertificadoNomeArquivo,
                    Origem = OrigemCliente.Agente,
                    PrimeiraVezVistoEm = DateTime.UtcNow,
                };
                db.Clientes.Add(novo);
                novos++;
                mapeamento.Add(new ClienteIdMapeado(novo.Codigo, novo.Id));
            }
        }

        await db.SaveChangesAsync();

        return Results.Ok(new { atualizados, novos, limitados, clientes = mapeamento });
    }
}

// ── Helper ──

file static class StringExtensions
{
    public static string Truncate(this string value, int maxLength)
        => value.Length <= maxLength ? value : value[..maxLength];
}

// ── DTOs ──

public record HandshakeRequest
{
    public string? VersaoAgente { get; init; }
    public int RegrasVersaoLocal { get; init; }
    public string? So { get; init; }
}

public record HandshakeResponse
{
    public EscritorioInfo Escritorio { get; init; } = null!;
    public string Status { get; init; } = string.Empty;
    public bool PodeExecutar { get; init; }
    public string? Mensagem { get; init; }
    public PlanoInfo? Plano { get; init; }
    public int RegrasVersaoAtual { get; init; }
    public string AgenteVersaoMinima { get; init; } = "2.0.0";
    public string HmacCnpjKey { get; init; } = string.Empty;
    public string ConfiguracaoCifrada { get; init; } = string.Empty;
}

public record EscritorioInfo
{
    public Guid Id { get; init; }
    public string Nome { get; init; } = string.Empty;
}

public record PlanoInfo
{
    public int MaxClientes { get; init; }
    public bool PermiteEmitidas { get; init; }
}

public record RegrasResponse
{
    public int Versao { get; init; }
    public DateTime PublicadaEm { get; init; }
    public JsonElement Conteudo { get; init; }
}

public record AbrirExecucaoRequest
{
    public string? VersaoAgente { get; init; }
}

public record MetricaRequest
{
    public Guid ClienteId { get; init; }
    public TipoNota Tipo { get; init; }
    public string Competencia { get; init; } = string.Empty;
    public int QtdBaixadas { get; init; }
    public int QtdPuladas { get; init; }
    public int QtdFalhas { get; init; }
    public long DuracaoMs { get; init; }
}

public record FinalizarExecucaoRequest
{
    public StatusExecucao Status { get; init; }
    public string? MensagemErro { get; init; }
}

public record ClienteAgentRequest
{
    public string Codigo { get; init; } = string.Empty;
    public string Nome { get; init; } = string.Empty;
    public string CnpjMascarado { get; init; } = string.Empty;
    public string CnpjHash { get; init; } = string.Empty;
    public DateOnly? CertificadoValidade { get; init; }
    public string? CertificadoNomeArquivo { get; init; }
}

// Wrapper records for list parameters (required by System.Text.Json source-gen in minimal APIs)
public record UpsertClientesRequest(List<ClienteAgentRequest> Clientes);
public record EnviarMetricasRequest(List<MetricaRequest> Metricas);

public record ClienteIdMapeado(string Codigo, Guid Id);
