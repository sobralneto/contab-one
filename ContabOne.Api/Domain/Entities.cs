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
    public ICollection<EscritorioProduto> Produtos { get; set; } = [];
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

/// <summary>
/// Departamento do escritório contábil que a ferramenta atende (Fiscal, DP,
/// Contábil, …). Dado, não enum: cadastrar domínio novo não exige deploy do
/// frontend, que agrupa o menu e o hub a partir do catálogo.
/// </summary>
public class Dominio
{
    /// <summary>Chave natural, curta e estável (`fiscal`, `dp`, `contabil`).</summary>
    public string Codigo { get; set; } = string.Empty;

    /// <summary>
    /// Nome único usado em todo lugar — menu, hub e cadastro. Não existe nome
    /// curto separado: se um domínio algum dia precisar de dois, é quando
    /// essa coluna se justifica, não antes.
    /// </summary>
    public string Nome { get; set; } = string.Empty;

    public int Ordem { get; set; }

    /// <summary>Nome de um ícone do mapa do frontend; desconhecido cai no genérico.</summary>
    public string? Icone { get; set; }

    public ICollection<Produto> Produtos { get; set; } = [];
}

/// <summary>
/// Página que uma ferramenta pode declarar ter. Conjunto fechado de
/// propósito: cada valor corresponde a um componente que existe no
/// frontend, então aceitar valor arbitrário só produziria item de menu que
/// leva a lugar nenhum.
///
/// Clientes e Agentes NÃO entram aqui: as duas telas mostram dado do
/// escritório inteiro (Cliente e Agente não são particionados por produto
/// no banco — Agente até tem <see cref="Agente.ProdutoId"/>, mas a listagem
/// é uma tabela só, com o produto como coluna, não uma tela por produto).
/// Vivem em rotas transversais (`/clientes`, `/agentes`), fora de
/// `/f/:produto/…`.
/// </summary>
public static class PaginaFerramenta
{
    public const string VisaoGeral = "visao-geral";
    public const string Execucoes = "execucoes";
    public const string Configuracao = "configuracao";

    /// <summary>
    /// Cadastro do pacote de regras que os agentes baixam para conversar com
    /// o portal da ferramenta. Só o NFS-e declara hoje — é específico do
    /// Portal Nacional, sem equivalente ainda em outra ferramenta — e é
    /// restrita a PlatformAdmin, mais estrita que Configuração/Execuções
    /// (que EscritorioAdmin também acessa): publicar uma versão quebrada
    /// afeta a coleta de todos os escritórios de uma vez.
    /// </summary>
    public const string Regras = "regras";

    public static readonly IReadOnlyCollection<string> Todas =
        [VisaoGeral, Execucoes, Configuracao, Regras];

    public static bool Valida(string? pagina) => pagina != null && Todas.Contains(pagina);
}

/// <summary>
/// Ferramenta do hub (coleta de NFS-e, DET, …). Cada agente em campo pertence
/// a exatamente uma, e a chave de API dele começa pelo <see cref="Codigo"/>
/// deste produto.
///
/// O catálogo é dado, não código: cadastrar um produto aqui não exige deploy.
/// O que o cadastro NÃO faz é criar a ferramenta — binário do agente,
/// endpoints e bloco de configuração do handshake continuam sendo código.
/// </summary>
public class Produto
{
    public Guid Id { get; set; } = Guid.NewGuid();

    /// <summary>
    /// Primeiro campo da chave de API (`nfse_a1b2c3d4_…`). **Imutável depois
    /// de criado**: ele já foi impresso nas chaves que estão nos config.toml
    /// dos clientes, e o handler compara a chave apresentada contra ele.
    /// Trocá-lo derruba todos os agentes deste produto de uma vez — por isso
    /// o endpoint de atualização não expõe este campo.
    /// </summary>
    public string Codigo { get; set; } = string.Empty;

    public string Nome { get; set; } = string.Empty;
    public string Descricao { get; set; } = string.Empty;

    /// <summary>Departamento do escritório contábil que esta ferramenta atende.</summary>
    public string DominioCodigo { get; set; } = string.Empty;
    public Dominio Dominio { get; set; } = null!;

    /// <summary>
    /// Subconjunto de <see cref="PaginaFerramenta.Todas"/> que esta ferramenta
    /// oferece. O submenu e as rotas do frontend são derivados daqui — página
    /// não declarada não aparece no menu e não é alcançável pelo endereço.
    /// </summary>
    public string[] Paginas { get; set; } = [];

    /// <summary>
    /// Controla apenas a OFERTA de novas chaves. Agente já em campo com um
    /// produto inativo continua autenticando: desativar é decisão comercial,
    /// não revogação — para cortar acesso existe revogar a chave do agente.
    /// </summary>
    public bool Ativo { get; set; } = true;

    public int Ordem { get; set; }
    public DateTime CriadoEm { get; set; } = DateTime.UtcNow;

    public ICollection<Agente> Agentes { get; set; } = [];
    public ICollection<EscritorioProduto> Escritorios { get; set; } = [];
}

/// <summary>
/// Quais ferramentas do hub um escritorio contratou. Sem uma linha habilitada
/// aqui o escritorio nao gera chave para o produto, e os agentes que ele ja
/// tenha daquele produto param no handshake.
///
/// Isso e gate comercial deliberado, da mesma familia de
/// <see cref="Escritorio.Status"/> — que ja bloqueia o agente no mesmo ponto.
/// Nao confundir com o catalogo <see cref="Produto"/>, esse sim mantido fora
/// do caminho de autenticacao de proposito.
///
/// Desabilitar e reversivel e preserva historico (<see cref="DesabilitadoEm"/>
/// em vez de apagar a linha), no mesmo espirito de Agente.RevogadoEm.
/// </summary>
public class EscritorioProduto
{
    public Guid EscritorioId { get; set; }
    public Escritorio Escritorio { get; set; } = null!;
    public Guid ProdutoId { get; set; }
    public Produto Produto { get; set; } = null!;

    public DateTime HabilitadoEm { get; set; } = DateTime.UtcNow;
    public DateTime? DesabilitadoEm { get; set; }

    /// <summary>
    /// Propriedade computada, SEM coluna: nao use em Where/OrderBy — o EF nao
    /// traduz e lanca em runtime (o mesmo defeito que Agente.Ativo ja causou
    /// duas vezes). Nas queries escreva `DesabilitadoEm == null`.
    /// </summary>
    public bool Habilitado => DesabilitadoEm == null;
}

/// <summary>
/// Regra do <see cref="Produto.Codigo"/>. Vive fora da entidade porque tanto o
/// validador do endpoint quanto os testes precisam dela.
/// </summary>
public static class ProdutoCodigo
{
    // Sem `_`: o parser da chave separa por `_` e exige exatamente 3 campos,
    // então um código com underscore produziria chave impossível de validar.
    // Só minúsculas: a comparação no handler é ordinal, sem ignorar caixa.
    private static readonly System.Text.RegularExpressions.Regex Padrao =
        new("^[a-z0-9]{2,20}$", System.Text.RegularExpressions.RegexOptions.Compiled);

    public static bool Valido(string? codigo)
        => !string.IsNullOrEmpty(codigo) && Padrao.IsMatch(codigo);
}

public class Agente
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid EscritorioId { get; set; }
    public Escritorio Escritorio { get; set; } = null!;
    public string Nome { get; set; } = string.Empty;

    /// <summary>
    /// Ferramenta do hub que esta chave habilita. Redundante com o prefixo da
    /// chave crua de propósito: a chave crua não é persistida (só o hash), e o
    /// handler confere um contra o outro a cada request.
    /// </summary>
    public Guid ProdutoId { get; set; }
    public Produto Produto { get; set; } = null!;

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

/// <summary>
/// Chave-valor por (escritório, ferramenta). Escopada por
/// <see cref="ProdutoId"/> porque o comportamento configurável — período de
/// busca, tipos de nota, geração de PDF — é próprio de cada ferramenta:
/// NFS-e e DET não têm por que compartilhar o mesmo "período padrão de
/// busca". Antes de existir mais de uma ferramenta a chave era só
/// (EscritorioId, Chave); o histórico foi atribuído ao NFS-e no backfill.
/// </summary>
public class ConfiguracaoEscritorio
{
    public Guid EscritorioId { get; set; }
    public Escritorio Escritorio { get; set; } = null!;
    public Guid ProdutoId { get; set; }
    public Produto Produto { get; set; } = null!;
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
