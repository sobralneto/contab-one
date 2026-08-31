import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { createPinia, setActivePinia } from 'pinia'
import { http, HttpResponse } from 'msw'
import { servidor } from '@/testes/servidor'
import UsuariosView from './UsuariosView.vue'
import { useAuthStore } from '@/stores/auth'
import type { UsuarioListaDto, Papel } from '@/api/types'

function usuario(
  id: string,
  nome: string,
  papel: Papel,
  extras: Partial<UsuarioListaDto> = {},
): UsuarioListaDto {
  return {
    id,
    nome,
    email: `${id}@nfse.local`,
    papel,
    escritorios: [{ id: 'e1', nome: 'Contabilidade Silva ME' }],
    ativo: true,
    deveTrocarSenha: false,
    ultimoLoginEm: null,
    ...extras,
  }
}

const USUARIOS = [
  usuario('u1', 'Ana Souza', 'EscritorioAdmin'),
  usuario('u2', 'Bruno Lima', 'EscritorioUsuario', { deveTrocarSenha: true }),
]

function autenticarComo(papel: Papel) {
  const auth = useAuthStore()
  auth.setSession('token-teste', {
    id: 'logado',
    email: 'logado@nfse.local',
    nome: 'Usuário Logado',
    papel,
    escritorioId: papel === 'PlatformAdmin' ? null : 'e1',
    deveTrocarSenha: false,
  })
}

beforeEach(() => {
  setActivePinia(createPinia())
  servidor.use(
    http.get('*/api/usuarios', () => HttpResponse.json(USUARIOS)),
    http.get('*/api/admin/escritorios', () =>
      HttpResponse.json([{ id: 'e1', nome: 'Contabilidade Silva ME' }]),
    ),
  )
})

describe('UsuariosView (integração com MSW)', () => {
  it('carrega a lista via API e renderiza os usuários', async () => {
    autenticarComo('EscritorioAdmin')
    render(UsuariosView)

    expect(await screen.findByText('Ana Souza')).toBeInTheDocument()
    expect(screen.getByText('Bruno Lima')).toBeInTheDocument()
  })

  it('marca quem ainda está com senha provisória', async () => {
    autenticarComo('EscritorioAdmin')
    render(UsuariosView)
    await screen.findByText('Bruno Lima')

    expect(screen.getByText('senha provisória')).toBeInTheDocument()
  })

  it('admin de escritório vê a coluna de escritórios, com os vínculos que enxerga', async () => {
    autenticarComo('EscritorioAdmin')
    render(UsuariosView)
    await screen.findByText('Ana Souza')

    expect(screen.getByRole('columnheader', { name: 'Escritórios' })).toBeInTheDocument()
  })

  it('admin da plataforma vê a coluna de escritórios', async () => {
    autenticarComo('PlatformAdmin')
    render(UsuariosView)
    await screen.findByText('Ana Souza')

    expect(screen.getByRole('columnheader', { name: 'Escritórios' })).toBeInTheDocument()
  })

  it('admin de escritório não pode conceder o papel de plataforma', async () => {
    // Espelha a regra do servidor (403 em UsuariosEndpoints): esconder a opção
    // evita oferecer uma ação que a API vai recusar.
    const user = userEvent.setup()
    autenticarComo('EscritorioAdmin')
    render(UsuariosView)
    await screen.findByText('Ana Souza')

    await user.click(screen.getByRole('button', { name: '+ Novo usuário' }))

    expect(await screen.findByRole('option', { name: 'Admin do Escritório' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'Admin da Plataforma' })).not.toBeInTheDocument()
  })

  it('a senha provisória não usa campo do tipo password', async () => {
    // Regressão: com type="password" ao lado do campo de e-mail, o navegador
    // reconhece o modal como formulário de cadastro e salva a credencial do
    // usuário recém-criado no perfil do admin — que passava a vê-la
    // autocompletada na tela de login, sem sumir ao limpar dados do site.
    const user = userEvent.setup()
    autenticarComo('EscritorioAdmin')
    render(UsuariosView)
    await screen.findByText('Ana Souza')

    await user.click(screen.getByRole('button', { name: '+ Novo usuário' }))

    // O modal é teleportado para o body, fora do container do componente.
    const campo = document.querySelector<HTMLInputElement>('input[name="senha-provisoria"]')
    expect(campo).not.toBeNull()
    expect(campo!.type).toBe('text')
    expect(document.querySelector('input[type="password"]')).toBeNull()
  })

  it('a redefinição de senha também não usa campo do tipo password', async () => {
    const user = userEvent.setup()
    autenticarComo('EscritorioAdmin')
    render(UsuariosView)
    await screen.findByText('Ana Souza')

    await user.click(screen.getAllByTitle('Redefinir senha')[0])

    const campo = document.querySelector<HTMLInputElement>('input[name="nova-senha-provisoria"]')
    expect(campo).not.toBeNull()
    expect(campo!.type).toBe('text')
    expect(document.querySelector('input[type="password"]')).toBeNull()
  })

  it('admin da plataforma pode conceder o papel de plataforma', async () => {
    const user = userEvent.setup()
    autenticarComo('PlatformAdmin')
    render(UsuariosView)
    await screen.findByText('Ana Souza')

    await user.click(screen.getByRole('button', { name: '+ Novo usuário' }))

    expect(await screen.findByRole('option', { name: 'Admin da Plataforma' })).toBeInTheDocument()
  })
})
