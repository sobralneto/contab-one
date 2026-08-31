using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Infra;

namespace ContabOne.Api.Features.Produtos;

/// <summary>
/// Catálogo de ferramentas que a sessão enxerga — alimenta o seletor da tela
/// de agentes E a navegação (menu e hub) do frontend. O cadastro do catálogo
/// fica em /api/admin/produtos (só PlatformAdmin).
///
/// Só devolve produto ativo: quem consome isto está escolhendo ferramenta
/// para uma chave nova ou montando a navegação da sessão. Agente já existente
/// exibe o próprio produto pelo que vem na listagem de agentes, então
/// desativar uma ferramenta não apaga da tela quem já a usa.
///
/// Sempre o catálogo ativo INTEIRO, nunca só o contratado — a navegação
/// precisa saber que uma ferramenta existe para mostrá-la como indisponível
/// no hub (card informativo, sem ação), e o seletor de chave de agente filtra
/// pela flag `contratado` no próprio frontend. Sem escopo resolvido (admin
/// sem escritório em foco), tudo vem como não contratado.
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
        // seria IDOR (§5). O parâmetro só é honrado para PlatformAdmin SEM foco;
        // com foco, o admin é escopado ao escritório em foco como qualquer outro.
        var escopo = tenant.EscritorioId ?? (tenant.VeTodosOsEscritorios ? escritorioId : null);

        var catalogo = await db.Produtos
            .Where(p => p.Ativo)
            .OrderBy(p => p.Dominio.Ordem).ThenBy(p => p.Ordem).ThenBy(p => p.Nome)
            .Select(p => new
            {
                p.Id,
                p.Codigo,
                p.Nome,
                p.Descricao,
                p.Ativo,
                p.TemAgente,
                p.Ordem,
                p.Paginas,
                Dominio = new { p.Dominio.Codigo, p.Dominio.Nome, p.Dominio.Ordem, p.Dominio.Icone },
            })
            .ToListAsync();

        // Sem escopo resolvido (admin ainda não escolheu escritório): nada
        // para marcar como contratado — quem decide contratação é a tela de
        // Escritórios, não esta listagem.
        var contratados = escopo == null
            ? []
            : await db.EscritorioProdutos
                .IgnoreQueryFilters() // escopo já resolvido acima, sem confiar na query string
                .Where(ep => ep.EscritorioId == escopo && ep.DesabilitadoEm == null)
                .Select(ep => ep.ProdutoId)
                .ToListAsync();

        var resultado = catalogo.Select(p => new
        {
            p.Id,
            p.Codigo,
            p.Nome,
            p.Descricao,
            p.Ativo,
            p.TemAgente,
            p.Ordem,
            p.Paginas,
            p.Dominio,
            Contratado = contratados.Contains(p.Id),
        });

        return Results.Ok(resultado);
    }
}
