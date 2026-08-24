<template>
  <!-- O botão fica no topbar; o modal é teleportado para fora dele. -->
  <button
    v-if="explicacao"
    class="btn-ajuda"
    type="button"
    title="Sobre esta página"
    aria-label="Sobre esta página"
    @click="abrirManual"
  >
    ?
  </button>

  <Teleport to="body">
    <div class="modal-overlay" v-if="visivel && explicacao" @click.self="fechar">
      <div class="modal-card" role="dialog" aria-modal="true">
        <div class="modal-selo">Sobre esta página</div>
        <h2 class="modal-title">{{ explicacao.titulo }}</h2>

        <p v-for="(paragrafo, i) in explicacao.paragrafos" :key="i" class="modal-p">
          {{ paragrafo }}
        </p>

        <p v-if="nota" class="modal-nota">{{ nota }}</p>

        <div class="modal-actions">
          <button type="button" class="btn-primary" @click="fechar">Entendi</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { EXPLICACOES_PAGINA } from '@/constants/explicacoesPagina'
import { listarPaginasVistas, marcarPaginaVista } from '@/api/endpoints/tour'

const route = useRoute()
const auth = useAuthStore()

// null enquanto carrega — sem isso o modal pisca antes de saber se já foi visto.
const vistas = ref<string[] | null>(null)
// Se a listagem falhar, a abertura automática fica desligada: sem conseguir
// gravar o "já vi", a explicação reapareceria a cada navegação.
const carregouVistas = ref(false)
const abertoManualmente = ref(false)

// Rota de ferramenta (/f/:produto/...): a identidade da página é
// `${produto}.${pagina}` — DET e NFS-e têm cada um o próprio "visto" para a
// mesma tela, mesmo que o texto explicativo seja o genérico dos dois. Rota
// transversal (sem :produto) continua identificada só pelo `name`, como
// sempre foi.
const paginaAtual = computed(() => {
  const produto = route.params.produto as string | undefined
  const pagina = (route.meta.pagina as string | undefined) ?? (route.name ? String(route.name) : '')
  return produto ? `${produto}.${pagina}` : pagina
})

// O texto tenta a chave específica da ferramenta primeiro e cai para o
// genérico da página — é o que deixa uma ferramenta nova (DET, e as
// seguintes) sem precisar de entrada própria em EXPLICACOES_PAGINA.
const explicacao = computed(() => {
  const especifica = EXPLICACOES_PAGINA[paginaAtual.value]
  if (especifica) return especifica
  const generico = route.meta.pagina as string | undefined
  return generico ? (EXPLICACOES_PAGINA[generico] ?? null) : null
})

const nota = computed(() => {
  const porPapel = explicacao.value?.notaPorPapel
  if (!porPapel || !auth.papel) return null
  return porPapel[auth.papel] ?? null
})

const visivel = computed(() => {
  if (!explicacao.value) return false
  if (abertoManualmente.value) return true
  if (!carregouVistas.value || vistas.value === null) return false
  return !vistas.value.includes(paginaAtual.value)
})

onMounted(async () => {
  try {
    vistas.value = await listarPaginasVistas()
    carregouVistas.value = true
  } catch {
    // Botão "?" continua funcionando; só a abertura automática fica de fora.
    vistas.value = []
  }
})

// Trocar de rota fecha a abertura manual — senão o modal da página anterior
// continuaria aberto sobre a nova.
watch(paginaAtual, () => {
  abertoManualmente.value = false
})

function abrirManual() {
  abertoManualmente.value = true
}

async function fechar() {
  const pagina = paginaAtual.value
  const eraManual = abertoManualmente.value
  abertoManualmente.value = false

  // Reabrir pelo "?" não deve regravar o que já está marcado.
  if (eraManual || vistas.value?.includes(pagina)) return

  // Otimista: marca local antes da API para o modal não reaparecer se a
  // requisição demorar ou falhar.
  vistas.value = [...(vistas.value ?? []), pagina]

  try {
    await marcarPaginaVista(pagina)
  } catch {
    // Fica valendo só nesta sessão; na próxima o usuário vê de novo.
  }
}
</script>

<style scoped>
.btn-ajuda {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 700;
  font-family: var(--font-family);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 120ms ease;
}

.btn-ajuda:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--accent-suave);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1002;
}

.modal-card {
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 28px;
  max-width: 520px;
  width: 90%;
  box-shadow: var(--shadow-lg);
}

.modal-selo {
  display: inline-block;
  font-size: 10.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--accent);
  background: var(--accent-suave);
  padding: 3px 10px;
  border-radius: 10px;
  margin-bottom: 12px;
}

.modal-title {
  font-size: 19px;
  font-weight: 700;
  margin: 0 0 14px;
  letter-spacing: -0.01em;
  color: var(--text-primary);
}

.modal-p {
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0 0 12px;
}

.modal-nota {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  background: var(--surface-page);
  border-left: 3px solid var(--accent);
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  margin: 0 0 12px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.btn-primary {
  height: 38px;
  padding: 0 20px;
  background: var(--accent-gradient);
  color: var(--accent-gradient-texto);
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font-family);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(var(--accent-rgb), 0.25);
  transition: all 150ms ease;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(var(--accent-rgb), 0.35);
}
</style>
