import apiClient from '../client'
import type { AlertaDto } from '../types'

export async function listarAlertas(): Promise<AlertaDto[]> {
  const { data } = await apiClient.get<AlertaDto[]>('/api/alertas')
  return data
}

export async function resolverAlerta(id: string): Promise<{ id: string; resolvido: boolean }> {
  const { data } = await apiClient.post<{ id: string; resolvido: boolean }>(`/api/alertas/${id}/resolver`)
  return data
}
