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
