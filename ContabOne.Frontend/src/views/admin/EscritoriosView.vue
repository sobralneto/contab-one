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
              <!-- Classe própria, não `btn-edit`: são duas ações diferentes na
                   mesma célula, e compartilhar classe torna qualquer seletor
                   posicional ambíguo (o E2E seleciona o editar por `.btn-edit`). -->
              <button
                class="btn-ferramentas"
                @click="abrirFerramentas(e)"
                title="Ferramentas contratadas"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path
                    d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"
                  />
                </svg>
              </button>
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

    <!-- Modal: ferramentas contratadas -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="ferramentasModal">
        <div class="modal-card modal-largo">
          <h2 class="modal-title">Ferramentas de {{ escritorioFerramentas?.nome }}</h2>
          <p class="modal-desc">
            Desmarcar uma ferramenta bloqueia os agentes dela no próximo
            handshake e impede novas chaves. As chaves não são revogadas:
            remarcar devolve o acesso.
          </p>

          <div v-if="carregandoFerramentas" class="loading-msg">Carregando...</div>

          <ul class="ferramentas-lista" v-else>
            <li v-for="f in ferramentas" :key="f.id" class="ferramenta-item">
              <label class="ferramenta-label">
                <input type="checkbox" v-model="ferramentasSelecionadas" :value="f.id" />
                <span class="ferramenta-info">
                  <span class="ferramenta-nome">
                    {{ f.nome }}
                    <code class="codigo">{{ f.codigo }}_</code>
                    <span class="tag-inativo" v-if="!f.produtoAtivo">catálogo inativo</span>
                  </span>
                  <span class="ferramenta-desc">{{ f.descricao || '—' }}</span>
                </span>
              </label>
              <span
                class="ferramenta-agentes"
                :class="{ 'aviso-forte': f.totalAgentes > 0 && !ferramentasSelecionadas.includes(f.id) }"
              >
                {{ f.totalAgentes }} agente{{ f.totalAgentes === 1 ? '' : 's' }}
              </span>
            </li>
          </ul>

          <p class="aviso-impacto" v-if="agentesQueVaoCair > 0">
            ⚠ {{ agentesQueVaoCair }} agente{{ agentesQueVaoCair === 1 ? '' : 's' }}
            deste escritório vai parar de autenticar no próximo handshake.
          </p>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="ferramentasModal = false">
              Cancelar
            </button>
            <button
              type="button"
              class="btn-primary"
              :disabled="salvandoFerramentas"
              @click="salvarFerramentas"
            >
              {{ salvandoFerramentas ? 'Salvando...' : 'Salvar' }}
            </button>
          </div>
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
  listarProdutosDoEscritorio,
  definirProdutosDoEscritorio,
} from '@/api/endpoints/admin'
import type {
  EscritorioDto,
  PlanoDto,
  StatusEscritorio,
  EscritorioProdutoDto,
} from '@/api/types'
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

// ── Ferramentas contratadas ──
const ferramentasModal = ref(false)
const escritorioFerramentas = ref<EscritorioDto | null>(null)
const ferramentas = ref<EscritorioProdutoDto[]>([])
const ferramentasSelecionadas = ref<string[]>([])
const carregandoFerramentas = ref(false)
const salvandoFerramentas = ref(false)

// Quantos agentes ativos caem se este estado for salvo. Desmarcar uma
// ferramenta com agente em campo é a ação de maior consequência desta tela,
// então ela é mostrada antes de salvar, não depois.
const agentesQueVaoCair = computed(() =>
  ferramentas.value
    .filter((f) => f.habilitado && !ferramentasSelecionadas.value.includes(f.id))
    .reduce((total, f) => total + f.totalAgentes, 0),
)

async function abrirFerramentas(e: EscritorioDto) {
  escritorioFerramentas.value = e
  ferramentas.value = []
  ferramentasSelecionadas.value = []
  ferramentasModal.value = true
  carregandoFerramentas.value = true
  try {
    ferramentas.value = await listarProdutosDoEscritorio(e.id)
    ferramentasSelecionadas.value = ferramentas.value.filter((f) => f.habilitado).map((f) => f.id)
  } catch { /* interceptor handles */ } finally {
    carregandoFerramentas.value = false
  }
}

async function salvarFerramentas() {
  if (!escritorioFerramentas.value) return
  salvandoFerramentas.value = true
  try {
    await definirProdutosDoEscritorio(escritorioFerramentas.value.id, ferramentasSelecionadas.value)
    ferramentasModal.value = false
    carregar()
  } catch { /* interceptor handles */ } finally {
    salvandoFerramentas.value = false
  }
}

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

.col-nome { font-weight: 500; }
.col-cnpj { font-size: 13px; }

.btn-ferramentas { background: none; border: 1px solid var(--border); cursor: pointer; font-size: 14px; padding: 6px 8px; border-radius: 6px; line-height: 1; display: inline-flex; align-items: center; transition: all 120ms; }
.btn-ferramentas:hover { border-color: var(--accent); background: var(--accent-suave); }

.modal-largo { max-width: 640px; }
.modal-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin: 0 0 16px; }
.ferramentas-lista { list-style: none; margin: 0 0 16px; padding: 0; display: flex; flex-direction: column; gap: 2px; max-height: 46vh; overflow-y: auto; }
.ferramenta-item { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 12px; border-radius: var(--radius-sm); }
.ferramenta-item:hover { background: var(--surface-page); }
.ferramenta-label { display: flex; align-items: flex-start; gap: 10px; cursor: pointer; flex: 1; }
.ferramenta-label input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--accent); cursor: pointer; margin-top: 2px; flex-shrink: 0; }
.ferramenta-info { display: flex; flex-direction: column; gap: 2px; }
.ferramenta-nome { font-size: 14px; font-weight: 500; color: var(--text-primary); display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.ferramenta-desc { font-size: 12px; color: var(--text-muted); }
.ferramenta-agentes { font-size: 12px; color: var(--text-muted); white-space: nowrap; }
.aviso-forte { color: var(--erro); font-weight: 600; }
.tag-inativo { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted); background: var(--surface-page); border: 1px solid var(--border); padding: 1px 6px; border-radius: 10px; }
.codigo { font-family: var(--font-mono); font-size: 11px; color: var(--accent); background: var(--accent-suave); padding: 2px 6px; border-radius: 4px; }
.aviso-impacto { font-size: 13px; color: var(--erro); background: var(--erro-suave); border: 1px solid var(--erro); border-radius: var(--radius-sm); padding: 10px 12px; margin: 0 0 16px; line-height: 1.5; }
.loading-msg { padding: 24px; text-align: center; color: var(--text-muted); font-size: 14px; }

.field-hint { font-size: 12px; color: var(--text-muted); }
.hint-crit { color: var(--erro); font-weight: 600; }
</style>
