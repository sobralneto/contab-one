import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import type { ProdutoDto } from '@/api/types'

// O guards.ts guarda `bootstrapped` no escopo do módulo e a store lê
// sessionStorage na criação — os dois precisam estar limpos entre casos.
// vi.resetModules() + imports dinâmicos garantem isso (design.md, Decisão 4).
vi.mock('@/api/client', () => ({
  refreshAccessToken: vi.fn(),
}))

vi.mock('@/api/endpoints/produtos', () => ({
  listarProdutos: vi.fn(),
}))

const CHAVE = 'contabone_access_token'

// Fixture padrão: a maioria dos testes aqui não está exercitando o catálogo
// em si, só precisa que `/f/nfse/...` resolva normalmente (contratado, com
// todas as páginas) em vez de bater no guard de produto/página.
const NFSE_CONTRATADO: ProdutoDto = {
  id: 'p-nfse',
  codigo: 'nfse',
  nome: 'NFS-e',
  descricao: '',
  ativo: true,
  ordem: 1,
  paginas: ['visao-geral', 'execucoes', 'configuracao', 'regras'],
  dominio: { codigo: 'fiscal', nome: 'Fiscal', ordem: 1, icone: null },
  contratado: true,
}

function tokenComPapel(papel: string, exp = 1_800_000_000): string {
  const header = btoa(JSON.stringify({ alg: 'HS256' }))
  const corpo = btoa(JSON.stringify({
    sub: 'u1', email: 'a@b.c', nome: 'A', role: papel, exp,
  }))
  return `${header}.${corpo}.sig`
}

async function montarCenario() {
  const { refreshAccessToken } = await import('@/api/client')
  const { listarProdutos } = await import('@/api/endpoints/produtos')
  const { registerGuards } = await import('./guards')
  // router/index.ts exporta a instância como default — com vi.resetModules()
  // cada import dinâmico dá uma instância nova, que é o que cada caso precisa.
  const { default: router } = await import('./index')
  const { useAuthStore } = await import('@/stores/auth')
  const { useCatalogoStore } = await import('@/stores/catalogo')

  setActivePinia(createPinia())
  const auth = useAuthStore()
  const catalogo = useCatalogoStore()
  registerGuards(router)
  // Sem await router.isReady(): em jsdom não há mount do app, então a
  // navegação inicial só começa no primeiro push — e é o push que resolve
  // quando os guards concluem.
  return { router, auth, catalogo, refreshAccessToken, listarProdutos }
}

beforeEach(async () => {
  vi.resetModules()
  sessionStorage.clear()
  vi.restoreAllMocks()
  const { listarProdutos } = await import('@/api/endpoints/produtos')
  // restoreAllMocks não zera o histórico de chamadas de um vi.fn() vindo de
  // vi.mock (ele persiste entre testes do mesmo arquivo) — sem o clear
  // explícito, navegações protegidas de testes anteriores inflam a contagem
  // que os testes de catálogo abaixo verificam.
  vi.mocked(listarProdutos).mockClear()
  vi.mocked(listarProdutos).mockResolvedValue([NFSE_CONTRATADO])
})

describe('router/guards', () => {
  it('rota pública é liberada sem sessão', async () => {
    const { router } = await montarCenario()
    await router.push('/login')
    expect(router.currentRoute.value.name).toBe('login')
  })

  it('usuário autenticado em /login é redirecionado ao hub', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioUsuario'))
    const { router } = await montarCenario()
    await router.push('/login')
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('rota protegida sem sessão redireciona para login preservando o redirect', async () => {
    const { router } = await montarCenario()
    await router.push('/clientes')
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/clientes')
  })

  it('papel insuficiente para rota admin cai no hub', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioUsuario'))
    const { router } = await montarCenario()
    await router.push('/admin/planos')
    expect(router.currentRoute.value.path).toBe('/')
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

describe('router/guards — catálogo', () => {
  it('sessão confirmada dispara a carga do catálogo, sem bloquear a navegação', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioUsuario'))
    const { router, catalogo, listarProdutos } = await montarCenario()

    await router.push('/dashboard')

    expect(router.currentRoute.value.path).toBe('/f/nfse')
    expect(listarProdutos).toHaveBeenCalledTimes(1)
    expect(catalogo.carregado).toBe(true)
  })

  it('segunda navegação não repete a carga do catálogo já resolvido', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioUsuario'))
    const { router, listarProdutos } = await montarCenario()

    await router.push('/dashboard')
    await router.push('/clientes')

    expect(listarProdutos).toHaveBeenCalledTimes(1)
  })

  it('falha ao carregar o catálogo não derruba a sessão — devolve ao hub, não à ferramenta', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioUsuario'))
    const { listarProdutos } = await import('@/api/endpoints/produtos')
    vi.mocked(listarProdutos).mockRejectedValue(new Error('offline'))

    const { router, auth, catalogo } = await montarCenario()
    await router.push('/dashboard')

    // Sem catálogo não há como confirmar que "nfse" está contratado — o
    // guard nega por padrão e devolve ao hub, que é quem mostra o aviso e a
    // opção de tentar de novo (design.md, Risks).
    expect(router.currentRoute.value.path).toBe('/')
    expect(auth.isAuthenticated).toBe(true)
    expect(catalogo.falhou).toBe(true)
  })

  it('logout de um escritório não deixa catálogo para a sessão seguinte', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioUsuario'))
    const { router, auth, catalogo } = await montarCenario()

    await router.push('/dashboard')
    expect(catalogo.carregado).toBe(true)

    auth.clearSession()

    expect(catalogo.produtos).toEqual([])
    expect(catalogo.carregado).toBe(false)
  })
})

describe('router/guards — produto e página da ferramenta', () => {
  it('produto inexistente no catálogo devolve ao hub', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioUsuario'))
    const { router } = await montarCenario()

    await router.push('/f/inexistente')

    expect(router.currentRoute.value.path).toBe('/')
  })

  it('produto ativo mas não contratado devolve ao hub para usuário de escritório', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioUsuario'))
    const { listarProdutos } = await import('@/api/endpoints/produtos')
    vi.mocked(listarProdutos).mockResolvedValue([{ ...NFSE_CONTRATADO, contratado: false }])

    const { router } = await montarCenario()
    await router.push('/f/nfse')

    expect(router.currentRoute.value.path).toBe('/')
  })

  it('página não declarada pela ferramenta devolve à visão geral dela', async () => {
    // 'configuracao' já exige EscritorioAdmin/PlatformAdmin por papel — usa
    // um desses aqui para isolar o que este teste quer exercitar: a checagem
    // de página declarada, não o guard de papel (já coberto em outro teste).
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioAdmin'))
    const { listarProdutos } = await import('@/api/endpoints/produtos')
    vi.mocked(listarProdutos).mockResolvedValue([{ ...NFSE_CONTRATADO, paginas: ['visao-geral'] }])

    const { router } = await montarCenario()
    await router.push('/f/nfse/configuracao')

    expect(router.currentRoute.value.path).toBe('/f/nfse')
  })

  it('admin acessa ferramenta ativa mesmo sem tê-la contratado', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('PlatformAdmin'))
    const { listarProdutos } = await import('@/api/endpoints/produtos')
    vi.mocked(listarProdutos).mockResolvedValue([{ ...NFSE_CONTRATADO, contratado: false }])

    const { router } = await montarCenario()
    await router.push('/f/nfse')

    expect(router.currentRoute.value.path).toBe('/f/nfse')
  })

  it('regras é restrita a PlatformAdmin mesmo com EscritorioAdmin', async () => {
    // Configuração (papeis: [PlatformAdmin, EscritorioAdmin]) já é coberta
    // no teste de "página não declarada" acima — este cobre a página com a
    // restrição mais estrita, exclusiva de PlatformAdmin.
    sessionStorage.setItem(CHAVE, tokenComPapel('EscritorioAdmin'))
    const { router } = await montarCenario()

    await router.push('/f/nfse/regras')

    expect(router.currentRoute.value.path).toBe('/')
  })

  it('regras é acessível para PlatformAdmin', async () => {
    sessionStorage.setItem(CHAVE, tokenComPapel('PlatformAdmin'))
    const { router } = await montarCenario()

    await router.push('/f/nfse/regras')

    expect(router.currentRoute.value.path).toBe('/f/nfse/regras')
  })
})
