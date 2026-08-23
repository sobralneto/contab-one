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
        string nome = "Produto Teste", bool ativo = true)
    {
        var produto = new Produto
        {
            Codigo = codigo,
            Nome = nome,
            Descricao = "Produto de teste " + codigo,
            Ativo = ativo,
        };
        db.Produtos.Add(produto);
        db.SaveChanges();
        return produto;
    }

    public static (Agente agente, string chaveCompleta) CriarAgente(
        AppDbContext db, Guid escritorioId, string nome = "Agente Teste",
        string codigoProduto = "nfse")
    {
        var produto = ObterProduto(db, codigoProduto);
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
