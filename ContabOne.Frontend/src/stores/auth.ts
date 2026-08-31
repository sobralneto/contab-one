import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { decodeJwt, isJwtExpired } from '@/api/jwt'
import { useCatalogoStore } from '@/stores/catalogo'
import {
  listarEscritoriosDisponiveis,
  trocarEscritorio as apiTrocarEscritorio,
} from '@/api/endpoints/auth'
import type { UsuarioDto, Papel, EscritorioVinculoDto } from '@/api/types'

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

  // Escritórios que a sessão pode colocar em foco, carregados de
  // /auth/escritorios-disponiveis. `undefined` distingue "ainda não carregou"
  // de "carregou e está vazio" — a topbar usa isso para o estado de loading.
  const escritoriosDisponiveis = ref<EscritorioVinculoDto[]>([])
  const carregandoEscritorios = ref(false)

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

  // Escritório em foco da sessão (id). null = PlatformAdmin operando sem foco.
  const focoEscritorioId = computed<string | null>(() => usuario.value?.escritorioId ?? null)

  // Nome do escritório em foco, resolvido da lista carregada. null quando ainda
  // não resolveu (loading) ou quando não há foco — a topbar distingue os dois.
  const focoEscritorioNome = computed<string | null>(() => {
    const foco = focoEscritorioId.value
    if (!foco) return null
    return escritoriosDisponiveis.value.find((e) => e.id === foco)?.nome ?? null
  })

  function setSession(token: string, user: UsuarioDto) {
    accessToken.value = token
    usuario.value = user
    sessionStorage.setItem(ACCESS_TOKEN_KEY, token)
  }

  function setAccessToken(token: string) {
    accessToken.value = token
    sessionStorage.setItem(ACCESS_TOKEN_KEY, token)

    // O token é a fonte da verdade da exigência de troca de senha E do foco.
    // Sem ressincronizar aqui, o token novo devolvido por /trocar-senha entraria
    // sem limpar a flag e o guard devolveria o usuário para a mesma tela; e a
    // troca de foco não refletiria o escritório novo no estado da sessão.
    if (usuario.value) {
      const payload = decodeJwt(token)
      if (payload) {
        usuario.value = {
          ...usuario.value,
          deveTrocarSenha: payload.deve_trocar_senha === 'true',
          escritorioId: payload.escritorio_id || null,
        }
      }
    }
  }

  async function carregarEscritorios() {
    carregandoEscritorios.value = true
    try {
      const res = await listarEscritoriosDisponiveis()
      escritoriosDisponiveis.value = res.escritorios
    } catch {
      // Falha aqui não derruba a sessão: a topbar simplesmente segue sem
      // o nome/opções até a próxima tentativa (a troca de foco re-tenta).
    } finally {
      carregandoEscritorios.value = false
    }
  }

  /**
   * Troca o escritório em foco: chama o endpoint, grava o novo token, descarta
   * o catálogo do escritório anterior e o recarrega para o novo. Lança em caso
   * de recusa (sem vínculo / escritório não operável) para a topbar explicar.
   */
  async function trocarFoco(escritorioId: string | null): Promise<void> {
    const res = await apiTrocarEscritorio({ escritorioId })
    setAccessToken(res.accessToken)
    useCatalogoStore().limpar()
    await useCatalogoStore().carregar()
    await carregarEscritorios()
  }

  function clearSession() {
    accessToken.value = null
    usuario.value = null
    escritoriosDisponiveis.value = []
    carregandoEscritorios.value = false
    sessionStorage.removeItem(ACCESS_TOKEN_KEY)

    // O catálogo é por sessão: sem isto, o menu de um escritório sobreviveria
    // ao login seguinte, de outro escritório, na mesma aba.
    useCatalogoStore().limpar()
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
    escritoriosDisponiveis,
    carregandoEscritorios,
    focoEscritorioId,
    focoEscritorioNome,
    setSession,
    setAccessToken,
    carregarEscritorios,
    trocarFoco,
    clearSession,
    canAccess,
  }
})
