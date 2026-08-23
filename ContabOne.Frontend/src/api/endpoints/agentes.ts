import apiClient from '../client'
import type { AgenteDto, CriarAgenteRequest, CriarAgenteResponse } from '../types'

export async function listarAgentes(): Promise<AgenteDto[]> {
  const { data } = await apiClient.get<AgenteDto[]>('/api/agentes')
  return data
}

export async function criarAgente(req: CriarAgenteRequest): Promise<CriarAgenteResponse> {
  const { data } = await apiClient.post<CriarAgenteResponse>('/api/agentes', req)
  return data
}

export async function revogarAgente(id: string): Promise<{ id: string; revogado: boolean }> {
  const { data } = await apiClient.delete<{ id: string; revogado: boolean }>(`/api/agentes/${id}`)
  return data
}
