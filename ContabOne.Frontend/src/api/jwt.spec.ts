import { describe, it, expect, vi, afterEach } from 'vitest'
import { decodeJwt, isJwtExpired } from './jwt'

// Monta um JWT com o payload dado (assinatura irrelevante — o decode não valida).
function tokenComPayload(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const corpo = btoa(JSON.stringify(payload)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
  return `${header}.${corpo}.assinatura-fake`
}

const URI_ROLE = 'http://schemas.microsoft.com/ws/2008/06/identity/claims/role'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('jwt.decodeJwt', () => {
  it('extrai as claims', () => {
    const token = tokenComPayload({
      sub: 'abc-123',
      email: 'admin@nfse.local',
      nome: 'Admin',
      role: 'PlatformAdmin',
      escritorio_id: null,
      exp: 1_800_000_000,
    })
    expect(decodeJwt(token)).toMatchObject({
      sub: 'abc-123',
      email: 'admin@nfse.local',
      nome: 'Admin',
      role: 'PlatformAdmin',
      exp: 1_800_000_000,
    })
  })

  it('mapeia a claim de papel na URI longa do .NET para role', () => {
    const token = tokenComPayload({
      sub: 'x',
      [URI_ROLE]: 'EscritorioAdmin',
    })
    expect(decodeJwt(token)?.role).toBe('EscritorioAdmin')
  })

  it('devolve null para token malformado', () => {
    expect(decodeJwt('')).toBeNull()
    expect(decodeJwt('sem-pontos')).toBeNull()
    expect(decodeJwt('a.b.c')).toBeNull() // corpo não é JSON
    expect(decodeJwt('@@@.@@@.@@@')).toBeNull()
  })
})

describe('jwt.isJwtExpired', () => {
  it('token expirado é true', () => {
    vi.spyOn(Date, 'now').mockReturnValue(2_000_000_000_000) // 2033
    const token = tokenComPayload({ exp: 1_800_000_000 }) // 2027
    expect(isJwtExpired(token)).toBe(true)
  })

  it('token válido é false', () => {
    vi.spyOn(Date, 'now').mockReturnValue(1_700_000_000_000) // 2023
    const token = tokenComPayload({ exp: 1_800_000_000 }) // 2027
    expect(isJwtExpired(token)).toBe(false)
  })

  it('token sem exp é true (não confiável)', () => {
    expect(isJwtExpired(tokenComPayload({ sub: 'x' }))).toBe(true)
  })

  it('token ilegível é true', () => {
    expect(isJwtExpired('@@@.@@@.@@@')).toBe(true)
  })
})
