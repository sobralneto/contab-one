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

    public static (Agente agente, string chaveCompleta) CriarAgente(
        AppDbContext db, Guid escritorioId, string nome = "Agente Teste",
        Produto produto = Produto.Nfse)
    {
        var (chave, prefixo, hash) = ApiKeyHasher.Gerar(produto);
        var agente = new Agente
        {
            EscritorioId = escritorioId,
            Nome = nome,
            Produto = produto,
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
