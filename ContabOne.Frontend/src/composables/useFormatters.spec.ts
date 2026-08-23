import { describe, it, expect, vi, afterEach } from 'vitest'
import { useFormatters } from './useFormatters'

const { formatCnpj, formatDate, formatDateTime, formatRelativeTime, formatNumber } = useFormatters()

afterEach(() => {
  vi.restoreAllMocks()
})

describe('useFormatters.formatRelativeTime', () => {
  it('as quatro faixas: agora, minutos, horas, dias', () => {
    const agora = Date.now()
    vi.spyOn(Date, 'now').mockReturnValue(agora)

    expect(formatRelativeTime(new Date(agora - 10_000).toISOString())).toBe('agora')
    expect(formatRelativeTime(new Date(agora - 5 * 60_000).toISOString())).toBe('há 5 min')
    expect(formatRelativeTime(new Date(agora - 3 * 3_600_000).toISOString())).toBe('há 3 h')
    expect(formatRelativeTime(new Date(agora - 2 * 86_400_000).toISOString())).toBe('há 2 dias')
    expect(formatRelativeTime(new Date(agora - 1 * 86_400_000).toISOString())).toBe('há 1 dia')
  })

  it('acima de 30 dias devolve a data absoluta', () => {
    const agora = Date.now()
    vi.spyOn(Date, 'now').mockReturnValue(agora)
    const velho = new Date(agora - 45 * 86_400_000).toISOString()
    expect(formatRelativeTime(velho)).toBe(formatDate(velho))
  })
})

describe('useFormatters — entrada vazia devolve —', () => {
  it('em formatCnpj, formatDate, formatDateTime e formatRelativeTime', () => {
    expect(formatCnpj('')).toBe('—')
    expect(formatDate('')).toBe('—')
    expect(formatDateTime('')).toBe('—')
    expect(formatRelativeTime('')).toBe('—')
  })
})

describe('useFormatters.formatNumber', () => {
  it('formata em pt-BR', () => {
    expect(formatNumber(1234567)).toBe('1.234.567')
  })
})
