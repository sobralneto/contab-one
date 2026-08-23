import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import { http, HttpResponse } from 'msw'
import { servidor } from '@/testes/servidor'
import ExplicacaoPagina from './ExplicacaoPagina.vue'
import { useAuthStore } from '@/stores/auth'
import type { Papel } from '@/api/types'

const rotaVazia = { template: '<div />' }

async function montar(nomeRota: string, papel: Papel = 'EscritorioUsuario') {
  const auth = useAuthStore()
  auth.setSession('token-teste', {
    id: 'u1',
    email: 'u1@nfse.local',
    nome: 'Usuário Teste',
    papel,
    escritorioId: papel === 'PlatformAdmin' ? null : 'e1',
    deveTrocarSenha: false,
  })

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/dashboard', name: 'dashboard', component: rotaVazia },
      { path: '/clientes', name: 'clientes', component: rotaVazia },
      { path: '/sem-texto', name: 'sem-texto', component: rotaVazia },
    ],
  })

  await router.push({ name: nomeRota })
  await router.isReady()

  return render(ExplicacaoPagina, { global: { plugins: [router] } })
}

beforeEach(() => {
  setActivePinia(createPinia())
  servidor.use(http.get('*/api/tour', () => HttpResponse.json([])))
})

describe('ExplicacaoPagina', () => {
  it('abre sozinha na primeira visita da página', async () => {
    await montar('clientes')
    expect(await screen.findByText('Clientes')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Entendi' })).toBeInTheDocument()
  })

  it('não abre quando a página já foi vista', async () => {
    servidor.use(http.get('*/api/tour', () => HttpResponse.json(['clientes'])))
    await montar('clientes')

    // O botão "?" existe, mas o modal não deve aparecer sozinho.
    expect(await screen.findByRole('button', { name: 'Sobre esta página' })).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: 'Entendi' })).not.toBeInTheDocument()
    })
  })

  it('não renderiza nada em rota sem texto cadastrado', async () => {
    await montar('sem-texto')
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: 'Sobre esta página' })).not.toBeInTheDocument()
    })
    expect(screen.queryByRole('button', { name: 'Entendi' })).not.toBeInTheDocument()
  })

  it('mostra a nota específica do papel', async () => {
    await montar('dashboard', 'PlatformAdmin')
    expect(
      await screen.findByText(/os números somam todos os escritórios/i),
    ).toBeInTheDocument()
  })

  it('não mostra a nota de outro papel', async () => {
    await montar('dashboard', 'EscritorioUsuario')
    await screen.findByText('Dashboard')
    expect(screen.queryByText(/os números somam todos os escritórios/i)).not.toBeInTheDocument()
  })

  it('ao fechar, grava que a página foi vista', async () => {
    const marcadas: string[] = []
    servidor.use(
      http.post('*/api/tour/:pagina', ({ params }) => {
        marcadas.push(String(params.pagina))
        return HttpResponse.json({ pagina: params.pagina, vista: true })
      }),
    )

    const user = userEvent.setup()
    await montar('clientes')
    await user.click(await screen.findByRole('button', { name: 'Entendi' }))

    await waitFor(() => expect(marcadas).toEqual(['clientes']))
    expect(screen.queryByRole('button', { name: 'Entendi' })).not.toBeInTheDocument()
  })

  it('reabrir pelo "?" não regrava a página', async () => {
    const marcadas: string[] = []
    servidor.use(
      http.get('*/api/tour', () => HttpResponse.json(['clientes'])),
      http.post('*/api/tour/:pagina', ({ params }) => {
        marcadas.push(String(params.pagina))
        return HttpResponse.json({ pagina: params.pagina, vista: true })
      }),
    )

    const user = userEvent.setup()
    await montar('clientes')

    await user.click(await screen.findByRole('button', { name: 'Sobre esta página' }))
    expect(await screen.findByText('Clientes')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Entendi' }))
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: 'Entendi' })).not.toBeInTheDocument()
    })
    expect(marcadas).toEqual([])
  })

  it('se a listagem falhar, não abre sozinha mas o "?" continua funcionando', async () => {
    // Sem conseguir gravar o "já vi", abrir automaticamente faria a explicação
    // reaparecer a cada navegação.
    servidor.use(http.get('*/api/tour', () => new HttpResponse(null, { status: 500 })))

    const user = userEvent.setup()
    await montar('clientes')

    const botaoAjuda = await screen.findByRole('button', { name: 'Sobre esta página' })
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: 'Entendi' })).not.toBeInTheDocument()
    })

    await user.click(botaoAjuda)
    expect(await screen.findByText('Clientes')).toBeInTheDocument()
  })
})
