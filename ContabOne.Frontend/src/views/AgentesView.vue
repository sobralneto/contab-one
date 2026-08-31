<template>
  <div class="agentes-view animate-fade-in">
    <div class="view-header">
      <h1>Agentes</h1>
      <button class="btn-primary" @click="abrirGerarChave">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Gerar nova chave
      </button>
    </div>

    <div class="table-card">
      <table class="data-table" v-if="agentes.length > 0">
        <thead>
          <tr>
            <th>Nome</th>
            <th>Ferramenta</th>
            <th v-if="auth.isPlatformAdmin">Escritório</th>
            <th>Chave</th>
            <th>Versão</th>
            <th>Criado em</th>
            <th>Último contato</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in agentes" :key="a.id">
            <td class="col-nome">{{ a.nome }}</td>
            <td class="col-produto">
              <span class="produto-chip">{{ a.produtoNome }}</span>
            </td>
            <td v-if="auth.isPlatformAdmin" class="col-escritorio">{{ a.escritorioNome || '—' }}</td>
            <td class="col-chave"><code>{{ a.produtoCodigo }}_{{ a.apiKeyPrefixo }}_…</code></td>
            <td class="col-versao">{{ a.versaoAgente || '—' }}</td>
            <td class="col-criado">{{ formatDate(a.criadoEm) }}</td>
            <td class="col-contato">{{ a.ultimoContatoEm ? formatRelativeTime(a.ultimoContatoEm) : 'Nunca' }}</td>
            <td>
              <span class="status-chip" :class="a.ativo ? 'status-ok' : 'status-err'">
                {{ a.ativo ? 'Ativo' : 'Revogado' }}
              </span>
            </td>
            <td class="col-actions">
              <button
                v-if="a.ativo"
                class="btn-revogar"
                @click="confirmarRevogar(a)"
                title="Revogar chave"
              >
                Revogar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <EstadoVazio
        v-else-if="!loading"
        title="Nenhum agente"
        description="Gere uma chave de API para conectar o agente instalado na máquina do escritório."
        action-label="Gerar nova chave"
        @action="abrirGerarChave"
      />
      <div v-if="loading" class="loading-msg">Carregando...</div>
    </div>

    <!-- Modal: escolher a ferramenta (e o escritório, se admin) antes de gerar -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="gerarModal">
        <div class="modal-card animate-fade-in">
          <h2 class="modal-title">Nova chave de agente</h2>
          <p class="modal-desc">
            A chave vale para uma ferramenta só — o prefixo dela identifica qual.
          </p>
          <form @submit.prevent="confirmarGerar" class="modal-form">
            <!-- Escritório primeiro: é ele que determina quais ferramentas
                 estão contratadas, então a lista abaixo depende desta escolha. -->
            <div class="form-field" v-if="auth.isPlatformAdmin">
              <label>Escritório <span class="req">*</span></label>
              <select
                name="escritorio"
                v-model="escritorioSelecionado"
                required
                @change="carregarProdutos"
              >
                <option :value="null" disabled>Selecione o escritório</option>
                <option v-for="e in escritorios" :key="e.id" :value="e.id">{{ e.nome }}</option>
              </select>
            </div>
            <div class="form-field">
              <label>Ferramenta <span class="req">*</span></label>
              <select
                name="produto"
                v-model="produtoSelecionado"
                required
                :disabled="loadingProdutos || (auth.isPlatformAdmin && !escritorioSelecionado)"
              >
                <option :value="null" disabled>
                  {{ loadingProdutos ? 'Carregando...' : 'Selecione a ferramenta' }}
                </option>
                <option v-for="p in produtos" :key="p.id" :value="p.id">
                  {{ p.nome }}{{ p.descricao ? ` — ${p.descricao}` : '' }}
                </option>
              </select>
              <span class="form-hint" v-if="produtoEscolhido">
                A chave começará com <code>{{ produtoEscolhido.codigo }}_</code>
              </span>
              <span class="form-hint" v-else-if="auth.isPlatformAdmin && !escritorioSelecionado">
                Escolha o escritório para ver as ferramentas que ele contratou.
              </span>
              <span class="form-hint" v-else-if="!loadingProdutos && produtos.length === 0">
                Nenhuma ferramenta contratada. Habilite uma em Escritórios antes
                de gerar a chave.
              </span>
            </div>
            <div class="modal-actions">
              <button type="button" class="btn-secondary" @click="fecharGerarModal">Cancelar</button>
              <button type="submit" class="btn-primary" :disabled="gerandoChave">
                {{ gerandoChave ? 'Gerando...' : 'Gerar chave' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Modal: Gerar chave -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="chaveModal">
        <div class="modal-card animate-fade-in">
          <h2 class="modal-title">Nova chave de agente</h2>
          <div class="chave-aviso">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            Esta chave será exibida <strong>apenas uma vez</strong>.
            Copie-a agora e configure no <code>config.toml</code> do agente.
          </div>
          <div class="chave-display">
            <code class="chave-valor">{{ novaChave }}</code>
            <button class="btn-copiar" @click="copiarChave">
              {{ copiado ? '✓ Copiado!' : 'Copiar' }}
            </button>
          </div>
          <div class="modal-actions">
            <button class="btn-secondary" @click="fecharChaveModal">Fechar</button>
          </div>
        </div>
      </div>
    </Teleport>

    <ConfirmarAcao
      :visible="revogarModal"
      title="Revogar chave do agente"
      :message="`Tem certeza que deseja revogar a chave de ${agenteRevogar?.nome}? O agente perderá o acesso no próximo handshake.`"
      confirm-label="Revogar"
      @confirm="executarRevogacao"
      @cancel="revogarModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import EstadoVazio from '@/components/comum/EstadoVazio.vue'
import ConfirmarAcao from '@/components/comum/ConfirmarAcao.vue'
import { listarAgentes, criarAgente, revogarAgente } from '@/api/endpoints/agentes'
import { listarEscritorios } from '@/api/endpoints/admin'
import type { AgenteDto, EscritorioDto, ProdutoDto } from '@/api/types'
import { listarProdutos } from '@/api/endpoints/produtos'
import { useFormatters } from '@/composables/useFormatters'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const { formatDate, formatRelativeTime } = useFormatters()

const loading = ref(true)
const agentes = ref<AgenteDto[]>([])
const escritorios = ref<EscritorioDto[]>([])

// Catálogo de ferramentas: vem do banco via API, não de lista fixa no front.
const produtos = ref<ProdutoDto[]>([])
const loadingProdutos = ref(false)

const chaveModal = ref(false)
const novaChave = ref('')
const copiado = ref(false)

// Escolha da ferramenta (todos) e do escritório (só admin) antes de gerar
const gerarModal = ref(false)
const produtoSelecionado = ref<string | null>(null)
const escritorioSelecionado = ref<string | null>(null)
const gerandoChave = ref(false)

const produtoEscolhido = computed(() =>
  produtos.value.find((p) => p.id === produtoSelecionado.value) ?? null,
)

// Ferramentas CONTRATADAS pelo escritório em questão — para o admin isso
// muda a cada escritório escolhido, então a lista é recarregada, não cacheada.
//
// A API devolve o catálogo ativo INTEIRO (a navegação por domínio precisa do
// que NÃO foi contratado também, para mostrar como indisponível no hub) —
// aqui, que é o seletor de uma chave nova, o filtro por `contratado` é quem
// decide o que aparece. `temAgente` filtra além disso: ferramenta sem agente
// (ex.: pgdas) nunca deveria ser destino de uma chave — nenhum binário vai
// usá-la (catalogo-dominios-ferramentas, "A ferramenta declara se tem agente").
async function carregarProdutos() {
  produtoSelecionado.value = null
  produtos.value = []

  if (auth.isPlatformAdmin && !escritorioSelecionado.value) return

  loadingProdutos.value = true
  try {
    const catalogo = await listarProdutos(escritorioSelecionado.value ?? undefined)
    produtos.value = catalogo.filter((p) => p.contratado && p.temAgente)
    if (produtos.value.length === 1) produtoSelecionado.value = produtos.value[0].id
  } catch { /* interceptor handles */ } finally {
    loadingProdutos.value = false
  }
}

async function abrirGerarChave() {
  gerarModal.value = true
  // Carrega na abertura, não no mount: quem só está conferindo a lista de
  // agentes não precisa da chamada.
  if (!auth.isPlatformAdmin) await carregarProdutos()
}

function fecharGerarModal() {
  gerarModal.value = false
  escritorioSelecionado.value = null
  produtoSelecionado.value = null
  if (auth.isPlatformAdmin) produtos.value = []
}

async function confirmarGerar() {
  await gerarChave(escritorioSelecionado.value ?? undefined)
}

async function gerarChave(escritorioId?: string) {
  const produto = produtoEscolhido.value
  if (!produto) return

  gerandoChave.value = true
  try {
    const nome = `Agente ${produto.nome} ${new Date().toLocaleDateString('pt-BR')}`
    const res = await criarAgente({ nome, produtoId: produto.id, escritorioId })
    novaChave.value = res.apiKey
    copiado.value = false
    gerarModal.value = false
    chaveModal.value = true
    carregar()
  } catch { /* interceptor handles */ } finally {
    gerandoChave.value = false
  }
}

function fecharChaveModal() {
  chaveModal.value = false
  novaChave.value = ''
}

async function copiarChave() {
  try {
    await navigator.clipboard.writeText(novaChave.value)
    copiado.value = true
    setTimeout(() => (copiado.value = false), 2000)
  } catch { /* fallback */ }
}

const revogarModal = ref(false)
const agenteRevogar = ref<AgenteDto | null>(null)

function confirmarRevogar(a: AgenteDto) {
  agenteRevogar.value = a
  revogarModal.value = true
}

async function executarRevogacao() {
  if (!agenteRevogar.value) return
  try {
    await revogarAgente(agenteRevogar.value.id)
    revogarModal.value = false
    agenteRevogar.value = null
    carregar()
  } catch { /* interceptor handles */ }
}

async function carregar() {
  loading.value = true
  try {
    agentes.value = await listarAgentes()
    if (auth.isPlatformAdmin) {
      escritorios.value = await listarEscritorios()
    }
  } catch { /* interceptor handles */ } finally {
    loading.value = false
  }
}

onMounted(carregar)
</script>

<style scoped>
.agentes-view { max-width: 1100px; }

.col-nome { font-weight: 500; }
.col-escritorio { font-size: 13px; color: var(--text-secondary); }
.produto-chip {
  display: inline-block; font-size: 11px; font-weight: 600;
  padding: 3px 10px; border-radius: 12px; letter-spacing: 0.02em;
  background: var(--accent-suave); color: var(--accent);
}
.col-chave code { font-size: 12px; color: var(--text-muted); background: var(--surface-page); padding: 3px 8px; border-radius: 4px; }
.col-versao { font-size: 13px; color: var(--text-muted); }
.col-criado { font-size: 13px; color: var(--text-secondary); white-space: nowrap; }
.col-contato { font-size: 13px; color: var(--text-secondary); }

.btn-revogar {
  background: none; border: 1px solid var(--border);
  color: var(--erro); border-radius: var(--radius-sm);
  padding: 4px 12px; font-size: 12px; font-weight: 500;
  font-family: var(--font-family); cursor: pointer; transition: all 120ms;
}
.btn-revogar:hover { background: var(--erro-suave); border-color: var(--erro); }

.modal-card { max-width: 540px; }
.modal-title { margin: 0 0 16px; }
.modal-desc { font-size: 13px; color: var(--text-secondary); margin: 0 0 16px; }
.form-hint { font-size: 12px; color: var(--text-muted); }
.form-hint code { font-family: var(--font-mono); background: var(--surface-page); padding: 1px 5px; border-radius: 3px; }

.chave-aviso {
  font-size: 13px; color: var(--atencao); background: var(--atencao-suave);
  border: 1px solid var(--atencao); border-radius: var(--radius-sm);
  padding: 12px 14px; margin-bottom: 16px; line-height: 1.6;
  display: flex; align-items: flex-start; gap: 8px;
}
.chave-aviso svg { flex-shrink: 0; margin-top: 1px; }
.chave-aviso code { background: rgba(0,0,0,0.06); padding: 1px 5px; border-radius: 3px; font-size: 12px; }
.dark .chave-aviso code { background: rgba(255,255,255,0.1); }

.chave-display { display: flex; gap: 8px; margin-bottom: 20px; }
.chave-valor {
  flex: 1; height: 42px; display: flex; align-items: center;
  padding: 0 12px; background: var(--surface-page);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 13px; font-family: var(--font-mono); overflow-x: auto; white-space: nowrap;
}
.btn-copiar {
  height: 42px; padding: 0 16px; background: var(--accent); color: #fff;
  border: none; border-radius: var(--radius-sm);
  font-size: 13px; font-weight: 600; font-family: var(--font-family); cursor: pointer; white-space: nowrap;
  transition: all 120ms;
}
.btn-copiar:hover { background: var(--accent-hover); }
</style>
