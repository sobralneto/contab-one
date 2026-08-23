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
  label?: string
  tipo: TipoNota
  qtd: number
}

export interface RankingItem {
  clienteId: string
  nome: string
  codigo: string | null
  total: number
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
  cnpjMascarado?: string
  cnpjHash?: string
  certificadoValidade?: string
  escritorioId?: string
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
  sucesso: number
  parcial: number
  falha: number
  execucoes: ExecucaoResumo[]
}

export interface ExecucaoGrupoCliente {
  clienteId: string
  clienteNome: string
  total: number
  sucesso: number
  parcial: number
  falha: number
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

// ── Produtos (ferramentas do hub) ──

// Catálogo vindo do banco, não de uma lista fixa no front. `codigo` é o
// primeiro campo da chave de API do produto (`nfse_…`, `det_…`).
export interface ProdutoDto {
  id: string
  codigo: string
  nome: string
  descricao: string
  ativo: boolean
  ordem: number
}

// A visão do admin traz também o que só interessa ao cadastro.
export interface ProdutoAdminDto extends ProdutoDto {
  criadoEm: string
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
  ativo?: boolean
  ordem?: number
}

// Sem `codigo`: ele é imutável depois de criado — já foi impresso nas chaves
// que estão nos config.toml dos clientes.
export interface AtualizarProdutoRequest {
  nome: string
  descricao?: string
  ativo?: boolean
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

// ── Enums (match C# System.Text.Json string serialization exactly) ──
export type StatusEscritorio = 'Ativo' | 'Inadimplente' | 'Suspenso' | 'Cancelado'
export type StatusExecucao = 'Sucesso' | 'Parcial' | 'Falha'
export type TipoNota = 'Recebidas' | 'Emitidas'
export type OrigemCliente = 'Manual' | 'Agente'
export type TipoAlerta = 'CertificadoVencendo' | 'CertificadoVencido' | 'ExecucaoFalhou' | 'AgenteSilencioso'
export type SeveridadeAlerta = 'Info' | 'Atencao' | 'Critico'
