import type { StatusEscritorio } from '@/api/types'

// Mapa enum → string legível (D5). A API serializa o enum como string
// ("Ativo", "Inadimplente", "Suspenso", "Cancelado").
export const STATUS_ESCRITORIO: Record<StatusEscritorio, { label: string; cssClass: string }> = {
  Ativo: { label: 'Ativo', cssClass: 'status-ok' },
  Inadimplente: { label: 'Inadimplente', cssClass: 'status-warn' },
  Suspenso: { label: 'Suspenso', cssClass: 'status-err' },
  Cancelado: { label: 'Cancelado', cssClass: 'status-err' },
}
