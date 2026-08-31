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
    Agente,

    /// <summary>
    /// Cliente identificado/cadastrado a partir da importação de um documento
    /// (ex.: PGDAS-D). Acrescentado ao fim: o enum é persistido como inteiro,
    /// e reordenar reescreveria o significado das linhas já gravadas.
    /// </summary>
    Importacao,
}

/// <summary>Leiaute do documento do PGDAS-D — o extrator trata os dois.</summary>
public enum TipoDocumentoPgdas
{
    /// <summary>Tributos na seção "6) Informações sobre DAS", valor na mesma linha do rótulo.</summary>
    Extrato,

    /// <summary>Tributos na seção "2.8) Total Geral da Empresa", valor na linha seguinte ao cabeçalho.</summary>
    Declaracao,
}

/// <summary>Categoria fiscal da receita segregada (seção do PGDAS-D).</summary>
public enum CategoriaReceita
{
    Tributado,
    TributadoMonofasico,
    ComSt,
    ComStMonofasico,
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
