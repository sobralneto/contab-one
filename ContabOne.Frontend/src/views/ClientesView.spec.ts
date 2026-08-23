import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { createPinia, setActivePinia } from 'pinia'
import { http, HttpResponse } from 'msw'
import { servidor } from '@/testes/servidor'
import ClientesView from './ClientesView.vue'
import { useAuthStore } from '@/stores/auth'
import type { ClienteDto } from '@/api/types'

function cliente(id: string, codigo: string, nome: string): ClienteDto {
  return {
    id, codigo, nome, cnpjMascarado: '12.345.678/9012-34',
    certificadoValidade: '2027-12-31', certificadoNomeArquivo: null,
    escritorioNome: null, origem: 'Manual', atualizadoEm: new Date().toISOString(),
  }
}

const TODOS = [cliente('c1', '0001', 'Alfa Contabilidade'), cliente('c2', '0002', 'Beta Serviços')]

beforeEach(() => {
  setActivePinia(createPinia())
  const auth = useAuthStore()
  auth.setSession('token-teste', {
    id: 'u1', email: 'esc@nfse.local', nome: 'Esc', papel: 'EscritorioUsuario', escritorioId: 'e1',
  })
  servidor.use(
    http.get('*/api/clientes', ({ request }) => {
      const url = new URL(request.url)
      const busca = url.searchParams.get('busca') ?? ''
      const dados = TODOS.filter((c) => c.nome.toLowerCase().includes(busca.toLowerCase()))
      return HttpResponse.json({ total: dados.length, pagina: 1, tamanho: 20, dados })
    }),
  )
})

describe('ClientesView (integração com MSW)', () => {
  it('carrega a lista via API e renderiza os clientes', async () => {
    render(ClientesView)
    expect(await screen.findByText('Alfa Contabilidade')).toBeInTheDocument()
    expect(screen.getByText('Beta Serviços')).toBeInTheDocument()
  })

  it('filtra pela busca com debounce', async () => {
    const user = userEvent.setup()
    render(ClientesView)
    await screen.findByText('Alfa Contabilidade')

    await user.type(screen.getByPlaceholderText('Buscar por nome, código ou CNPJ...'), 'beta')
    await waitFor(() => {
      expect(screen.queryByText('Alfa Contabilidade')).not.toBeInTheDocument()
    })
    expect(screen.getByText('Beta Serviços')).toBeInTheDocument()
  })

  it('sem resultado mostra o estado vazio', async () => {
    const user = userEvent.setup()
    render(ClientesView)
    await screen.findByText('Alfa Contabilidade')

    await user.type(screen.getByPlaceholderText('Buscar por nome, código ou CNPJ...'), 'inexistente')
    await waitFor(() => {
      expect(screen.getByText('Nenhum cliente')).toBeInTheDocument()
    })
  })
})
