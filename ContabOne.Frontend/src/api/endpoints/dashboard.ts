import apiClient from '../client'
import type { DashboardKpis, SerieItem, RankingItem, CertificadoVencimentoItem } from '../types'

export async function fetchKpis(): Promise<DashboardKpis> {
  const { data } = await apiClient.get<DashboardKpis>('/api/dashboard/kpis')
  return data
}

export async function fetchSeries(params?: {
  de?: string
  ate?: string
  escritorioId?: string
  clienteId?: string
}): Promise<SerieItem[]> {
  const { data } = await apiClient.get<SerieItem[]>('/api/dashboard/series', { params })
  return data
}

export async function fetchRanking(): Promise<RankingItem[]> {
  const { data } = await apiClient.get<RankingItem[]>('/api/dashboard/ranking')
  return data
}

export async function fetchCertificadosVencimento(): Promise<CertificadoVencimentoItem[]> {
  const { data } = await apiClient.get<CertificadoVencimentoItem[]>('/api/dashboard/certificados')
  return data
}
