import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useCatalogoStore } from '@/stores/catalogo'
import { refreshAccessToken } from '@/api/client'
import { decodeJwt } from '@/api/jwt'
import type { Papel } from '@/api/types'

let bootstrapping = false
let bootstrapped = false

/**
 * Dispara o carregamento do catálogo sem bloquear a navegação — o layout
 * renderiza a moldura sem esperar por ele, e o menu de ferramentas aparece
 * quando o catálogo chega. Idempotente: chamado a cada navegação até o
 * bootstrap, mas só efetua o request enquanto não houver catálogo carregado
 * nem carregamento em andamento (guardado dentro do próprio store).
 */
function carregarCatalogoEmParalelo() {
  const catalogo = useCatalogoStore()
  if (!catalogo.carregado && !catalogo.carregando && !catalogo.falhou) {
    void catalogo.carregar()
  }
}

export function registerGuards(router: Router) {
  router.beforeEach(async (to, _from, next) => {
    const auth = useAuthStore()
    const ui = useUiStore()

    // Set page title from route meta
    const titulo = (to.meta.titulo as string) || ''
    ui.setPageTitle(titulo)

    // ── Bootstrap: try refresh on first navigation after page load ──
    if (!bootstrapped) {
      if (auth.isAuthenticated) {
        // Sessão já restaurada do sessionStorage — nada a verificar
        bootstrapped = true
        auth.isInitializing = false
      } else if (!bootstrapping) {
        auth.isInitializing = true
        bootstrapping = true
        try {
          const res = await refreshAccessToken()
          // We have a new access token, but need user info — decode JWT
          const payload = decodeJwt(res.accessToken)
          if (!payload) throw new Error('Token inválido')
          auth.setSession(res.accessToken, {
            id: payload.sub,
            email: payload.email || '',
            nome: payload.nome || '',
            papel: payload.role as Papel,
            escritorioId: payload.escritorio_id || null,
            deveTrocarSenha: payload.deve_trocar_senha === 'true',
          })
        } catch {
          // No valid refresh token — proceed to login below
        } finally {
          bootstrapping = false
          bootstrapped = true
          auth.isInitializing = false
        }
      }
    }

    // ── Public routes — allow always ──
    if (to.meta.public) {
      if (to.name === 'login' && auth.isAuthenticated) {
        return next('/')
      }
      return next()
    }

    // ── Protected routes ──

    if (!auth.isAuthenticated) {
      return next({ name: 'login', query: { redirect: to.fullPath } })
    }

    const catalogo = useCatalogoStore()

    // Sem await de propósito: o catálogo não bloqueia a navegação, só chega
    // um instante depois e o menu de ferramentas aparece quando resolver.
    carregarCatalogoEmParalelo()

    // Senha provisória (definida por um admin): a navegação fica presa na tela
    // de troca. A exceção da própria rota evita o laço de redirecionamento.
    if (auth.usuario?.deveTrocarSenha && to.name !== 'trocar-senha') {
      return next({ name: 'trocar-senha' })
    }

    const requiredRoles = (to.meta.papeis as readonly Papel[] | undefined) ?? []
    if (requiredRoles.length > 0 && !auth.canAccess([...requiredRoles])) {
      return next('/')
    }

    // ── Rota de ferramenta (/f/:produto/...): produto precisa existir no
    // catálogo ativo e, para quem não é admin, estar contratado. Página
    // que a ferramenta não declara não é alcançável mesmo por endereço
    // direto — aqui SIM esperamos o catálogo: sem ele não há como decidir.
    const produtoCodigo = to.params.produto as string | undefined
    if (produtoCodigo) {
      if (!catalogo.carregado && !catalogo.falhou) {
        await catalogo.carregar()
      }

      const produto = catalogo.porCodigo(produtoCodigo)
      if (!produto || (!auth.isPlatformAdmin && !produto.contratado)) {
        return next('/')
      }

      const pagina = to.meta.pagina
      if (pagina && !produto.paginas.includes(pagina)) {
        // Visão geral não declarada cairia num loop se redirecionasse pra
        // ela mesma — só nesse caso o destino seguro é o hub.
        return next(pagina === 'visao-geral' ? '/' : `/f/${produtoCodigo}`)
      }
    }

    return next()
  })
}
