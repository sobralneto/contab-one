<template>
  <div class="admin-view">
    <div class="view-header">
      <h1>Planos</h1>
      <button class="btn-primary" @click="abrirCriar">+ Novo plano</button>
    </div>

    <div class="table-card">
      <table class="data-table" v-if="planos.length > 0">
        <thead>
          <tr>
            <th>Nome</th>
            <th class="text-right">Máx. clientes</th>
            <th class="text-right">Máx. agentes</th>
            <th>Emitidas</th>
            <th class="text-right">Preço mensal</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in planos" :key="p.id">
            <td class="col-nome">{{ p.nome }}</td>
            <td class="text-right tabular-nums">{{ p.maxClientes }}</td>
            <td class="text-right tabular-nums">{{ p.maxAgentes }}</td>
            <td>{{ p.permiteEmitidas ? 'Sim' : 'Não' }}</td>
            <td class="text-right tabular-nums">R$ {{ p.precoMensal.toFixed(2).replace('.', ',') }}</td>
            <td class="col-actions">
              <button class="btn-edit" @click="abrirEditar(p)" title="Editar">✎</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="loading" class="loading-msg">Carregando...</div>
    </div>

    <!-- Modal -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="modalAberto">
        <div class="modal-card">
          <h2 class="modal-title">{{ editando ? 'Editar plano' : 'Novo plano' }}</h2>
          <form @submit.prevent="salvar" class="modal-form">
            <div class="form-field">
              <label>Nome <span class="req">*</span></label>
              <input v-model="form.nome" required />
            </div>
            <div class="form-row">
              <div class="form-field">
                <label>Máx. clientes</label>
                <input v-model.number="form.maxClientes" type="number" min="1" />
              </div>
              <div class="form-field">
                <label>Máx. agentes</label>
                <input v-model.number="form.maxAgentes" type="number" min="1" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-field">
                <label>Preço mensal (R$)</label>
                <input
                  v-model="precoDisplay"
                  @beforeinput="bloquearNaoDigito"
                  placeholder="R$ 0,00"
                  inputmode="numeric"
                  maxlength="20"
                />
              </div>
              <div class="form-field checkbox-field">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="form.permiteEmitidas" />
                  Permite emitidas
                </label>
              </div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { listarPlanos, criarPlano, atualizarPlano } from '@/api/endpoints/admin'
import type { PlanoDto } from '@/api/types'
import { useInputMask } from '@/composables/useInputMask'

const { moedaDigitada, moedaFormatada } = useInputMask()

const loading = ref(true)
const planos = ref<PlanoDto[]>([])

const modalAberto = ref(false)
const editando = ref(false)
const planoEdit = ref<PlanoDto | null>(null)
const salvando = ref(false)
const form = reactive({ nome: '', maxClientes: 50, maxAgentes: 3, permiteEmitidas: true, precoMensal: 0 })

const precoDisplay = computed({
  get: () => moedaFormatada(form.precoMensal),
  set: (v: string) => (form.precoMensal = moedaDigitada(v)),
})

/**
 * A máscara já descarta não-dígitos, mas um caractere digitado que não muda o
 * valor (a vírgula, por exemplo) deixa o computed inalterado — e o Vue então
 * não reescreve o DOM, então o caractere fica visível no campo até a tecla
 * seguinte. Barrar na origem evita esse piscar.
 *
 * Só bloqueia digitação de caractere; apagar e colar continuam passando (o
 * texto colado é limpo pela máscara).
 */
function bloquearNaoDigito(e: InputEvent) {
  if (e.inputType === 'insertText' && e.data && /\D/.test(e.data)) e.preventDefault()
}

async function carregar() {
  loading.value = true
  try { planos.value = await listarPlanos() } catch { } finally { loading.value = false }
}

function abrirCriar() {
  editando.value = false; planoEdit.value = null
  form.nome = ''; form.maxClientes = 50; form.maxAgentes = 3; form.permiteEmitidas = true; form.precoMensal = 0
  modalAberto.value = true
}

function abrirEditar(p: PlanoDto) {
  editando.value = true; planoEdit.value = p
  form.nome = p.nome; form.maxClientes = p.maxClientes; form.maxAgentes = p.maxAgentes
  form.permiteEmitidas = p.permiteEmitidas; form.precoMensal = p.precoMensal
  modalAberto.value = true
}

function fecharModal() { modalAberto.value = false }

async function salvar() {
  salvando.value = true
  try {
    const payload = { nome: form.nome, maxClientes: form.maxClientes, maxAgentes: form.maxAgentes, permiteEmitidas: form.permiteEmitidas, precoMensal: form.precoMensal }
    if (editando.value && planoEdit.value) {
      await atualizarPlano(planoEdit.value.id, payload)
    } else {
      await criarPlano(payload)
    }
    fecharModal(); carregar()
  } catch { } finally { salvando.value = false }
}

onMounted(carregar)
</script>

<style scoped>
.admin-view { max-width: 900px; }
.col-nome { font-weight: 500; }

.form-row { display: flex; gap: 12px; }
.form-row .form-field { flex: 1; }
.checkbox-field { justify-content: flex-end; }
.checkbox-label { display: flex; align-items: center; gap: 6px; font-size: 14px; color: var(--text-primary); cursor: pointer; }
.checkbox-label input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--accent); cursor: pointer; }
</style>
