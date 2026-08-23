import apiClient from '../client'
import type {
  EscritorioDto,
  CriarEscritorioRequest,
  AtualizarEscritorioRequest,
  PlanoDto,
  ProdutoDto,
  ProdutoAdminDto,
  CriarProdutoRequest,
  AtualizarProdutoRequest,
  RegraDto,
  RegraDetalheDto,
  PublicarRegraRequest,
  VisaoGeralDto,
} from '../types'

// ── Escritórios ──
export async function listarEscritorios(): Promise<EscritorioDto[]> {
  const { data } = await apiClient.get<EscritorioDto[]>('/api/admin/escritorios')
  return data
}

export async function obterEscritorio(id: string): Promise<EscritorioDto> {
  const { data } = await apiClient.get<EscritorioDto>(`/api/admin/escritorios/${id}`)
  return data
}

export async function criarEscritorio(req: CriarEscritorioRequest): Promise<{ id: string; nome: string }> {
  const { data } = await apiClient.post<{ id: string; nome: string }>('/api/admin/escritorios', req)
  return data
}

export async function atualizarEscritorio(
  id: string,
  req: AtualizarEscritorioRequest,
): Promise<{ id: string; status: string }> {
  const { data } = await apiClient.put<{ id: string; status: string }>(`/api/admin/escritorios/${id}`, req)
  return data
}

// ── Planos ──
export async function listarPlanos(): Promise<PlanoDto[]> {
  const { data } = await apiClient.get<PlanoDto[]>('/api/admin/planos')
  return data
}

export async function criarPlano(plano: Omit<PlanoDto, 'id'>): Promise<PlanoDto> {
  const { data } = await apiClient.post<PlanoDto>('/api/admin/planos', plano)
  return data
}

export async function atualizarPlano(id: string, plano: Omit<PlanoDto, 'id'>): Promise<PlanoDto> {
  const { data } = await apiClient.put<PlanoDto>(`/api/admin/planos/${id}`, plano)
  return data
}

// ── Produtos (ferramentas do hub) ──
export async function listarProdutosAdmin(): Promise<ProdutoAdminDto[]> {
  const { data } = await apiClient.get<ProdutoAdminDto[]>('/api/admin/produtos')
  return data
}

export async function criarProduto(
  req: CriarProdutoRequest,
): Promise<{ id: string; codigo: string; nome: string }> {
  const { data } = await apiClient.post('/api/admin/produtos', req)
  return data
}

export async function atualizarProduto(
  id: string,
  req: AtualizarProdutoRequest,
): Promise<ProdutoDto> {
  const { data } = await apiClient.put<ProdutoDto>(`/api/admin/produtos/${id}`, req)
  return data
}

// ── Regras ──
export async function listarRegras(): Promise<RegraDto[]> {
  const { data } = await apiClient.get<RegraDto[]>('/api/admin/regras')
  return data
}

export async function obterRegra(id: string): Promise<RegraDetalheDto> {
  const { data } = await apiClient.get<RegraDetalheDto>(`/api/admin/regras/${id}`)
  return data
}

/** Conteúdo da versão ativa (ou null se nenhuma regra foi publicada ainda). */
export async function obterRegraAtiva(): Promise<RegraDetalheDto | null> {
  const regras = await listarRegras()
  const ativa = regras.find((r) => r.ativa)
  if (!ativa) return null
  return obterRegra(ativa.id)
}

export async function publicarRegra(req: PublicarRegraRequest): Promise<{ id: string; versao: number }> {
  const { data } = await apiClient.post<{ id: string; versao: number }>('/api/admin/regras', req)
  return data
}

// ── Visão Geral ──
export async function fetchVisaoGeral(): Promise<VisaoGeralDto> {
  const { data } = await apiClient.get<VisaoGeralDto>('/api/admin/visao-geral')
  return data
}
