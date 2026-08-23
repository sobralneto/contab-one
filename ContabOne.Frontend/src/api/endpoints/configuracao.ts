import apiClient from '../client'
import type { ConfiguracaoDict, ConfiguracaoResponse } from '../types'

export async function obterConfiguracao(escritorioId?: string): Promise<ConfiguracaoResponse> {
  const { data } = await apiClient.get<ConfiguracaoResponse>('/api/configuracao', {
    params: escritorioId ? { escritorioId } : undefined,
  })
  return data
}

export async function salvarConfiguracao(
  configs: ConfiguracaoDict,
  escritorioId?: string,
): Promise<{ salvas: number }> {
  const { data } = await apiClient.put<{ salvas: number }>('/api/configuracao', configs, {
    params: escritorioId ? { escritorioId } : undefined,
  })
  return data
}
