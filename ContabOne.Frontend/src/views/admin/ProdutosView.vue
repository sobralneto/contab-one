<template>
  <div class="admin-view">
    <div class="view-header">
      <h1>Ferramentas</h1>
      <button class="btn-primary" @click="abrirCriar">+ Nova ferramenta</button>
    </div>

    <p class="view-desc">
      Cada ferramenta do hub tem um código próprio, que é o prefixo das chaves
      de API dos agentes dela (<code>codigo_a1b2c3d4_…</code>). Cadastrar aqui
      libera a emissão de chaves — o agente em si continua sendo entregue como
      programa instalado na máquina do escritório.
    </p>

    <div class="table-card">
      <table class="data-table" v-if="produtos.length > 0">
        <thead>
          <tr>
            <th>Nome</th>
            <th>Código</th>
            <th>Descrição</th>
            <th class="text-right">Agentes ativos</th>
            <th class="text-right">Ordem</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in produtos" :key="p.id" :class="{ 'linha-inativa': !p.ativo }">
            <td class="col-nome">{{ p.nome }}</td>
            <td><code class="codigo">{{ p.codigo }}_</code></td>
            <td class="col-desc">{{ p.descricao || '—' }}</td>
            <td class="text-right tabular-nums">{{ p.totalAgentes }}</td>
            <td class="text-right tabular-nums">{{ p.ordem }}</td>
            <td>
              <span class="status-chip" :class="p.ativo ? 'status-ok' : 'status-off'">
                {{ p.ativo ? 'Ativa' : 'Inativa' }}
              </span>
            </td>
            <td class="col-actions">
              <button class="btn-edit" @click="abrirEditar(p)" title="Editar">✎</button>
            </td>
          </tr>
        </tbody>
      </table>
      <EstadoVazio
        v-else-if="!loading"
        title="Nenhuma ferramenta cadastrada"
        description="Sem ferramenta cadastrada não é possível gerar chave de agente."
        action-label="Nova ferramenta"
        @action="abrirCriar"
      />
      <div v-if="loading" class="loading-msg">Carregando...</div>
    </div>

    <Teleport to="body">
      <div class="modal-overlay" v-if="modalAberto">
        <div class="modal-card">
          <h2 class="modal-title">{{ editando ? 'Editar ferramenta' : 'Nova ferramenta' }}</h2>
          <form @submit.prevent="salvar" class="modal-form">
            <div class="form-field">
              <label>Nome <span class="req">*</span></label>
              <input v-model="form.nome" required maxlength="80" />
            </div>

            <div class="form-field">
              <label>
                Código <span class="req" v-if="!editando">*</span>
              </label>
              <input
                v-model="form.codigo"
                :disabled="editando"
                required
                maxlength="20"
                placeholder="nfse"
                @input="normalizarCodigo"
              />
              <span class="form-hint" v-if="editando">
                O código não pode ser alterado: ele já está impresso nas chaves
                que os clientes têm configuradas. Para trocá-lo seria preciso
                reemitir todas as chaves desta ferramenta.
              </span>
              <span class="form-hint" v-else-if="form.codigo">
                As chaves ficarão assim:
                <code>{{ form.codigo }}_a1b2c3d4_…</code>
              </span>
              <span class="form-hint" v-else>
                2 a 20 caracteres, só letras minúsculas e números. Sem
                <code>_</code>, que separa os campos da chave.
              </span>
              <span class="form-erro" v-if="erroCodigo">{{ erroCodigo }}</span>
            </div>

            <div class="form-field">
              <label>Descrição</label>
              <input v-model="form.descricao" maxlength="200" />
            </div>

            <div class="form-row">
              <div class="form-field">
                <label>Ordem no seletor</label>
                <input v-model.number="form.ordem" type="number" min="0" />
              </div>
              <div class="form-field checkbox-field">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="form.ativo" />
                  Ativa
                </label>
                <span class="form-hint">
                  Inativa some do seletor de novas chaves. Agentes já em campo
                  continuam funcionando.
                </span>
              </div>
            </div>

            <div class="modal-actions">
              <button type="button" class="btn-secondary" @click="fecharModal">Cancelar</button>
              <button type="submit" class="btn-primary" :disabled="salvando || !podeSalvar">
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
import EstadoVazio from '@/components/comum/EstadoVazio.vue'
import { listarProdutosAdmin, criarProduto, atualizarProduto } from '@/api/endpoints/admin'
import type { ProdutoAdminDto } from '@/api/types'

const loading = ref(true)
const produtos = ref<ProdutoAdminDto[]>([])

const modalAberto = ref(false)
const editando = ref(false)
const produtoEdit = ref<ProdutoAdminDto | null>(null)
const salvando = ref(false)

const form = reactive({ codigo: '', nome: '', descricao: '', ativo: true, ordem: 0 })

// Espelha ProdutoCodigo.Valido no servidor. O servidor continua sendo a
// autoridade — isto só evita a ida ao backend para errar o óbvio.
const CODIGO_VALIDO = /^[a-z0-9]{2,20}$/

const erroCodigo = computed(() => {
  if (editando.value || !form.codigo) return ''
  if (!CODIGO_VALIDO.test(form.codigo)) {
    return 'De 2 a 20 caracteres, só letras minúsculas e números.'
  }
  if (produtos.value.some((p) => p.codigo === form.codigo)) {
    return `Já existe uma ferramenta com o código "${form.codigo}".`
  }
  return ''
})

const podeSalvar = computed(() =>
  form.nome.trim().length > 0 && (editando.value || (!!form.codigo && !erroCodigo.value)),
)

// O código é comparado byte a byte no servidor, então normalizar na digitação
// evita o erro mais provável (digitar em caixa alta) virar 400.
function normalizarCodigo() {
  form.codigo = form.codigo.toLowerCase().replace(/[^a-z0-9]/g, '')
}

async function carregar() {
  loading.value = true
  try {
    produtos.value = await listarProdutosAdmin()
  } catch { /* interceptor handles */ } finally {
    loading.value = false
  }
}

function abrirCriar() {
  editando.value = false
  produtoEdit.value = null
  form.codigo = ''
  form.nome = ''
  form.descricao = ''
  form.ativo = true
  form.ordem = produtos.value.length + 1
  modalAberto.value = true
}

function abrirEditar(p: ProdutoAdminDto) {
  editando.value = true
  produtoEdit.value = p
  form.codigo = p.codigo
  form.nome = p.nome
  form.descricao = p.descricao
  form.ativo = p.ativo
  form.ordem = p.ordem
  modalAberto.value = true
}

function fecharModal() {
  modalAberto.value = false
}

async function salvar() {
  if (!podeSalvar.value) return
  salvando.value = true
  try {
    if (editando.value && produtoEdit.value) {
      // Sem `codigo`: imutável depois de criado.
      await atualizarProduto(produtoEdit.value.id, {
        nome: form.nome,
        descricao: form.descricao,
        ativo: form.ativo,
        ordem: form.ordem,
      })
    } else {
      await criarProduto({
        codigo: form.codigo,
        nome: form.nome,
        descricao: form.descricao,
        ativo: form.ativo,
        ordem: form.ordem,
      })
    }
    fecharModal()
    carregar()
  } catch { /* interceptor handles */ } finally {
    salvando.value = false
  }
}

onMounted(carregar)
</script>

<style scoped>
.admin-view { max-width: 1000px; }
.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.view-header h1 { margin: 0; }
.view-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin: 0 0 16px; max-width: 70ch; }
.view-desc code { font-family: var(--font-mono); font-size: 12px; background: var(--surface-page); padding: 1px 5px; border-radius: 3px; }

.btn-primary {
  height: 38px; padding: 0 18px;
  background: var(--accent-gradient); color: var(--accent-gradient-texto); border: none;
  border-radius: var(--radius-md); font-size: 13px; font-weight: 600;
  font-family: var(--font-family); cursor: pointer; white-space: nowrap;
  display: inline-flex; align-items: center; gap: 6px;
  box-shadow: 0 2px 8px rgba(var(--accent-rgb), 0.25);
  transition: all 150ms ease;
}
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(var(--accent-rgb), 0.35); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.table-card { background: var(--surface-card); border: 1px solid var(--border); border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-xs); }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { text-align: left; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted); padding: 10px 14px; background: var(--surface-page); border-bottom: 1px solid var(--border); }
.data-table td { padding: 10px 14px; border-bottom: 1px solid var(--border); color: var(--text-primary); vertical-align: middle; }
.data-table tbody tr { transition: background-color 120ms; }
.data-table tbody tr:hover { background: var(--surface-page); }
.data-table tbody tr:last-child td { border-bottom: none; }
.linha-inativa { opacity: 0.55; }
.col-nome { font-weight: 500; }
.col-desc { font-size: 13px; color: var(--text-secondary); }
.col-actions { text-align: right; }
.text-right { text-align: right; }
.tabular-nums { font-variant-numeric: tabular-nums; }
.codigo { font-family: var(--font-mono); font-size: 12px; color: var(--accent); background: var(--accent-suave); padding: 3px 8px; border-radius: 4px; }

.status-chip { display: inline-block; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 12px; letter-spacing: 0.02em; }
.status-ok { background: var(--sucesso-suave); color: var(--sucesso); }
.status-off { background: var(--surface-page); color: var(--text-muted); }

.btn-edit { background: none; border: 1px solid var(--border); cursor: pointer; font-size: 14px; padding: 6px 8px; border-radius: 6px; color: var(--text-muted); display: inline-flex; align-items: center; transition: all 120ms; }
.btn-edit:hover { color: var(--accent); border-color: var(--accent); background: var(--accent-suave); }
.loading-msg { padding: 32px; text-align: center; color: var(--text-muted); font-size: 14px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { background: var(--surface-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 28px; max-width: 540px; width: 90%; box-shadow: var(--shadow-lg); }
.modal-title { font-size: 18px; font-weight: 700; margin: 0 0 20px; letter-spacing: -0.01em; }
.modal-form { display: flex; flex-direction: column; gap: 14px; }
.form-row { display: flex; gap: 12px; }
.form-row .form-field { flex: 1; }
.form-field { display: flex; flex-direction: column; gap: 4px; }
.form-field label { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.form-field input { height: 40px; padding: 0 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 14px; font-family: var(--font-family); background: var(--surface-page); color: var(--text-primary); outline: none; transition: border-color 150ms, box-shadow 150ms; }
.form-field input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-suave); }
.form-field input:disabled { opacity: 0.6; cursor: not-allowed; }
.form-hint { font-size: 12px; color: var(--text-muted); line-height: 1.5; }
.form-hint code { font-family: var(--font-mono); background: var(--surface-page); padding: 1px 5px; border-radius: 3px; }
.form-erro { font-size: 12px; color: var(--erro); }
.req { color: var(--erro); }
.checkbox-field { justify-content: flex-start; }
.checkbox-label { display: flex; align-items: center; gap: 6px; font-size: 14px; color: var(--text-primary); cursor: pointer; }
.checkbox-label input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--accent); cursor: pointer; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.btn-secondary { height: 38px; padding: 0 16px; background: transparent; color: var(--text-secondary); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 13px; font-family: var(--font-family); cursor: pointer; transition: all 120ms; }
.btn-secondary:hover { background: var(--surface-page); }
</style>
