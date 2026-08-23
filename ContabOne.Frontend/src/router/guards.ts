import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { refreshAccessToken } from '@/api/client'
import { decodeJwt } from '@/api/jwt'
import type { Papel } from '@/api/types'

let bootstrapping = false
let bootstrapped = false

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
        return next('/dashboard')
      }
      return next()
    }

    // ── Protected routes ──

    if (!auth.isAuthenticated) {
      return next({ name: 'login', query: { redirect: to.fullPath } })
    }

    // Senha provisória (definida por um admin): a navegação fica presa na tela
    // de troca. A exceção da própria rota evita o laço de redirecionamento.
    if (auth.usuario?.deveTrocarSenha && to.name !== 'trocar-senha') {
      return next({ name: 'trocar-senha' })
    }

    const requiredRoles = (to.meta.papeis as readonly Papel[] | undefined) ?? []
    if (requiredRoles.length > 0 && !auth.canAccess([...requiredRoles])) {
      return next('/dashboard')
    }

    return next()
  })
}
