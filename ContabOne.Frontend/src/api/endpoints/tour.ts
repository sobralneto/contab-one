import apiClient from '../client'

/** Nomes de rota cuja explicação o usuário logado já viu. */
export async function listarPaginasVistas(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>('/api/tour')
  return data
}

export async function marcarPaginaVista(pagina: string): Promise<void> {
  await apiClient.post(`/api/tour/${encodeURIComponent(pagina)}`)
}
