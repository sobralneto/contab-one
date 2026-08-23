import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { http, HttpResponse } from 'msw'
import { servidor } from '@/testes/servidor'
import type { AxiosInstance } from 'axios'

/**
 * O apiClient guarda estado de módulo (isRefreshing, failedQueue) e a store
 * lê sessionStorage na criação — os dois precisam estar limpos entre casos
 * (design.md, Decisão 4). resetModules + reimportação dinâmica em cada caso.
 */
async function importarApiClient() {
  vi.resetModules()
  sessionStorage.clear()
  setActivePinia(createPinia())
  const { default: apiClient, refreshAccessToken } = await import('./client')
  const { useAuthStore } = await import('@/stores/auth')
  return { apiClient, refreshAccessToken, auth: useAuthStore() }
}

let contadorRefresh = 0
function zeraContador() {
  contadorRefresh = 0
}

beforeEach(() => {
  zeraContador()
})

describe('apiClient — interceptor de request', () => {
  it('anexa Authorization: Bearer quando há token, e omite quando não há', async () => {
    const { apiClient, auth } = await importarApiClient()
    let headerVisto: string | null = 'sentinela'

    servidor.use(
      http.get('*/api/alvo', ({ request }) => {
        headerVisto = request.headers.get('authorization')
        return HttpResponse.json({ ok: true })
      }),
    )

    // sem token
    await apiClient.get('/api/alvo')
    expect(headerVisto).toBeNull()

    auth.setSession('token-abc', {
      id: 'u1', email: 'a@b.c', nome: 'A', papel: 'EscritorioUsuario', escritorioId: null,
    })
    await apiClient.get('/api/alvo')
    expect(headerVisto).toBe('Bearer token-abc')
  })
})

describe('apiClient — refresh no 401', () => {
  it('401 dispara refresh e repete a requisição original com o token novo', async () => {
    const { apiClient, auth } = await importarApiClient()
    auth.setSession('token-velho', {
      id: 'u1', email: 'a@b.c', nome: 'A', papel: 'EscritorioUsuario', escritorioId: null,
    })

    let chamadasAlvo = 0
    let headerNaRepeticao: string | null = null
    servidor.use(
      http.get('*/api/alvo', ({ request }) => {
        chamadasAlvo++
        if (chamadasAlvo === 1) return HttpResponse.json({ erro: 'expirado' }, { status: 401 })
        headerNaRepeticao = request.headers.get('authorization')
        return HttpResponse.json({ ok: true })
      }),
      http.post('*/api/auth/refresh', () => {
        contadorRefresh++
        return HttpResponse.json({ accessToken: 'token-novo' })
      }),
    )

    const resposta = await apiClient.get('/api/alvo')
    expect(resposta.data).toEqual({ ok: true })
    expect(chamadasAlvo).toBe(2)
    expect(contadorRefresh).toBe(1)
    expect(headerNaRepeticao).toBe('Bearer token-novo')
    expect(auth.accessToken).toBe('token-novo') // store atualizada com o token novo
  })

  it('a requisição repetida não dispara um segundo refresh se falhar de novo (_retry corta o laço)', async () => {
    const { apiClient, auth } = await importarApiClient()
    auth.setSession('token-velho', {
      id: 'u1', email: 'a@b.c', nome: 'A', papel: 'EscritorioUsuario', escritorioId: null,
    })

    servidor.use(
      http.get('*/api/alvo', () => HttpResponse.json({ erro: 'sempre 401' }, { status: 401 })),
      http.post('*/api/auth/refresh', () => {
        contadorRefresh++
        return HttpResponse.json({ accessToken: 'token-novo' })
      }),
    )

    await expect(apiClient.get('/api/alvo')).rejects.toThrow()
    expect(contadorRefresh).toBe(1) // um refresh só — a repetição não re-dispara
  })

  it('três requisições concorrentes com 401 disparam um único refresh', async () => {
    const { apiClient, auth } = await importarApiClient()
    auth.setSession('token-velho', {
      id: 'u1', email: 'a@b.c', nome: 'A', papel: 'EscritorioUsuario', escritorioId: null,
    })

    let chamadasAlvo = 0
    servidor.use(
      http.get('*/api/alvo', ({ request }) => {
        chamadasAlvo++
        if (chamadasAlvo <= 3) return HttpResponse.json({ erro: 'expirado' }, { status: 401 })
        // as três repetidas chegam com o token novo
        if (request.headers.get('authorization') !== 'Bearer token-novo') {
          return HttpResponse.json({ erro: 'token errado na repetição' }, { status: 401 })
        }
        return HttpResponse.json({ ok: true })
      }),
      http.post('*/api/auth/refresh', () => {
        contadorRefresh++
        return HttpResponse.json({ accessToken: 'token-novo' })
      }),
    )

    const [r1, r2, r3] = await Promise.all([
      apiClient.get('/api/alvo'),
      apiClient.get('/api/alvo'),
      apiClient.get('/api/alvo'),
    ])

    expect(r1.data).toEqual({ ok: true })
    expect(r2.data).toEqual({ ok: true })
    expect(r3.data).toEqual({ ok: true })
    expect(contadorRefresh).toBe(1) // fila: um refresh para as três
  })

  it('refresh que falha limpa a sessão e redireciona para /login', async () => {
    const { apiClient, auth } = await importarApiClient()
    auth.setSession('token-velho', {
      id: 'u1', email: 'a@b.c', nome: 'A', papel: 'EscritorioUsuario', escritorioId: null,
    })

    // jsdom não implementa navegação; o interceptor faz
    // window.location.href = '/login' — substituímos por um duplo para
    // capturar a atribuição (design.md, Decisão 2). Sem esta explicação,
    // alguém pode achar que é ruído e remover.
    // O href precisa ser uma URL válida: o XHR do axios resolve URLs
    // relativas contra window.location, e um objeto sem URL lança
    // "Invalid URL" ANTES do interceptor rodar.
    const locationOriginal = window.location
    Object.defineProperty(window, 'location', {
      value: { href: 'http://localhost:3000/' },
      writable: true,
    })
    try {
      servidor.use(
        http.get('*/api/alvo', () => HttpResponse.json({ erro: 'expirado' }, { status: 401 })),
        http.post('*/api/auth/refresh', () => HttpResponse.json({ erro: 'refresh inválido' }, { status: 401 })),
      )

      await expect(apiClient.get('/api/alvo')).rejects.toThrow()
      expect(auth.accessToken).toBeNull()
      expect(auth.usuario).toBeNull()
      expect((window.location as { href: string }).href).toBe('/login')
    } finally {
      Object.defineProperty(window, 'location', { value: locationOriginal, writable: true })
    }
  })

  it('401 de requisição sem token (ex.: login com senha errada) não dispara refresh', async () => {
    // Descoberto no E2E (7.2): login inválido recebia 401 e o interceptor
    // tentava refresh → falhava → redirecionava para /login, engolindo a
    // mensagem de erro do formulário. Refresh só faz sentido quando o 401
    // respondeu a uma requisição que carregava access token.
    const { apiClient } = await importarApiClient()

    servidor.use(
      http.post('*/api/auth/login', () => HttpResponse.json({ erro: 'credenciais' }, { status: 401 })),
      http.post('*/api/auth/refresh', () => {
        contadorRefresh++
        return HttpResponse.json({ accessToken: 'x' })
      }),
    )

    await expect(apiClient.post('/api/auth/login', { email: 'a@b.c', password: 'errada' })).rejects.toThrow()
    expect(contadorRefresh).toBe(0)
  })

  it('erro que não é 401 (403, 500) atravessa sem tentar refresh', async () => {
    const { apiClient } = await importarApiClient()

    servidor.use(
      http.get('*/api/proibido', () => HttpResponse.json({ erro: 'não' }, { status: 403 })),
      http.get('*/api/quebrado', () => HttpResponse.json({ erro: 'boom' }, { status: 500 })),
      http.post('*/api/auth/refresh', () => {
        contadorRefresh++
        return HttpResponse.json({ accessToken: 'x' })
      }),
    )

    await expect(apiClient.get('/api/proibido')).rejects.toThrow()
    await expect(apiClient.get('/api/quebrado')).rejects.toThrow()
    expect(contadorRefresh).toBe(0)
  })

  it('refreshAccessToken usa axios cru e não passa pelos interceptors', async () => {
    const { refreshAccessToken } = await importarApiClient()

    let headerNoRefresh: string | null = 'sentinela'
    servidor.use(
      http.post('*/api/auth/refresh', ({ request }) => {
        headerNoRefresh = request.headers.get('authorization')
        return HttpResponse.json({ accessToken: 'token-do-cru' })
      }),
    )

    const { accessToken } = await refreshAccessToken()
    expect(accessToken).toBe('token-do-cru')
    // O axios cru não tem o interceptor de request — sem header Authorization.
    // Se um dia o refresh passar a passar pelos interceptors, uma falha de
    // refresh dispararia refresh de novo (loop) e este teste quebra.
    expect(headerNoRefresh).toBeNull()
  })
})
