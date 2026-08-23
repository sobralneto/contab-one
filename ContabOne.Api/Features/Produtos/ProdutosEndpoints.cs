using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Produtos;

/// <summary>
/// Ferramentas do hub que o escritório da requisição CONTRATOU — é o que
/// alimenta o seletor da tela de agentes. O catálogo completo e o cadastro
/// ficam em /api/admin/produtos (só PlatformAdmin).
///
/// Só devolve produto ativo e habilitado: quem consome isto está escolhendo
/// ferramenta para uma chave NOVA. Agente já existente exibe o próprio produto
/// pelo que vem na listagem de agentes, então desabilitar uma ferramenta não
/// apaga da tela quem já a usa.
/// </summary>
public static class ProdutosEndpoints
{
    public static RouteGroupBuilder MapProdutosEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/", ListarAsync);
        return group;
    }

    private static async Task<IResult> ListarAsync(
        AppDbContext db,
        TenantContext tenant,
        Guid? escritorioId = null)
    {
        // O escopo NUNCA vem da query string para usuário de escritório —
        // seria IDOR (§5). O parâmetro só é honrado para PlatformAdmin, que
        // legitimamente gera chave em nome de outro escritório.
        var escopo = tenant.IsAdmin ? escritorioId : tenant.EscritorioId;

        // Admin sem escritório escolhido ainda não tem o que filtrar: devolve
        // o catálogo ativo, e a criação da chave é quem recusa ferramenta não
        // contratada, com o motivo.
        if (escopo == null)
        {
            if (!tenant.IsAdmin)
                return Results.Ok(Array.Empty<object>());

            var catalogo = await db.Produtos
                .Where(p => p.Ativo)
                .OrderBy(p => p.Ordem).ThenBy(p => p.Nome)
                .Select(p => new { p.Id, p.Codigo, p.Nome, p.Descricao, p.Ativo, p.Ordem })
                .ToListAsync();

            return Results.Ok(catalogo);
        }

        var produtos = await db.EscritorioProdutos
            .IgnoreQueryFilters() // escopo já resolvido acima, sem confiar na query string
            .Where(ep => ep.EscritorioId == escopo && ep.DesabilitadoEm == null && ep.Produto.Ativo)
            .OrderBy(ep => ep.Produto.Ordem).ThenBy(ep => ep.Produto.Nome)
            .Select(ep => new
            {
                ep.Produto.Id,
                ep.Produto.Codigo,
                ep.Produto.Nome,
                ep.Produto.Descricao,
                ep.Produto.Ativo,
                ep.Produto.Ordem,
            })
            .ToListAsync();

        return Results.Ok(produtos);
    }
}
