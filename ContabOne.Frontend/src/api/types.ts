// ── Auth ──
export interface LoginRequest {
  email: string
  password: string
}

export interface UsuarioDto {
  id: string
  email: string
  nome: string
  papel: Papel
  escritorioId: string | null
  deveTrocarSenha: boolean
}

export interface TrocarSenhaRequest {
  senhaAtual: string
  novaSenha: string
}

export interface LoginResponse {
  accessToken: string
  usuario: UsuarioDto
}

// ── Roles ──
export type Papel = 'PlatformAdmin' | 'EscritorioAdmin' | 'EscritorioUsuario'

// ── Dashboard ──
export interface DashboardKpis {
  totalClientes: number
  totalAgentesAtivos: number
  notasBaixadasMes: number
  certificadosVencendo30d: number
  ultimaExecucao: UltimaExecucaoResumo | null
}

export interface UltimaExecucaoResumo {
  id: string
  status: StatusExecucao
  iniciadoEm: string
  duracaoMs: number | null
}

export interface SerieItem {
  competencia: string
  tipo: TipoNota
  qtd: number
}

export interface RankingItem {
  clienteId: string
  nome: string
  codigo: string | null
  total: number
}

export interface CertificadoVencimentoItem {
  clienteId: string
  codigo: string
  nome: string
  certificadoValidade: string
}

// ── Clientes ──
export interface ClienteDto {
  id: string
  codigo: string
  nome: string
  cnpjMascarado: string
  certificadoValidade: string | null
  certificadoNomeArquivo: string | null
  escritorioNome: string | null
  origem: OrigemCliente
  atualizadoEm: string
}

export interface ClienteRequest {
  codigo: string
  nome: string
  /** CNPJ completo, opcional — o servidor deriva hash e máscara e descarta o valor cru. */
  cnpj?: string
  cnpjMascarado?: string
  cnpjHash?: string
  certificadoValidade?: string
  escritorioId?: string
  /** "Importacao" quando o cliente nasce da importação de um documento; ausente = Manual. */
  origem?: OrigemCliente
}

export interface PaginatedResponse<T> {
  total: number
  pagina: number
  tamanho: number
  dados: T[]
}

// ── Execucoes ──
export interface ExecucaoResumo {
  id: string
  status: StatusExecucao
  iniciadoEm: string
  finalizadoEm: string | null
  duracaoMs: number | null
  versaoAgente: string | null
  mensagemErro: string | null
  totalMetricas: number
  totalBaixadas: number
  totalFalhas: number
}

export interface ExecucaoDetalhe extends ExecucaoResumo {
  metricas: ExecucaoMetricaDto[]
}

export interface ExecucaoGrupoEscritorio {
  escritorioId: string
  escritorioNome: string
  total: number
  ultimoStatus: StatusExecucao
  falha: number
  execucoes: ExecucaoResumo[]
}

export interface ExecucaoGrupoCliente {
  clienteId: string
  clienteNome: string
  total: number
  ultimoStatus: StatusExecucao
  totalBaixadas: number
}

export interface ExecucaoMetricaDto {
  clienteId: string
  clienteNome: string | null
  tipo: TipoNota
  competencia: string
  qtdBaixadas: number
  qtdPuladas: number
  qtdFalhas: number
  duracaoMs: number
}

// ── Alertas ──
export interface AlertaDto {
  id: string
  tipo: TipoAlerta
  severidade: SeveridadeAlerta
  mensagem: string
  criadoEm: string
  resolvidoEm: string | null
  clienteNome: string | null
  aberto: boolean
}

// ── Configuracao ──
export type ConfiguracaoDict = Record<string, string>

export interface ConfiguracaoResponse {
  valores: ConfiguracaoDict
  plano: PlanoLimites
}

export interface PlanoLimites {
  permiteEmitidas: boolean
  maxClientes: number
  maxAgentes: number
}

// ── Domínios e páginas (agrupamento do catálogo) ──

// Departamento do escritório contábil que a ferramenta atende. Dado, não
// enum: cadastrar domínio novo no backend não exige deploy do front.
export interface DominioDto {
  codigo: string
  nome: string
  ordem: number
  icone: string | null
}

// Conjunto fechado espelhando `PaginaFerramenta` na API — cada valor
// corresponde a um componente de rota de ferramenta (/f/:produto/…) que
// existe no front. Clientes e Agentes ficam de fora de propósito: as duas
// telas mostram dado do escritório inteiro, não particionado por produto —
// vivem em rotas transversais (`/clientes`, `/agentes`). "regras" é
// restrita a PlatformAdmin (não EscritorioAdmin) — mais estrita que as
// outras páginas de ferramenta.
export type PaginaFerramenta = 'visao-geral' | 'execucoes' | 'configuracao' | 'regras' | 'importacao'

// ── Produtos (ferramentas do hub) ──

// Catálogo vindo do banco, não de uma lista fixa no front. `codigo` é o
// primeiro campo da chave de API do produto (`nfse_…`, `det_…`). É o que
// `GET /api/produtos` devolve para a sessão: escopado a quem contratou, ou o
// catálogo inteiro (marcado por `contratado`) para o admin.
export interface ProdutoDto {
  id: string
  codigo: string
  nome: string
  descricao: string
  ativo: boolean
  /** Governa só a OFERTA de chave de API nova — ferramenta sem agente (ex.: pgdas) some do seletor. */
  temAgente: boolean
  ordem: number
  paginas: PaginaFerramenta[]
  dominio: DominioDto
  contratado: boolean
}

// A visão de cadastro do admin (`GET /api/admin/produtos`) — inclui
// inativos e o que só interessa à tela de Ferramentas.
export interface ProdutoAdminDto {
  id: string
  codigo: string
  nome: string
  descricao: string
  ativo: boolean
  temAgente: boolean
  ordem: number
  criadoEm: string
  paginas: PaginaFerramenta[]
  dominioCodigo: string
  dominioNome: string
  totalAgentes: number
}

// Estado de uma ferramenta para UM escritório, na tela de admin.
export interface EscritorioProdutoDto {
  id: string
  codigo: string
  nome: string
  descricao: string
  produtoAtivo: boolean
  totalAgentes: number
  habilitado: boolean
  habilitadoEm: string | null
}

export interface CriarProdutoRequest {
  codigo: string
  nome: string
  descricao?: string
  dominioCodigo: string
  paginas?: PaginaFerramenta[]
  ativo?: boolean
  /** Ausente = `true` — a maioria das ferramentas tem agente. */
  temAgente?: boolean
  ordem?: number
}

// Sem `codigo`: ele é imutável depois de criado — já foi impresso nas chaves
// que estão nos config.toml dos clientes.
export interface AtualizarProdutoRequest {
  nome: string
  descricao?: string
  dominioCodigo?: string
  paginas?: PaginaFerramenta[]
  ativo?: boolean
  temAgente?: boolean
  ordem?: number
}

// ── Agentes ──
export interface AgenteDto {
  id: string
  nome: string
  produtoId: string
  produtoCodigo: string
  produtoNome: string
  apiKeyPrefixo: string
  versaoAgente: string | null
  ultimoContatoEm: string | null
  criadoEm: string
  ativo: boolean
  revogadoEm: string | null
  escritorioNome: string | null
}

export interface CriarAgenteRequest {
  nome: string
  produtoId: string
  escritorioId?: string
}

export interface CriarAgenteResponse {
  id: string
  nome: string
  produtoId: string
  produtoCodigo: string
  produtoNome: string
  apiKey: string
  aviso: string
}

// ── Usuários ──
export interface UsuarioListaDto {
  id: string
  nome: string
  email: string
  papel: Papel
  escritorioId: string | null
  escritorioNome: string | null
  ativo: boolean
  deveTrocarSenha: boolean
  ultimoLoginEm: string | null
}

export interface CriarUsuarioRequest {
  nome: string
  email: string
  senha: string
  papel: Papel
  escritorioId?: string
}

export interface AtualizarUsuarioRequest {
  nome?: string
  papel?: Papel
  escritorioId?: string
}

export interface ResetarSenhaRequest {
  novaSenha: string
}

// ── Admin ──
export interface EscritorioDto {
  id: string
  nome: string
  cnpjMascarado: string
  status: StatusEscritorio
  planoId: string | null
  planoNome: string | null
  criadoEm: string
  totalClientes: number
  totalAgentes: number
}

export interface CriarEscritorioRequest {
  nome: string
  cnpjMascarado?: string
  cnpjHash?: string
  planoId?: string
  status?: StatusEscritorio
}

export interface AtualizarEscritorioRequest {
  nome?: string
  cnpjMascarado?: string
  cnpjHash?: string
  planoId?: string
  status?: StatusEscritorio
}

export interface PlanoDto {
  id: string
  nome: string
  maxClientes: number
  maxAgentes: number
  permiteEmitidas: boolean
  precoMensal: number
}

export interface RegraDto {
  id: string
  versao: number
  publicadaEm: string
  ativa: boolean
  tamanhoConteudo: number
}

export interface RegraDetalheDto extends RegraDto {
  conteudo: string
}

export interface PublicarRegraRequest {
  conteudo: string
}

export interface VisaoGeralDto {
  totalEscritorios: number
  totalAtivos: number
  execucoesUltimos30d: number
  escritoriosAtivos30d: number
}

// ── PGDAS-D (apuração do Simples Nacional) ──

// Os oito tributos do PGDAS-D — mesmos nomes de campo em toda a slice, do
// parser (frontend) ao `ApuracaoSimples` (backend).
export interface TributosPgdas {
  irpj: number
  csll: number
  cofins: number
  pis: number
  inss: number
  icms: number
  ipi: number
  iss: number
}

export type TipoDocumentoPgdas = 'Extrato' | 'Declaracao'

export interface SegregacaoPgdasDto {
  categoria: string
  receita: number
}

// Uma linha da tabela em `GET /api/pgdas/apuracoes` (visão geral).
export interface ApuracaoListaDto {
  id: string
  clienteId: string
  clienteNome: string
  competencia: string
  tipoDocumento: TipoDocumentoPgdas
  faturamento: number
  das: number
  semMovimento: boolean
  vencimento: string
  pago: boolean
  editadoManualmente: boolean
  rba: number | null
  sublimite: number | null
  /** Soma dos oito tributos x DAS (tolerância R$ 0,05) — calculado no servidor, nunca no front. */
  naoConfere: boolean
}

// Uma competência dentro do payload de `GET /api/pgdas/clientes/{id}/dashboard`
// — inclui os tributos e a segregação que a lista não precisa.
export interface ApuracaoDashboardDto extends TributosPgdas {
  id: string
  competencia: string
  tipoDocumento: TipoDocumentoPgdas
  faturamento: number
  das: number
  semMovimento: boolean
  vencimento: string
  pago: boolean
  rba: number | null
  sublimite: number | null
  impedido: boolean | null
  editadoManualmente: boolean
  segregacao: SegregacaoPgdasDto[]
}

export interface SerieMensalDto {
  competencia: string
  receitaBruta: number
}

export interface ClienteDashboardDto {
  id: string
  nome: string
  cnpjMascarado: string
}

export interface DashboardPgdasDto {
  cliente: ClienteDashboardDto
  apuracoes: ApuracaoDashboardDto[]
  serieMensal: SerieMensalDto[]
}

// Uma competência do lote conferido — o que `POST /api/pgdas/apuracoes` recebe.
export interface ApuracaoPgdasRequest extends TributosPgdas {
  competencia: string
  tipoDocumento: TipoDocumentoPgdas
  faturamento: number
  das: number
  semMovimento: boolean
  vencimento: string
  pago: boolean
  rba?: number | null
  sublimite?: number | null
  impedido?: boolean | null
  editadoManualmente: boolean
  /** Categoria (`CategoriaReceita`) → receita do período. */
  segregacao?: Record<string, number>
}

export interface GravarApuracoesRequest {
  clienteId: string
  substituir: boolean
  /** Competência do documento carregado — decide quem prevalece no upsert da série mensal. */
  competenciaDocumento: string
  apuracoes: ApuracaoPgdasRequest[]
  serieMensal?: SerieMensalDto[]
}

export interface GravarApuracoesResponse {
  gravadas: number
}

// Corpo do 409 quando alguma competência do lote já existe.
export interface CompetenciaConflitoDto {
  competencia: string
  editadoManualmente: boolean
}

export interface ConflitoApuracoesResponse {
  erro: string
  competencias: CompetenciaConflitoDto[]
}

export interface AtualizarApuracaoRequest {
  pago?: boolean
  vencimento?: string
}

export interface ResumoPgdasDto {
  clientesComApuracao: number
  competenciasGravadas: number
  dasEmAberto: number
  naoConferem: number
}

export interface IdentificarClienteRequest {
  cnpj: string
}

export interface IdentificarClienteResponse {
  encontrado: boolean
  id?: string
  codigo?: string
  nome?: string
  cnpjMascarado?: string
}

export interface ProximoCodigoResponse {
  codigo: string
}

// ── Enums (match C# System.Text.Json string serialization exactly) ──
export type StatusEscritorio = 'Ativo' | 'Inadimplente' | 'Suspenso' | 'Cancelado'
export type StatusExecucao = 'Sucesso' | 'Parcial' | 'Falha'
export type TipoNota = 'Recebidas' | 'Emitidas'
export type OrigemCliente = 'Manual' | 'Agente' | 'Importacao'
export type TipoAlerta = 'CertificadoVencendo' | 'CertificadoVencido' | 'ExecucaoFalhou' | 'AgenteSilencioso'
export type SeveridadeAlerta = 'Info' | 'Atencao' | 'Critico'
