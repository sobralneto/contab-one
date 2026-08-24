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

// `produtoCodigo` escopa a lista pela ferramenta da tela — sem ele a
// execução de qualquer ferramenta do escritório apareceria misturada.
export async function listarExecucoesAgrupadas(
  agruparPor: 'escritorio' | 'cliente',
  produtoCodigo: string,
): Promise<ExecucaoGrupoEscritorio[] | ExecucaoGrupoCliente[]> {
  const { data } = await apiClient.get<
    | { grupos: ExecucaoGrupoEscritorio[] }
    | { grupos: ExecucaoGrupoCliente[] }
  >('/api/execucoes', { params: { agruparPor, produtoCodigo } })
  return data.grupos
}

export async function detalheExecucao(id: string): Promise<ExecucaoDetalhe> {
  const { data } = await apiClient.get<ExecucaoDetalhe>(`/api/execucoes/${id}`)
  return data
}
