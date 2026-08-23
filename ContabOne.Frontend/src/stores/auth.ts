import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { decodeJwt, isJwtExpired } from '@/api/jwt'
import type { UsuarioDto, Papel } from '@/api/types'

// sessionStorage (não localStorage): sobrevive a reload/HMR na mesma aba,
// mas some ao fechar a aba — o refresh token de longa duração continua
// sendo o cookie httpOnly, este é só o access token de curta duração.
const ACCESS_TOKEN_KEY = 'contabone_access_token'

function restaurarSessao(): { token: string; usuario: UsuarioDto } | null {
  const token = sessionStorage.getItem(ACCESS_TOKEN_KEY)
  if (!token || isJwtExpired(token)) return null

  const payload = decodeJwt(token)
  if (!payload) return null

  return {
    token,
    usuario: {
      id: payload.sub,
      email: payload.email || '',
      nome: payload.nome || '',
      papel: payload.role as Papel,
      escritorioId: payload.escritorio_id || null,
      deveTrocarSenha: payload.deve_trocar_senha === 'true',
    },
  }
}

export const useAuthStore = defineStore('auth', () => {
  const restaurado = restaurarSessao()

  const usuario = ref<UsuarioDto | null>(restaurado?.usuario ?? null)
  const accessToken = ref<string | null>(restaurado?.token ?? null)

  // Indica se a verificação inicial de sessão ainda está em andamento.
  // Começa `true` para que a UI nunca renderize a área autenticada
  // antes da confirmação do status — o router guard limpa a flag ao
  // concluir o bootstrap (sucesso ou falha).
  const isInitializing = ref(true)

  const isAuthenticated = computed(() => !!accessToken.value)
  const papel = computed<Papel | null>(() => usuario.value?.papel ?? null)
  const isPlatformAdmin = computed(() => papel.value === 'PlatformAdmin')
  const isEscritorioAdmin = computed(
    () => papel.value === 'EscritorioAdmin' || papel.value === 'PlatformAdmin',
  )

  function setSession(token: string, user: UsuarioDto) {
    accessToken.value = token
    usuario.value = user
    sessionStorage.setItem(ACCESS_TOKEN_KEY, token)
  }

  function setAccessToken(token: string) {
    accessToken.value = token
    sessionStorage.setItem(ACCESS_TOKEN_KEY, token)

    // O token é a fonte da verdade da exigência de troca de senha. Sem
    // ressincronizar aqui, o token novo devolvido por /trocar-senha entraria
    // sem limpar a flag e o guard devolveria o usuário para a mesma tela.
    if (usuario.value) {
      const payload = decodeJwt(token)
      if (payload) {
        usuario.value = {
          ...usuario.value,
          deveTrocarSenha: payload.deve_trocar_senha === 'true',
        }
      }
    }
  }

  function clearSession() {
    accessToken.value = null
    usuario.value = null
    sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  }

  function canAccess(requiredRoles: Papel[]): boolean {
    if (!papel.value) return false
    if (requiredRoles.length === 0) return true
    return requiredRoles.includes(papel.value)
  }

  return {
    usuario,
    accessToken,
    isInitializing,
    isAuthenticated,
    papel,
    isPlatformAdmin,
    isEscritorioAdmin,
    setSession,
    setAccessToken,
    clearSession,
    canAccess,
  }
})
