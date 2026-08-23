using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Produtos;

/// <summary>
/// Catálogo de ferramentas do hub, em leitura, para qualquer usuário
/// autenticado — é o que alimenta o seletor da tela de agentes. O cadastro
/// vive em /api/admin/produtos (só PlatformAdmin).
///
/// Só devolve produtos ativos: quem consome isto está escolhendo produto para
/// uma chave NOVA. Agentes já existentes exibem o próprio produto pelo que
/// vem na listagem de agentes, então um produto desativado não some da tela
/// de quem já o usa.
/// </summary>
public static class ProdutosEndpoints
{
    public static RouteGroupBuilder MapProdutosEndpoints(this RouteGroupBuilder group)
    {
        group.MapGet("/", ListarAsync);
        return group;
    }

    private static async Task<IResult> ListarAsync(AppDbContext db)
    {
        var produtos = await db.Produtos
            .Where(p => p.Ativo)
            .OrderBy(p => p.Ordem).ThenBy(p => p.Nome)
            .Select(p => new
            {
                p.Id,
                p.Codigo,
                p.Nome,
                p.Descricao,
                p.Ativo,
                p.Ordem,
            })
            .ToListAsync();

        return Results.Ok(produtos);
    }
}
