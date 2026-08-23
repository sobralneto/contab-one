import apiClient from '../client'
import type {
  ExecucaoResumo,
  ExecucaoDetalhe,
  ExecucaoGrupoEscritorio,
  ExecucaoGrupoCliente,
  PaginatedResponse,
} from '../types'

export async function listarExecucoes(params?: {
  pagina?: number
  tamanho?: number
}): Promise<PaginatedResponse<ExecucaoResumo>> {
  const { data } = await apiClient.get<PaginatedResponse<ExecucaoResumo>>('/api/execucoes', { params })
  return data
}

export async function listarExecucoesAgrupadas(
  agruparPor: 'escritorio' | 'cliente',
): Promise<ExecucaoGrupoEscritorio[] | ExecucaoGrupoCliente[]> {
  const { data } = await apiClient.get<
    | { grupos: ExecucaoGrupoEscritorio[] }
    | { grupos: ExecucaoGrupoCliente[] }
  >('/api/execucoes', { params: { agruparPor } })
  return data.grupos
}

export async function detalheExecucao(id: string): Promise<ExecucaoDetalhe> {
  const { data } = await apiClient.get<ExecucaoDetalhe>(`/api/execucoes/${id}`)
  return data
}
