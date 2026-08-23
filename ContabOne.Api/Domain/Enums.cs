namespace ContabOne.Api.Domain;

public enum StatusEscritorio
{
    Ativo,
    Inadimplente,
    Suspenso,
    Cancelado
}

public enum PapelUsuario
{
    PlatformAdmin,
    EscritorioAdmin,
    EscritorioUsuario
}

/// <summary>
/// Ferramenta do hub que a chave de API habilita. O nome de cada valor, em
/// minúsculas, É o prefixo da chave (`nfse_…`, `det_…`) — ver
/// <see cref="Security.ApiKeyHasher"/>. Duas consequências ao adicionar um
/// produto: o nome não pode conter `_` (o parser da chave separa por `_`) e
/// não pode colidir, em minúsculas, com outro valor. HashersTest tranca as
/// duas regras.
///
/// A ordem importa: `Nfse` é 0 porque é o valor gravado nas linhas que já
/// existiam quando a coluna foi criada.
/// </summary>
public enum Produto
{
    Nfse,
    Det
}

public enum TipoNota
{
    Recebidas,
    Emitidas
}

public enum StatusExecucao
{
    Sucesso,
    Parcial,
    Falha
}

public enum OrigemCliente
{
    Manual,
    Agente
}

public enum TipoAlerta
{
    CertificadoVencendo,
    CertificadoVencido,
    ExecucaoFalhou,
    AgenteSilencioso
}

public enum SeveridadeAlerta
{
    Info,
    Atencao,
    Critico
}
