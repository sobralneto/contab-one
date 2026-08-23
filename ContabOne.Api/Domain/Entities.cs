using Microsoft.AspNetCore.Identity;

namespace ContabOne.Api.Domain;

// ── Tenancy ──

public class Escritorio
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Nome { get; set; } = string.Empty;
    public string CnpjMascarado { get; set; } = string.Empty;
    public string CnpjHash { get; set; } = string.Empty;
    public Guid? PlanoId { get; set; }
    public Plano? Plano { get; set; }
    public StatusEscritorio Status { get; set; } = StatusEscritorio.Ativo;
    public DateTime CriadoEm { get; set; } = DateTime.UtcNow;
    public DateTime AtualizadoEm { get; set; } = DateTime.UtcNow;

    public ICollection<Usuario> Usuarios { get; set; } = [];
    public ICollection<Agente> Agentes { get; set; } = [];
    public ICollection<Cliente> Clientes { get; set; } = [];
    public ICollection<Execucao> Execucoes { get; set; } = [];
    public ICollection<ConfiguracaoEscritorio> Configuracoes { get; set; } = [];
    public ICollection<Alerta> Alertas { get; set; } = [];
}

public class Plano
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Nome { get; set; } = string.Empty;
    public int MaxClientes { get; set; }
    public int MaxAgentes { get; set; }
    public bool PermiteEmitidas { get; set; }
    public decimal PrecoMensal { get; set; }

    public ICollection<Escritorio> Escritorios { get; set; } = [];
}

// ── Identity ──

public class Usuario : IdentityUser<Guid>
{
    // Nome de exibição próprio, separado de UserName: o Identity valida
    // UserName contra AllowedUserNameCharacters (alfanumérico + "-._@+"), o
    // que rejeita espaço e acento — "João Silva" seria recusado. UserName
    // passa a receber o e-mail (único por construção) e o nome humano vive aqui.
    public string Nome { get; set; } = string.Empty;
    public Guid? EscritorioId { get; set; }
    public Escritorio? Escritorio { get; set; }
    public PapelUsuario Papel { get; set; } = PapelUsuario.EscritorioUsuario;
    public DateTime? UltimoLoginEm { get; set; }
    public bool Ativo { get; set; } = true;
    // Ligado quando um admin cria o usuário ou reseta a senha dele: o guard do
    // frontend prende a navegação na tela de troca até ser desligado.
    public bool DeveTrocarSenha { get; set; }
}

/// <summary>
/// Registro de que um usuário já viu a explicação de uma página. Uma linha por
/// página (e não um booleano de "tour concluído") porque a explicação é por
/// tela: quem entra em Clientes hoje e em Agentes só semana que vem precisa ver
/// cada uma na sua primeira visita.
/// </summary>
public class TourPaginaVista
{
    public Guid UsuarioId { get; set; }
    public Usuario Usuario { get; set; } = null!;
    /// <summary>Nome da rota no vue-router (ex.: "clientes").</summary>
    public string Pagina { get; set; } = string.Empty;
    public DateTime VistoEm { get; set; } = DateTime.UtcNow;
}

// ── Agent ──

public class Agente
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid EscritorioId { get; set; }
    public Escritorio Escritorio { get; set; } = null!;
    public string Nome { get; set; } = string.Empty;
    public string ApiKeyHash { get; set; } = string.Empty;
    public string ApiKeyPrefixo { get; set; } = string.Empty;
    public string? VersaoAgente { get; set; }
    public DateTime? UltimoContatoEm { get; set; }
    public DateTime CriadoEm { get; set; } = DateTime.UtcNow;
    public DateTime? RevogadoEm { get; set; }

    public bool Ativo => RevogadoEm == null;
}

// ── Cliente (certificate owner) ──

public class Cliente
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid EscritorioId { get; set; }
    public Escritorio Escritorio { get; set; } = null!;
    public string Codigo { get; set; } = string.Empty;
    public string Nome { get; set; } = string.Empty;
    public string CnpjMascarado { get; set; } = string.Empty;
    public string CnpjHash { get; set; } = string.Empty;
    public DateOnly? CertificadoValidade { get; set; }
    public string? CertificadoNomeArquivo { get; set; }
    public DateTime PrimeiraVezVistoEm { get; set; } = DateTime.UtcNow;
    public DateTime AtualizadoEm { get; set; } = DateTime.UtcNow;
    public OrigemCliente Origem { get; set; } = OrigemCliente.Agente;
}

// ── Execution tracking ──

public class Execucao
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid EscritorioId { get; set; }
    public Escritorio Escritorio { get; set; } = null!;
    public Guid AgenteId { get; set; }
    public Agente Agente { get; set; } = null!;
    public DateTime IniciadoEm { get; set; } = DateTime.UtcNow;
    public DateTime? FinalizadoEm { get; set; }
    public StatusExecucao Status { get; set; } = StatusExecucao.Sucesso;
    public string? VersaoAgente { get; set; }
    public string? MensagemErro { get; set; }

    public ICollection<ExecucaoMetrica> Metricas { get; set; } = [];
}

public class ExecucaoMetrica
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid ExecucaoId { get; set; }
    public Execucao Execucao { get; set; } = null!;
    public Guid ClienteId { get; set; }
    public Cliente Cliente { get; set; } = null!;
    public TipoNota Tipo { get; set; }
    public string Competencia { get; set; } = string.Empty; // "2026-06"
    public int QtdBaixadas { get; set; }
    public int QtdPuladas { get; set; }
    public int QtdFalhas { get; set; }
    public long DuracaoMs { get; set; }
}

// ── Remote rules bundle ──

public class RegraColeta
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public int Versao { get; set; }
    public string Conteudo { get; set; } = "{}"; // jsonb
    public DateTime PublicadaEm { get; set; } = DateTime.UtcNow;
    public bool Ativa { get; set; } = false;
}

// ── Per-tenant config ──

public class ConfiguracaoEscritorio
{
    public Guid EscritorioId { get; set; }
    public Escritorio Escritorio { get; set; } = null!;
    public string Chave { get; set; } = string.Empty;
    public string Valor { get; set; } = string.Empty;
}

// ── Alerts ──

public class Alerta
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid EscritorioId { get; set; }
    public Escritorio Escritorio { get; set; } = null!;
    public Guid? ClienteId { get; set; }
    public Cliente? Cliente { get; set; }
    public TipoAlerta Tipo { get; set; }
    public SeveridadeAlerta Severidade { get; set; } = SeveridadeAlerta.Info;
    public string Mensagem { get; set; } = string.Empty;
    public DateTime CriadoEm { get; set; } = DateTime.UtcNow;
    public DateTime? ResolvidoEm { get; set; }

    public bool Aberto => ResolvidoEm == null;
}
