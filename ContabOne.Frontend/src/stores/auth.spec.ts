import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from './auth'
import type { UsuarioDto, Papel } from '@/api/types'

const CHAVE = 'contabone_access_token'

function tokenValido(exp = 1_800_000_000): string {
  const header = btoa(JSON.stringify({ alg: 'HS256' }))
  const corpo = btoa(JSON.stringify({ sub: 'u1', email: 'a@b.c', nome: 'A', role: 'PlatformAdmin', exp }))
  return `${header}.${corpo}.sig`
}

function tokenExpirado(): string {
  return tokenValido(1) // exp em 1970
}

const usuario: UsuarioDto = {
  id: 'u1',
  email: 'a@b.c',
  nome: 'A',
  papel: 'PlatformAdmin',
  escritorioId: null,
}

beforeEach(() => {
  setActivePinia(createPinia())
  sessionStorage.clear()
  vi.restoreAllMocks()
})

describe('stores/auth — persistência', () => {
  it('setSession persiste em sessionStorage e clearSession remove', () => {
    const store = useAuthStore()
    store.setSession(tokenValido(), usuario)
    expect(sessionStorage.getItem(CHAVE)).toBeTruthy()
    expect(store.isAuthenticated).toBe(true)

    store.clearSession()
    expect(sessionStorage.getItem(CHAVE)).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(store.usuario).toBeNull()
  })

  it('sessão é restaurada do sessionStorage na criação quando o token é válido', () => {
    sessionStorage.setItem(CHAVE, tokenValido())
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
    expect(store.usuario?.papel).toBe('PlatformAdmin')
  })

  it('sessão expirada no storage é ignorada na criação', () => {
    sessionStorage.setItem(CHAVE, tokenExpirado())
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.usuario).toBeNull()
  })
})

describe('stores/auth — papéis', () => {
  it.each([
    ['PlatformAdmin', true, true],
    ['EscritorioAdmin', false, true],
    ['EscritorioUsuario', false, false],
  ] as [Papel, boolean, boolean][])(
    'papel %s: isPlatformAdmin=%s, isEscritorioAdmin=%s',
    (papel, ehAdmin, ehEscritorioAdmin) => {
      const store = useAuthStore()
      store.setSession(tokenValido(), { ...usuario, papel })
      expect(store.isPlatformAdmin).toBe(ehAdmin)
      expect(store.isEscritorioAdmin).toBe(ehEscritorioAdmin)
    },
  )
})

describe('stores/auth — canAccess', () => {
  it('lista de papéis vazia libera para usuário autenticado', () => {
    const store = useAuthStore()
    store.setSession(tokenValido(), usuario)
    expect(store.canAccess([])).toBe(true)
  })

  it('papel ausente bloqueia mesmo com lista vazia', () => {
    const store = useAuthStore()
    expect(store.canAccess([])).toBe(false)
  })

  it('papel fora da lista bloqueia', () => {
    const store = useAuthStore()
    store.setSession(tokenValido(), { ...usuario, papel: 'EscritorioUsuario' })
    expect(store.canAccess(['PlatformAdmin'])).toBe(false)
    expect(store.canAccess(['EscritorioUsuario', 'EscritorioAdmin'])).toBe(true)
  })
})
