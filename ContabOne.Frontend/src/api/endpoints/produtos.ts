import apiClient from '../client'
import type { ProdutoDto } from '../types'

// Catálogo de ferramentas do hub, só as ativas — é o que alimenta o seletor
// da tela de agentes. O cadastro fica em endpoints/admin.ts.
export async function listarProdutos(): Promise<ProdutoDto[]> {
  const { data } = await apiClient.get<ProdutoDto[]>('/api/produtos')
  return data
}
