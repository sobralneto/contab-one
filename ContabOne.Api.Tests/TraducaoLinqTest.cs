using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// Rede de proteção contra reintrodução de `a.Aberto` (propriedade computada
/// sem coluna) num Where/Any — o defeito que quebrava a finalização de
/// execução com falha e o job diário de alertas com InvalidOperationException.
///
/// ToQueryString() força a compilação da query e a tradução para SQL sem abrir
/// conexão: se o predicado usar algo não-mapeado, a tradução lança e o teste
/// falha. Nenhum banco de pé é necessário.
/// </summary>
public class TraducaoLinqTest
{
    private static AppDbContext CriarContexto()
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseNpgsql("Host=localhost;Database=nao-usado;Username=nao-usado;Password=nao-usado")
            .Options;
        return new AppDbContext(options, new TenantContext());
    }

    [Fact]
    public void PredicadoDeAlertaAberto_TraduzParaSql_SemPropriedadeComputada()
    {
        using var db = CriarContexto();

        // Forma do call site em FinalizarExecucaoAsync (1.1)
        var sql = db.Alertas
            .Where(AlertaExpressoes.Aberto(Guid.NewGuid(), TipoAlerta.ExecucaoFalhou))
            .ToQueryString();

        // A tradução não lançou; o predicado aberto virou filtro na coluna real.
        Assert.Contains("ResolvidoEm", sql);
    }

    [Fact]
    public void PredicadoDeAlertaAbertoComCliente_TraduzParaSql_SemPropriedadeComputada()
    {
        using var db = CriarContexto();

        // Forma do call site em AlertaJob.CriarAlertaSeNaoExiste (1.2), com o
        // clienteId opcional (nulo para alertas de escritório, valor para
        // alertas de certificado).
        var sql = db.Alertas
            .IgnoreQueryFilters()
            .Where(AlertaExpressoes.Aberto(Guid.NewGuid(), TipoAlerta.CertificadoVencido, Guid.NewGuid()))
            .ToQueryString();

        Assert.Contains("ResolvidoEm", sql);
    }

    [Fact]
    public void PredicadoDeAlertaAbertoComClienteNulo_TraduzParaSql()
    {
        using var db = CriarContexto();

        // clienteId nulo (alerta de escritório, ex.: agente silencioso) também
        // precisa traduzir — o `clienteId == null ||` vira parâmetro, não filtro.
        var sql = db.Alertas
            .IgnoreQueryFilters()
            .Where(AlertaExpressoes.Aberto(Guid.NewGuid(), TipoAlerta.AgenteSilencioso, null))
            .ToQueryString();

        Assert.Contains("ResolvidoEm", sql);
    }

    [Fact]
    public void OrderByDeAlertasEndpoints_TraduzParaSql()
    {
        using var db = CriarContexto();

        // Forma do OrderBy de AlertasEndpoints.ListarAsync — o workaround
        // `ResolvidoEm == null` no lugar de `a.Aberto` (que não traduz em
        // OrderBy). Se alguém "simplificar" de volta, a tradução falha aqui.
        var sql = db.Alertas
            .Include(a => a.Cliente)
            .OrderByDescending(a => a.ResolvidoEm == null)
            .ThenByDescending(a => a.CriadoEm)
            .Take(50)
            .ToQueryString();

        Assert.Contains("ResolvidoEm", sql);
        Assert.Contains("LIMIT", sql);
    }

    [Fact]
    public void ListagemDeAgentes_TraduzParaSql()
    {
        using var db = CriarContexto();

        // Forma da projeção de AgentesManagementEndpoints.ListarAsync: o
        // `Ativo` da entidade (propriedade computada) NÃO entra na query — o
        // endpoint projeta `Ativo = a.RevogadoEm == null` e ordena por
        // CriadoEm. Protege o mesmo padrão de Agente.Ativo, mais o ToString()
        // do enum Produto (mesmo risco de tradução do Papel em usuários).
        var sql = db.Agentes
            .Select(a => new
            {
                a.Id,
                a.Nome,
                Produto = a.Produto.ToString(),
                a.ApiKeyPrefixo,
                a.VersaoAgente,
                a.UltimoContatoEm,
                a.CriadoEm,
                Ativo = a.RevogadoEm == null,
                a.RevogadoEm,
                EscritorioNome = a.Escritorio.Nome,
            })
            .OrderByDescending(a => a.CriadoEm)
            .ToQueryString();

        Assert.Contains("RevogadoEm", sql);
        Assert.Contains("Produto", sql);
    }

    [Fact]
    public void ListagemDeUsuarios_TraduzParaSql()
    {
        using var db = CriarContexto();

        // Forma da projeção de UsuariosEndpoints.ListarAsync. Dois pontos que
        // poderiam não traduzir: o ToString() do enum Papel e o acesso à
        // navegação opcional Escritorio (PlatformAdmin não tem escritório).
        var sql = db.Users
            .Where(u => u.EscritorioId == Guid.NewGuid())
            .OrderBy(u => u.Nome)
            .Select(u => new
            {
                u.Id,
                u.Nome,
                u.Email,
                Papel = u.Papel.ToString(),
                u.EscritorioId,
                EscritorioNome = u.Escritorio != null ? u.Escritorio.Nome : null,
                u.Ativo,
                u.DeveTrocarSenha,
                u.UltimoLoginEm,
            })
            .ToQueryString();

        Assert.Contains("DeveTrocarSenha", sql);
        Assert.Contains("LEFT JOIN", sql); // navegação opcional, não INNER
    }

    [Fact]
    public void PaginasVistasDoTour_TraduzParaSql()
    {
        using var db = CriarContexto();

        // Forma de TourEndpoints.ListarVistasAsync. A entidade tem chave
        // composta (UsuarioId, Pagina) e nenhum query filter global — se o
        // mapeamento quebrar, a tradução falha aqui sem precisar de banco.
        var sql = db.TourPaginasVistas
            .Where(t => t.UsuarioId == Guid.NewGuid())
            .Select(t => t.Pagina)
            .ToQueryString();

        Assert.Contains("Pagina", sql);
        Assert.Contains("UsuarioId", sql);
    }

    private static AppDbContext CriarContexto(TenantContext tenant)
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseNpgsql("Host=localhost;Database=nao-usado;Username=nao-usado;Password=nao-usado")
            .Options;
        return new AppDbContext(options, tenant);
    }

    /// <summary>
    /// O sinal "vê todos os escritórios" tem que virar PARÂMETRO na query, não
    /// constante embutida: o TenantContext é mutado depois do AppDbContext
    /// existir (o ApiKeyAuthenticationHandler faz isso no meio do request), e
    /// uma constante congelaria o escopo do primeiro estado visto.
    /// </summary>
    [Fact]
    public void QueryFilter_ParametrizaOSinalDeVerTudo()
    {
        using var db = CriarContexto();
        var sql = db.Clientes.ToQueryString();
        Assert.Contains("@ef_filter__VeTodosOsEscritorios", sql);
    }

    /// <summary>
    /// Tenant não resolvido (o estado exato do bug de fail-open) tem que
    /// produzir "WHERE &lt;falso&gt;" — sem nenhuma comparação de EscritorioId
    /// que pudesse casar com linha alguma.
    /// </summary>
    [Fact]
    public void QueryFilterSemTenant_NaoComparaEscritorioId()
    {
        using var db = CriarContexto();
        var sql = db.Clientes.ToQueryString();

        var where = sql[sql.IndexOf("WHERE", StringComparison.Ordinal)..];
        // Só o parâmetro booleano (falso) sobra no WHERE: o EF descarta o ramo
        // do OR porque EscritorioId nulo não casa com coluna não-nula.
        Assert.DoesNotContain("\"EscritorioId\" =", where);
    }

    [Fact]
    public void QueryFilterComTenantResolvido_ComparaEscritorioId()
    {
        var tenant = new TenantContext();
        tenant.FromUsuario(Guid.NewGuid(), Guid.NewGuid(), "EscritorioAdmin");
        using var db = CriarContexto(tenant);

        var sql = db.Clientes.ToQueryString();
        var where = sql[sql.IndexOf("WHERE", StringComparison.Ordinal)..];
        Assert.Contains("\"EscritorioId\" = @ef_filter__EscritorioId", where);
    }

    [Fact]
    public void QueryFilterDeAdmin_NaoRestringeEscritorio()
    {
        var tenant = new TenantContext();
        tenant.FromAdmin(Guid.NewGuid());
        using var db = CriarContexto(tenant);

        var sql = db.Clientes.ToQueryString();
        var where = sql[sql.IndexOf("WHERE", StringComparison.Ordinal)..];
        Assert.DoesNotContain("\"EscritorioId\" =", where);
        Assert.Contains("VeTodosOsEscritorios0='True'", sql);
    }

    [Fact]
    public void AbertoEmWhere_NaoTraduz_DocumentaPorQueOsGuardasExistem()
    {
        using var db = CriarContexto();

        // Teste negativo: `a.Aberto` num Where é exatamente o defeito que já
        // ocorreu duas vezes (finalização de execução com falha e job de
        // alertas). Se um dia o EF passar a traduzir isso, este teste falha e
        // avisa que os guardas acima podem ser simplificados — de propósito.
        var ex = Assert.Throws<InvalidOperationException>(() =>
            db.Alertas.Where(a => a.Aberto).ToQueryString());

        Assert.Contains("Aberto", ex.Message);
    }
}
