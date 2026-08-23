import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// O guards.ts guarda `bootstrapped` no escopo do módulo e a store lê
// sessionStorage na criação — os dois precisam estar limpos entre casos.
// vi.resetModules() + imports dinâmicos garantem isso (design.md, Decisão 4).
vi.mock('@/api/client', () => ({
  refreshAccessToken: vi.fn(),
}))

const CHAVE = 'contabone_access_token'

function tokenComPapel(papel: string, exp = 1_800_000_000): string {
  const header = btoa(JSON.stringify({ alg: 'HS256' }))
  const corpo = btoa(JSON.stringify({
    sub: 'u1', email: 'a@b.c', nome: 'A', role: papel, exp,
  }))
  return `${header}.${corpo}.sig`
}

async function montarCenario() {
  const { refreshAccessToken } = await import('@/api/client')
  const { registerGuards } = await import('./guards')
  // router/index.ts exporta a instância como default — com vi.resetModules()
  // cada import dinâmico dá uma instância nova, que é o que cada caso precisa.
  const { default: router } = await import('./index')
  const { useAuthStore } = await import('@/stores/auth')

  setActivePinia(createPinia())
  const auth = useAuthStore()
  registerGuards(router)
  // Sem await router.isReady(): em jsdom não há mount do app, então a
  // navegação inicial só começa no primeiro push — e é o push que resolve
  // quando os guards concluem.
  return { router, auth, refreshAccessToken }
}

beforeEach(() => {
  vi.resetModules()
  sessionStorage.clear()
  vi.restoreAllMocks()
})

describe('router/guards', () => {
  it('rota pública é liberada sem sessão', async () => {
    const { router } = await montarCenario()
    await router.push('/login')
    expect(router.currentRoute.value.name).toBe('login')
  })

  it('usuário autenticado em /login é redirecionado ao dashboard', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioUsuario'))
    const { router } = await montarCenario()
    await router.push('/login')
    expect(router.currentRoute.value.path).toBe('/dashboard')
  })

  it('rota protegida sem sessão redireciona para login preservando o redirect', async () => {
    const { router } = await montarCenario()
    await router.push('/clientes')
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/clientes')
  })

  it('papel insuficiente para rota admin cai no dashboard', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioUsuario'))
    const { router } = await montarCenario()
    await router.push('/admin/planos')
    expect(router.currentRoute.value.path).toBe('/dashboard')
  })

  it('bootstrap tenta refresh uma única vez e limpa isInitializing no sucesso', async () => {
    const mockRefresh = vi.fn().mockResolvedValue({ accessToken: tokenComPapel('EscritorioUsuario') })
    vi.mocked(await import('@/api/client')).refreshAccessToken.mockImplementation(mockRefresh)

    const { router, auth, refreshAccessToken } = await montarCenario()
    expect(auth.isInitializing).toBe(true)

    await router.push('/dashboard')
    expect(auth.isInitializing).toBe(false)
    expect(auth.isAuthenticated).toBe(true)

    // segunda navegação não dispara outro refresh
    await router.push('/clientes')
    expect(mockRefresh).toHaveBeenCalledTimes(1)
  })

  it('bootstrap que falha limpa isInitializing e redireciona ao login', async () => {
    vi.mocked(await import('@/api/client')).refreshAccessToken.mockRejectedValue(new Error('offline'))

    const { router, auth } = await montarCenario()
    await router.push('/dashboard')
    expect(auth.isInitializing).toBe(false)
    expect(auth.isAuthenticated).toBe(false)
    expect(router.currentRoute.value.name).toBe('login')
  })
})
