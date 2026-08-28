<template>
  <div class="clientes-view animate-fade-in">
    <!-- Header -->
    <div class="view-header">
      <h1>Clientes</h1>
      <button class="btn-primary" @click="abrirCriar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Novo cliente
      </button>
    </div>

    <!-- Search + Filtros -->
    <div class="view-toolbar">
      <div class="search-wrapper">
        <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          v-model="busca"
          type="text"
          placeholder="Buscar por nome, código ou CNPJ..."
          class="search-input"
          @input="onSearchInput"
        />
      </div>
      <div class="filtros">
        <select v-if="auth.isPlatformAdmin" v-model="filtroEscritorioId" class="filtro-select" @change="aplicarFiltros">
          <option :value="null">Todos os escritórios</option>
          <option v-for="e in escritorios" :key="e.id" :value="e.id">{{ e.nome }}</option>
        </select>
        <select v-else v-model="filtroDiasVencimento" class="filtro-select" @change="aplicarFiltros">
          <option :value="null">Todos os certificados</option>
          <option :value="1">Vence em 1 dia</option>
          <option :value="2">Vence em 2 dias</option>
          <option :value="3">Vence em 3 dias</option>
          <option :value="7">Vence em 7 dias</option>
          <option :value="15">Vence em 15 dias</option>
        </select>
      </div>
    </div>

    <!-- Table -->
    <div class="table-card">
      <table class="data-table" v-if="clientes.length > 0">
        <thead>
          <tr>
            <th>Código</th>
            <th>Nome</th>
            <th v-if="auth.isPlatformAdmin">Escritório</th>
            <th>CNPJ</th>
            <th>Certificado</th>
            <th class="text-right">Atualizado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in clientes" :key="c.id">
            <td class="col-codigo">{{ c.codigo }}</td>
            <td class="col-nome">{{ c.nome }}</td>
            <td v-if="auth.isPlatformAdmin" class="col-escritorio">{{ c.escritorioNome || '—' }}</td>
            <td class="col-cnpj tabular-nums">{{ formatCnpj(c.cnpjMascarado) }}</td>
            <td>
              <span class="cert-chip" :class="certClass(c.certificadoValidade)">
                {{ certLabel(c.certificadoValidade) }}
              </span>
            </td>
            <td class="text-right text-muted col-data">
              {{ formatDate(c.atualizadoEm) }}<br />
              <span class="origem-tag">{{ c.origem === 'Agente' ? 'via agente' : 'manual' }}</span>
            </td>
            <td class="col-actions">
              <button class="btn-icon" @click="abrirEditar(c)" title="Editar">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button class="btn-icon btn-icon--danger" @click="confirmarExcluir(c)" title="Excluir">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <EstadoVazio
        v-else-if="!loading"
        title="Nenhum cliente"
        description="Clientes são cadastrados manualmente ou enviados automaticamente pelo agente."
        action-label="Novo cliente"
        @action="abrirCriar"
      />
      <div v-if="loading" class="loading-msg">Carregando...</div>
    </div>

    <!-- Paginação -->
    <div class="paginacao" v-if="total > tamanho">
      <span class="paginacao-info">
        {{ (pagina - 1) * tamanho + 1 }}–{{ Math.min(pagina * tamanho, total) }} de {{ total }}
      </span>
      <button :disabled="pagina <= 1" @click="pagina--; carregar()">‹ Anterior</button>
      <button :disabled="pagina * tamanho >= total" @click="pagina++; carregar()">Próxima ›</button>
    </div>

    <!-- Modal: Criar/Editar -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="modalAberto">
        <div class="modal-card animate-fade-in">
          <h2 class="modal-title">{{ editando ? 'Editar cliente' : 'Novo cliente' }}</h2>
          <form @submit.prevent="salvar" class="modal-form">
            <div class="form-field" v-if="auth.isPlatformAdmin">
              <label>Escritório <span class="req">*</span></label>
              <select v-model="form.escritorioId" :disabled="editando" required>
                <option :value="null" disabled>Selecione o escritório</option>
                <option v-for="e in escritorios" :key="e.id" :value="e.id">{{ e.nome }}</option>
              </select>
            </div>
            <div class="form-field">
              <label>Código <span class="req">*</span></label>
              <input v-model="form.codigo" required maxlength="20" :disabled="editando" />
            </div>
            <div class="form-field">
              <label>Nome <span class="req">*</span></label>
              <input v-model="form.nome" required maxlength="200" />
            </div>
            <div class="form-field">
              <label>CNPJ</label>
              <input v-model="cnpj" placeholder="00.000.000/0000-00" maxlength="18" inputmode="numeric"
                :disabled="editando && clienteEdit?.origem === 'Agente'" />
              <span class="field-hint" v-if="editando && clienteEdit?.origem === 'Agente'">
                Atualizado automaticamente pelo agente
              </span>
            </div>
            <div class="form-field">
              <label>Validade do certificado</label>
              <input v-model="form.certificadoValidade" type="date"
                :disabled="editando && clienteEdit?.origem === 'Agente'" />
              <span class="field-hint" v-if="editando && clienteEdit?.origem === 'Agente'">
                Atualizado automaticamente pelo agente
              </span>
            </div>
            <div class="modal-actions">
              <button type="button" class="btn-secondary" @click="fecharModal">Cancelar</button>
              <button type="submit" class="btn-primary" :disabled="salvando">
                {{ salvando ? 'Salvando...' : 'Salvar' }}
              </button>
            </div>
            <p class="erro-modal" v-if="erroSalvar">✗ {{ erroSalvar }}</p>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Confirmar exclusão -->
    <ConfirmarAcao
      :visible="deleteModal"
      title="Excluir cliente"
      :message="`Tem certeza que deseja excluir ${clienteDelete?.codigo} — ${clienteDelete?.nome}?`"
      confirm-label="Excluir"
      @confirm="executarExclusao"
      @cancel="deleteModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import EstadoVazio from '@/components/comum/EstadoVazio.vue'
import ConfirmarAcao from '@/components/comum/ConfirmarAcao.vue'
import {
  listarClientes,
  criarCliente,
  atualizarCliente,
  excluirCliente,
} from '@/api/endpoints/clientes'
import { listarEscritorios } from '@/api/endpoints/admin'
import type { ClienteDto, EscritorioDto } from '@/api/types'
import { useFormatters } from '@/composables/useFormatters'
import { useInputMask } from '@/composables/useInputMask'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const { formatCnpj, formatDate } = useFormatters()
const { cnpjMask } = useInputMask()

const cnpj = computed({
  get: () => form.value.cnpjMascarado,
  set: (v: string) => (form.value.cnpjMascarado = cnpjMask(v)),
})

const loading = ref(true)
const clientes = ref<ClienteDto[]>([])
const escritorios = ref<EscritorioDto[]>([])
const busca = ref('')
const filtroEscritorioId = ref<string | null>(null)
const filtroDiasVencimento = ref<number | null>(null)
const pagina = ref(1)
const tamanho = 20
const total = ref(0)

let searchTimer: ReturnType<typeof setTimeout> | null = null

const modalAberto = ref(false)
const editando = ref(false)
const clienteEdit = ref<ClienteDto | null>(null)
const salvando = ref(false)
const erroSalvar = ref('')
const form = ref({ codigo: '', nome: '', cnpjMascarado: '', certificadoValidade: '', escritorioId: null as string | null })

const deleteModal = ref(false)
const clienteDelete = ref<ClienteDto | null>(null)

function certClass(validade: string | null): string {
  if (!validade) return 'cert-unknown'
  const d = new Date(validade)
  const hoje = new Date()
  const dias = Math.ceil((d.getTime() - hoje.getTime()) / 86_400_000)
  if (dias < 0) return 'cert-vencido'
  if (dias <= 30) return 'cert-vencendo'
  return 'cert-ok'
}

function certLabel(validade: string | null): string {
  if (!validade) return '—'
  const d = new Date(validade)
  const hoje = new Date()
  const dias = Math.ceil((d.getTime() - hoje.getTime()) / 86_400_000)
  const fmt = d.toLocaleDateString('pt-BR')
  if (dias < 0) return `Vencido (${fmt})`
  if (dias === 0) return `Vence hoje`
  if (dias <= 30) return `Vence em ${dias} dias`
  return `Válido até ${fmt}`
}

async function carregar() {
  loading.value = true
  try {
    const res = await listarClientes({
      busca: busca.value || undefined,
      escritorioId: auth.isPlatformAdmin ? (filtroEscritorioId.value ?? undefined) : undefined,
      diasVencimentoCert: !auth.isPlatformAdmin ? (filtroDiasVencimento.value ?? undefined) : undefined,
      pagina: pagina.value,
      tamanho,
    })
    clientes.value = res.dados
    total.value = res.total
  } catch { /* interceptor handles */ } finally {
    loading.value = false
  }
}

async function carregarEscritorios() {
  if (!auth.isPlatformAdmin) return
  try {
    escritorios.value = await listarEscritorios()
  } catch { /* interceptor handles */ }
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    pagina.value = 1
    carregar()
  }, 300)
}

function aplicarFiltros() {
  pagina.value = 1
  carregar()
}

function abrirCriar() {
  editando.value = false
  clienteEdit.value = null
  form.value = { codigo: '', nome: '', cnpjMascarado: '', certificadoValidade: '', escritorioId: null }
  erroSalvar.value = ''
  modalAberto.value = true
}

function abrirEditar(c: ClienteDto) {
  editando.value = true
  clienteEdit.value = c
  form.value = {
    codigo: c.codigo,
    nome: c.nome,
    cnpjMascarado: c.cnpjMascarado,
    certificadoValidade: c.certificadoValidade ?? '',
    escritorioId: null, // escritório não é alterável na edição
  }
  erroSalvar.value = ''
  modalAberto.value = true
}

function fecharModal() { modalAberto.value = false }

async function salvar() {
  salvando.value = true
  erroSalvar.value = ''
  try {
    const payload: Record<string, string | undefined> = {
      codigo: form.value.codigo,
      nome: form.value.nome,
      cnpjMascarado: form.value.cnpjMascarado || undefined,
      certificadoValidade: form.value.certificadoValidade || undefined,
      escritorioId: form.value.escritorioId ?? undefined,
    }
    if (editando.value && clienteEdit.value) {
      await atualizarCliente(clienteEdit.value.id, payload as any)
    } else {
      await criarCliente(payload as any)
    }
    fecharModal()
    carregar()
  } catch (e: any) {
    erroSalvar.value = e?.response?.data?.erro || 'Não foi possível salvar o cliente.'
  } finally {
    salvando.value = false
  }
}

function confirmarExcluir(c: ClienteDto) {
  clienteDelete.value = c
  deleteModal.value = true
}

async function executarExclusao() {
  if (!clienteDelete.value) return
  try {
    await excluirCliente(clienteDelete.value.id)
    deleteModal.value = false
    clienteDelete.value = null
    carregar()
  } catch { /* interceptor handles */ }
}

onMounted(() => {
  carregar()
  carregarEscritorios()
})
</script>

<style scoped>
.clientes-view { max-width: 1200px; }

.view-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; margin-bottom: 12px; flex-wrap: wrap;
}

.search-wrapper {
  position: relative; max-width: 380px; flex: 1;
}

.filtros { display: flex; gap: 8px; }

.filtro-select {
  height: 40px; padding: 0 12px;
  border: 1px solid var(--border); border-radius: var(--radius-md);
  font-size: 13px; font-family: var(--font-family);
  background: var(--surface-card); color: var(--text-primary); outline: none;
  transition: border-color 150ms, box-shadow 150ms;
}
.filtro-select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-suave); }
.search-icon {
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  color: var(--text-muted); pointer-events: none;
}
.search-input {
  width: 100%; height: 40px; padding: 0 12px 0 38px;
  border: 1px solid var(--border); border-radius: var(--radius-md);
  font-size: 13px; font-family: var(--font-family);
  background: var(--surface-card); color: var(--text-primary); outline: none;
  transition: all 150ms ease;
}
.search-input:focus {
  border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-suave);
}

.col-codigo { width: 70px; font-weight: 600; font-variant-numeric: tabular-nums; color: var(--accent); }
.col-escritorio { font-size: 13px; color: var(--text-secondary); }
.col-cnpj { width: 140px; font-size: 13px; }
.col-data { width: 100px; font-size: 12px; line-height: 1.5; }

.cert-chip {
  display: inline-block; font-size: 11px; font-weight: 600;
  padding: 3px 10px; border-radius: 12px; white-space: nowrap; letter-spacing: 0.02em;
}
.cert-ok { background: var(--sucesso-suave); color: var(--sucesso); }
.cert-vencendo { background: var(--atencao-suave); color: var(--atencao); }
.cert-vencido { background: var(--erro-suave); color: var(--erro); }
.cert-unknown { color: var(--text-muted); }

.origem-tag { font-size: 11px; color: var(--text-muted); }

.paginacao {
  display: flex; align-items: center; justify-content: center;
  gap: 12px; margin-top: 16px; font-size: 13px;
}
.paginacao-info { color: var(--text-muted); }
.paginacao button {
  height: 34px; padding: 0 14px;
  background: var(--surface-card); color: var(--text-secondary);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 13px; font-family: var(--font-family); cursor: pointer;
  transition: all 120ms;
}
.paginacao button:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.paginacao button:disabled { opacity: 0.4; cursor: not-allowed; }

/* Modal */
.form-field input:disabled, .form-field select:disabled { opacity: 0.5; background: var(--border); }
.field-hint { font-size: 11px; color: var(--text-muted); }
.erro-modal { font-size: 13px; color: var(--erro); font-weight: 600; margin: 0; }
</style>
