/**
 * Formatting helpers for pt-BR locale.
 * CNPJ values come already masked from the API; these just handle display edge cases.
 */
export function useFormatters() {
  function formatCnpj(cnpj: string): string {
    return cnpj || '—'
  }

  function formatDate(iso: string): string {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('pt-BR')
  }

  function formatDateTime(iso: string): string {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('pt-BR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  function formatNumber(n: number): string {
    return n.toLocaleString('pt-BR')
  }

  /**
   * Relative time in Portuguese: "há 2 horas", "há 3 dias", etc.
   */
  function formatRelativeTime(iso: string): string {
    if (!iso) return '—'
    const diffMs = Date.now() - new Date(iso).getTime()
    const diffMin = Math.floor(diffMs / 60_000)
    if (diffMin < 1) return 'agora'
    if (diffMin < 60) return `há ${diffMin} min`
    const diffHrs = Math.floor(diffMin / 60)
    if (diffHrs < 24) return `há ${diffHrs} h`
    const diffDays = Math.floor(diffHrs / 24)
    if (diffDays < 30) return `há ${diffDays} dia${diffDays > 1 ? 's' : ''}`
    return formatDate(iso)
  }

  return { formatCnpj, formatDate, formatDateTime, formatNumber, formatRelativeTime }
}
