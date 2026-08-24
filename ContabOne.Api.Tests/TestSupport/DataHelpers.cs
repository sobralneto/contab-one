using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;
using ContabOne.Api.Infra;
using ContabOne.Api.Security;

namespace ContabOne.Api.Tests.TestSupport;

/// <summary>
/// Criação de dados de teste direto no AppDbContext (mais rápido e mais
/// explícito que montar pelos endpoints). O que interessa testar é o
/// comportamento dos endpoints; o setup vai direto ao banco do container.
/// </summary>
public static class DataHelpers
{
    public static Plano CriarPlano(AppDbContext db, string nome = "Plano Teste",
        int maxClientes = 100, int maxAgentes = 10, bool permiteEmitidas = true)
    {
        var plano = new Plano
        {
            Nome = nome,
            MaxClientes = maxClientes,
            MaxAgentes = maxAgentes,
            PermiteEmitidas = permiteEmitidas,
            PrecoMensal = 100m,
        };
        db.Planos.Add(plano);
        db.SaveChanges();
        return plano;
    }

    public static Escritorio CriarEscritorio(AppDbContext db, string nome = "Escritório Teste",
        Plano? plano = null)
    {
        var esc = new Escritorio
        {
            Nome = nome,
            CnpjMascarado = "00.000.***/**00",
            CnpjHash = $"manual-{Guid.NewGuid():N}",
            Status = StatusEscritorio.Ativo,
            PlanoId = plano?.Id,
        };
        db.Escritorios.Add(esc);
        db.SaveChanges();
        return esc;
    }

    /// <summary>
    /// Produto do catalogo semeado pela migration ProdutosComoTabela
    /// ("nfse", "det"). Os testes usam o seed em vez de criar produto proprio:
    /// o indice unico de Codigo e global e o container e compartilhado pela
    /// colecao inteira.
    /// </summary>
    public static Produto ObterProduto(AppDbContext db, string codigo = "nfse")
        => db.Produtos.First(p => p.Codigo == codigo);

    public static Produto CriarProduto(AppDbContext db, string codigo,
        string nome = "Produto Teste", bool ativo = true, string dominioCodigo = "fiscal")
    {
        var produto = new Produto
        {
            Codigo = codigo,
            Nome = nome,
            Descricao = "Produto de teste " + codigo,
            DominioCodigo = dominioCodigo,
            Paginas = [.. PaginaFerramenta.Todas],
            Ativo = ativo,
        };
        db.Produtos.Add(produto);
        db.SaveChanges();
        return produto;
    }

    /// <summary>
    /// Habilita a ferramenta para o escritorio (idempotente). Reabilitar
    /// reaproveita a linha, como o endpoint de admin faz.
    /// </summary>
    public static EscritorioProduto HabilitarProduto(AppDbContext db, Guid escritorioId, Guid produtoId)
    {
        var vinculo = db.EscritorioProdutos.IgnoreQueryFilters()
            .FirstOrDefault(ep => ep.EscritorioId == escritorioId && ep.ProdutoId == produtoId);

        if (vinculo == null)
        {
            vinculo = new EscritorioProduto { EscritorioId = escritorioId, ProdutoId = produtoId };
            db.EscritorioProdutos.Add(vinculo);
        }
        else
        {
            vinculo.DesabilitadoEm = null;
        }

        db.SaveChanges();
        return vinculo;
    }

    public static void DesabilitarProduto(AppDbContext db, Guid escritorioId, Guid produtoId)
    {
        var vinculo = db.EscritorioProdutos.IgnoreQueryFilters()
            .First(ep => ep.EscritorioId == escritorioId && ep.ProdutoId == produtoId);
        vinculo.DesabilitadoEm = DateTime.UtcNow;
        db.SaveChanges();
    }

    /// <summary>
    /// Cria o agente E habilita a ferramenta para o escritorio: ter agente de
    /// um produto implica ter o produto, e sem isso todo teste que so queria
    /// um agente esbarraria no gate comercial. Quem TESTA o gate desabilita
    /// explicitamente depois, com DesabilitarProduto.
    /// </summary>
    public static (Agente agente, string chaveCompleta) CriarAgente(
        AppDbContext db, Guid escritorioId, string nome = "Agente Teste",
        string codigoProduto = "nfse")
    {
        var produto = ObterProduto(db, codigoProduto);
        HabilitarProduto(db, escritorioId, produto.Id);
        var (chave, prefixo, hash) = ApiKeyHasher.Gerar(produto.Codigo);
        var agente = new Agente
        {
            EscritorioId = escritorioId,
            Nome = nome,
            ProdutoId = produto.Id,
            ApiKeyHash = hash,
            ApiKeyPrefixo = prefixo,
        };
        db.Agentes.Add(agente);
        db.SaveChanges();
        return (agente, chave);
    }

    public static Cliente CriarCliente(AppDbContext db, Guid escritorioId,
        string codigo = "0001", string nome = "Cliente Teste")
    {
        var cliente = new Cliente
        {
            EscritorioId = escritorioId,
            Codigo = codigo,
            Nome = nome,
            CnpjMascarado = "54.283.***/**26",
            CnpjHash = "hash-teste",
            Origem = OrigemCliente.Agente,
        };
        db.Clientes.Add(cliente);
        db.SaveChanges();
        return cliente;
    }
}
