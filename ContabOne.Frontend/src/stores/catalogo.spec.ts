import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useCatalogoStore } from './catalogo'
import type { ProdutoDto } from '@/api/types'

vi.mock('@/api/endpoints/produtos', () => ({
  listarProdutos: vi.fn(),
}))

function produto(over: Partial<ProdutoDto>): ProdutoDto {
  return {
    id: over.id ?? 'p1',
    codigo: over.codigo ?? 'nfse',
    nome: over.nome ?? 'NFS-e',
    descricao: '',
    ativo: true,
    ordem: 1,
    paginas: ['visao-geral'],
    dominio: over.dominio ?? { codigo: 'fiscal', nome: 'Fiscal', ordem: 1, icone: null },
    contratado: true,
    ...over,
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
})

describe('stores/catalogo', () => {
  it('carregar popula produtos e marca carregado', async () => {
    const { listarProdutos } = await import('@/api/endpoints/produtos')
    vi.mocked(listarProdutos).mockResolvedValue([produto({})])

    const store = useCatalogoStore()
    await store.carregar()

    expect(store.produtos).toHaveLength(1)
    expect(store.carregado).toBe(true)
    expect(store.falhou).toBe(false)
    expect(store.carregando).toBe(false)
  })

  it('falha na carga marca falhou e não derruba o que já havia', async () => {
    const { listarProdutos } = await import('@/api/endpoints/produtos')
    vi.mocked(listarProdutos).mockRejectedValue(new Error('offline'))

    const store = useCatalogoStore()
    await store.carregar()

    expect(store.falhou).toBe(true)
    expect(store.carregado).toBe(false)
    expect(store.produtos).toEqual([])
  })

  it('porDominio agrupa e ordena pela ordem do domínio', async () => {
    const { listarProdutos } = await import('@/api/endpoints/produtos')
    vi.mocked(listarProdutos).mockResolvedValue([
      produto({ id: 'p-det', codigo: 'det', dominio: { codigo: 'dp', nome: 'DP', ordem: 2, icone: null } }),
      produto({ id: 'p-nfse', codigo: 'nfse', dominio: { codigo: 'fiscal', nome: 'Fiscal', ordem: 1, icone: null } }),
    ])

    const store = useCatalogoStore()
    await store.carregar()

    expect(store.porDominio.map((g) => g.dominio.codigo)).toEqual(['fiscal', 'dp'])
    expect(store.porDominio[0].produtos.map((p) => p.codigo)).toEqual(['nfse'])
  })

  it('limpar reseta produtos e as flags de estado', async () => {
    const { listarProdutos } = await import('@/api/endpoints/produtos')
    vi.mocked(listarProdutos).mockResolvedValue([produto({})])

    const store = useCatalogoStore()
    await store.carregar()
    expect(store.carregado).toBe(true)

    store.limpar()

    expect(store.produtos).toEqual([])
    expect(store.carregado).toBe(false)
    expect(store.falhou).toBe(false)
  })
})
