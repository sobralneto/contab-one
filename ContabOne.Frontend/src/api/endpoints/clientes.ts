import apiClient from '../client'
import type { ClienteDto, ClienteRequest, PaginatedResponse, ProximoCodigoResponse } from '../types'

export async function listarClientes(params?: {
  busca?: string
  escritorioId?: string
  diasVencimentoCert?: number
  pagina?: number
  tamanho?: number
}): Promise<PaginatedResponse<ClienteDto>> {
  const { data } = await apiClient.get<PaginatedResponse<ClienteDto>>('/api/clientes', { params })
  return data
}

export async function criarCliente(req: ClienteRequest): Promise<{ id: string }> {
  const { data } = await apiClient.post<{ id: string }>('/api/clientes', req)
  return data
}

export async function atualizarCliente(id: string, req: ClienteRequest): Promise<{ id: string }> {
  const { data } = await apiClient.put<{ id: string }>(`/api/clientes/${id}`, req)
  return data
}

export async function excluirCliente(id: string): Promise<void> {
  await apiClient.delete(`/api/clientes/${id}`)
}

/** Sugestão do próximo código numérico de 4 dígitos livre para o escritório em escopo — editável antes de confirmar. */
export async function proximoCodigoCliente(escritorioId?: string): Promise<ProximoCodigoResponse> {
  const { data } = await apiClient.get<ProximoCodigoResponse>('/api/clientes/proximo-codigo', {
    params: escritorioId ? { escritorioId } : undefined,
  })
  return data
}
