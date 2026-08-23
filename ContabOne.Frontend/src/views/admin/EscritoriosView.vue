<template>
  <div class="admin-view">
    <div class="view-header">
      <h1>Escritórios</h1>
      <button class="btn-primary" @click="abrirCriar">+ Novo escritório</button>
    </div>

    <div class="table-card">
      <table class="data-table" v-if="escritorios.length > 0">
        <thead>
          <tr>
            <th>Nome</th>
            <th>CNPJ</th>
            <th>Plano</th>
            <th>Status</th>
            <th class="text-right">Clientes</th>
            <th class="text-right">Agentes</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in escritorios" :key="e.id">
            <td class="col-nome">{{ e.nome }}</td>
            <td class="col-cnpj tabular-nums">{{ e.cnpjMascarado || '—' }}</td>
            <td>{{ e.planoNome || '—' }}</td>
            <td>
              <span class="status-chip" :class="statusClass(e.status)">
                {{ statusLabel(e.status) }}
              </span>
            </td>
            <td class="text-right tabular-nums">{{ e.totalClientes }}</td>
            <td class="text-right tabular-nums">{{ e.totalAgentes }}</td>
            <td class="col-actions">
              <button class="btn-edit" @click="abrirEditar(e)" title="Editar">✎</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="loading" class="loading-msg">Carregando...</div>
    </div>

    <!-- Modal: Criar/Editar -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="modalAberto">
        <div class="modal-card">
          <h2 class="modal-title">{{ editando ? 'Editar escritório' : 'Novo escritório' }}</h2>
          <form @submit.prevent="salvar" class="modal-form">
            <div class="form-field">
              <label>Nome <span class="req">*</span></label>
              <input v-model="form.nome" required />
            </div>
            <div class="form-field">
              <label>CNPJ</label>
              <input v-model="cnpj" placeholder="00.000.000/0000-00" maxlength="18" inputmode="numeric" />
            </div>
            <div class="form-field">
              <label>Plano</label>
              <select v-model="form.planoId">
                <option :value="null">—</option>
                <option v-for="p in planos" :key="p.id" :value="p.id">{{ p.nome }}</option>
              </select>
            </div>
            <div class="form-field">
              <label>Status</label>
              <select v-model="form.status" class="status-select">
                <option value="Ativo">Ativo</option>
                <option value="Inadimplente">Inadimplente</option>
                <option value="Suspenso">Suspenso</option>
                <option value="Cancelado">Cancelado</option>
              </select>
              <span class="field-hint" v-if="statusAlterado" :class="statusHintClass">
                ⚠ {{ statusHintText }}
              </span>
            </div>
            <div class="modal-actions">
              <button type="button" class="btn-secondary" @click="fecharModal">Cancelar</button>
              <button type="submit" class="btn-primary" :disabled="salvando">
                {{ salvando ? 'Salvando...' : 'Salvar' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Confirmação de mudança de status -->
    <ConfirmarAcao
      :visible="confirmStatus"
      title="Alterar status do escritório"
      :message="confirmStatusMsg"
      confirm-label="Confirmar alteração"
      @confirm="executarSalvar"
      @cancel="confirmStatus = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import ConfirmarAcao from '@/components/comum/ConfirmarAcao.vue'
import {
  listarEscritorios,
  obterEscritorio,
  criarEscritorio,
  atualizarEscritorio,
  listarPlanos,
} from '@/api/endpoints/admin'
import type { EscritorioDto, PlanoDto, StatusEscritorio } from '@/api/types'
import { useInputMask } from '@/composables/useInputMask'
import { STATUS_ESCRITORIO } from '@/constants/statusEscritorio'

const { cnpjMask } = useInputMask()

const cnpj = computed({
  get: () => form.cnpjMascarado,
  set: (v: string) => (form.cnpjMascarado = cnpjMask(v)),
})

const loading = ref(true)
const escritorios = ref<EscritorioDto[]>([])
const planos = ref<PlanoDto[]>([])

// Modal
const modalAberto = ref(false)
const editando = ref(false)
const escritorioEdit = ref<EscritorioDto | null>(null)
const salvando = ref(false)
const form = reactive({ nome: '', cnpjMascarado: '', planoId: null as string | null, status: 'Ativo' as StatusEscritorio })

// Confirmation for status changes
const confirmStatus = ref(false)
const confirmStatusMsg = ref('')

const statusAlterado = computed(() => editando.value && form.status !== escritorioEdit.value?.status)
const statusHintClass = computed(() => form.status === 'Inadimplente' || form.status === 'Suspenso' ? 'hint-crit' : '')
const statusHintText = computed(() => {
  switch (form.status) {
    case 'Inadimplente': return 'O agente será bloqueado no próximo handshake.'
    case 'Suspenso': return 'O agente será bloqueado no próximo handshake.'
    case 'Cancelado': return 'Acesso permanentemente encerrado.'
    default: return ''
  }
})

function statusClass(s: string): string {
  return STATUS_ESCRITORIO[s as StatusEscritorio]?.cssClass ?? ''
}

function statusLabel(s: string): string {
  return STATUS_ESCRITORIO[s as StatusEscritorio]?.label ?? s
}

async function carregar() {
  loading.value = true
  try {
    const [esc, pl] = await Promise.all([listarEscritorios(), listarPlanos()])
    escritorios.value = esc
    planos.value = pl
  } catch { /* interceptor */ } finally {
    loading.value = false
  }
}

function abrirCriar() {
  editando.value = false
  escritorioEdit.value = null
  form.nome = ''
  form.cnpjMascarado = ''
  form.planoId = null
  form.status = 'Ativo'
  modalAberto.value = true
}

async function abrirEditar(e: EscritorioDto) {
  editando.value = true
  escritorioEdit.value = e
  try {
    const det = await obterEscritorio(e.id)
    form.nome = det.nome
    form.cnpjMascarado = det.cnpjMascarado
    form.planoId = det.planoId
    form.status = det.status
  } catch {
    // Fallback para os dados da listagem caso o detalhe falhe
    form.nome = e.nome
    form.cnpjMascarado = e.cnpjMascarado
    form.planoId = e.planoId
    form.status = e.status
  }
  modalAberto.value = true
}

function fecharModal() { modalAberto.value = false }

async function salvar() {
  // If status changed, require confirmation
  if (statusAlterado.value) {
    confirmStatusMsg.value = `Alterar status de ${escritorioEdit.value?.nome} de "${statusLabel(escritorioEdit.value?.status ?? 'Ativo')}" para "${statusLabel(form.status)}"?`
    confirmStatus.value = true
    return
  }
  await executarSalvar()
}

async function executarSalvar() {
  confirmStatus.value = false
  salvando.value = true
  try {
    if (editando.value && escritorioEdit.value) {
      await atualizarEscritorio(escritorioEdit.value.id, {
        nome: form.nome || undefined,
        cnpjMascarado: form.cnpjMascarado || undefined,
        planoId: form.planoId ?? undefined,
        status: form.status,
      })
    } else {
      await criarEscritorio({
        nome: form.nome,
        cnpjMascarado: form.cnpjMascarado || undefined,
        planoId: form.planoId ?? undefined,
        status: form.status,
      })
    }
    fecharModal()
    carregar()
  } catch { /* interceptor */ } finally {
    salvando.value = false
  }
}

onMounted(carregar)
</script>

<style scoped>
.admin-view { max-width: 1100px; }

.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.view-header h1 { margin: 0; }

.btn-primary {
  height: 38px; padding: 0 18px;
  background: var(--accent-gradient);
  color: var(--accent-gradient-texto); border: none; border-radius: var(--radius-md);
  font-size: 13px; font-weight: 600; font-family: var(--font-family);
  cursor: pointer; white-space: nowrap;
  display: inline-flex; align-items: center; gap: 6px;
  box-shadow: 0 2px 8px rgba(var(--accent-rgb), 0.25);
  transition: all 150ms ease;
}
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(var(--accent-rgb), 0.35); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.table-card {
  background: var(--surface-card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-xs);
}
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th {
  text-align: left; font-weight: 600; font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--text-muted); padding: 10px 14px;
  background: var(--surface-page); border-bottom: 1px solid var(--border);
}
.data-table td {
  padding: 10px 14px; border-bottom: 1px solid var(--border);
  color: var(--text-primary); vertical-align: middle;
}
.data-table tbody tr { transition: background-color 120ms; }
.data-table tbody tr:hover { background: var(--surface-page); }
.data-table tbody tr:last-child td { border-bottom: none; }
.col-nome { font-weight: 500; }
.col-cnpj { font-size: 13px; }
.col-actions { text-align: right; }

.status-chip { display: inline-block; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 12px; letter-spacing: 0.02em; }
.status-ok { background: var(--sucesso-suave); color: var(--sucesso); }
.status-warn { background: var(--atencao-suave); color: var(--atencao); }
.status-err { background: var(--erro-suave); color: var(--erro); }

.btn-edit {
  background: none; border: 1px solid var(--border); cursor: pointer;
  padding: 6px 8px; border-radius: 6px; color: var(--text-muted);
  display: inline-flex; align-items: center; transition: all 120ms;
}
.btn-edit:hover { color: var(--accent); border-color: var(--accent); background: var(--accent-suave); }

.loading-msg { padding: 32px; text-align: center; color: var(--text-muted); font-size: 14px; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-card {
  background: var(--surface-card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 28px;
  max-width: 500px; width: 90%; box-shadow: var(--shadow-lg);
}
.modal-title { font-size: 18px; font-weight: 700; margin: 0 0 20px; letter-spacing: -0.01em; }
.modal-form { display: flex; flex-direction: column; gap: 14px; }
.form-field { display: flex; flex-direction: column; gap: 4px; }
.form-field label { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.form-field input, .form-field select {
  height: 40px; padding: 0 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 14px; font-family: var(--font-family);
  background: var(--surface-page); color: var(--text-primary); outline: none;
  transition: border-color 150ms, box-shadow 150ms;
}
.form-field input:focus, .form-field select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-suave); }
.req { color: var(--erro); }
.field-hint { font-size: 12px; color: var(--text-muted); }
.hint-crit { color: var(--erro); font-weight: 600; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.btn-secondary {
  height: 38px; padding: 0 16px;
  background: transparent; color: var(--text-secondary);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 13px; font-family: var(--font-family); cursor: pointer;
  transition: all 120ms;
}
.btn-secondary:hover { background: var(--surface-page); }
</style>
