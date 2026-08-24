import apiClient from '../client'
import type { ConfiguracaoDict, ConfiguracaoResponse } from '../types'

// Configuração é por (escritório, ferramenta) — não existe mais "a"
// configuração do escritório, só a configuração dele para uma ferramenta
// específica. `produtoCodigo` é obrigatório nos dois, espelhando a API.
export async function obterConfiguracao(
  produtoCodigo: string,
  escritorioId?: string,
): Promise<ConfiguracaoResponse> {
  const { data } = await apiClient.get<ConfiguracaoResponse>('/api/configuracao', {
    params: { produtoCodigo, ...(escritorioId ? { escritorioId } : {}) },
  })
  return data
}

export async function salvarConfiguracao(
  configs: ConfiguracaoDict,
  produtoCodigo: string,
  escritorioId?: string,
): Promise<{ salvas: number }> {
  const { data } = await apiClient.put<{ salvas: number }>('/api/configuracao', configs, {
    params: { produtoCodigo, ...(escritorioId ? { escritorioId } : {}) },
  })
  return data
}
