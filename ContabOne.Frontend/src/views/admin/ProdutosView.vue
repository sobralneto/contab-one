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
            <th>Domínio</th>
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
            <td>{{ p.dominioNome }}</td>
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

            <div class="form-field">
              <label>Domínio <span class="req">*</span></label>
              <select v-model="form.dominioCodigo" required>
                <option value="" disabled>Selecione…</option>
                <option v-for="d in dominios" :key="d.codigo" :value="d.codigo">{{ d.nome }}</option>
              </select>
              <span class="form-hint">
                Departamento do escritório contábil que a ferramenta atende —
                agrupa o menu e o hub do painel.
              </span>
            </div>

            <div class="form-field">
              <label>Páginas <span class="req">*</span></label>
              <div class="paginas-checklist">
                <label v-for="pg in PAGINAS_DISPONIVEIS" :key="pg.valor" class="checkbox-label">
                  <input type="checkbox" :value="pg.valor" v-model="form.paginas" />
                  {{ pg.label }}
                </label>
              </div>
              <span class="form-hint">
                O que a ferramenta ainda não expõe fica de fora do submenu —
                marcar aqui não cria a tela, só libera o item de menu para ela.
              </span>
              <span class="form-erro" v-if="erroPaginas">{{ erroPaginas }}</span>
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

            <div class="form-row">
              <div class="form-field checkbox-field">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="form.temAgente" />
                  Tem agente
                </label>
                <span class="form-hint">
                  Desmarque para ferramenta sem binário instalado na máquina do
                  escritório (ex.: assistente de importação) — ela some do
                  seletor de nova chave, mas continua no menu e no hub.
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
import { listarProdutosAdmin, criarProduto, atualizarProduto, listarDominios } from '@/api/endpoints/admin'
import type { DominioDto, PaginaFerramenta, ProdutoAdminDto } from '@/api/types'

const loading = ref(true)
const produtos = ref<ProdutoAdminDto[]>([])
const dominios = ref<DominioDto[]>([])

const modalAberto = ref(false)
const editando = ref(false)
const produtoEdit = ref<ProdutoAdminDto | null>(null)
const salvando = ref(false)

// Espelha PaginaFerramenta.Todas no servidor.
// Clientes e Agentes ficam de fora: não são páginas de ferramenta — as duas
// telas mostram dado do escritório inteiro, fora de /f/:produto/… (design.md).
const PAGINAS_DISPONIVEIS: { valor: PaginaFerramenta; label: string }[] = [
  { valor: 'visao-geral', label: 'Visão geral' },
  { valor: 'execucoes', label: 'Execuções' },
  { valor: 'configuracao', label: 'Configuração' },
  { valor: 'regras', label: 'Regras de coleta (restrita a PlatformAdmin)' },
  { valor: 'importacao', label: 'Importação (assistente de carga de documento)' },
]

const form = reactive({
  codigo: '',
  nome: '',
  descricao: '',
  dominioCodigo: '',
  paginas: [] as PaginaFerramenta[],
  ativo: true,
  // Governa só a oferta de chave nova (mesma família de `ativo`) — a maioria
  // das ferramentas tem um agente em campo, então o default é `true`.
  temAgente: true,
  ordem: 0,
})

const tentouSalvar = ref(false)
const erroPaginas = computed(() =>
  tentouSalvar.value && form.paginas.length === 0 ? 'Selecione ao menos uma página.' : '',
)

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
  form.nome.trim().length > 0 &&
  !!form.dominioCodigo &&
  form.paginas.length > 0 &&
  (editando.value || (!!form.codigo && !erroCodigo.value)),
)

// O código é comparado byte a byte no servidor, então normalizar na digitação
// evita o erro mais provável (digitar em caixa alta) virar 400.
function normalizarCodigo() {
  form.codigo = form.codigo.toLowerCase().replace(/[^a-z0-9]/g, '')
}

async function carregar() {
  loading.value = true
  try {
    const [listaProdutos, listaDominios] = await Promise.all([
      listarProdutosAdmin(),
      dominios.value.length > 0 ? Promise.resolve(dominios.value) : listarDominios(),
    ])
    produtos.value = listaProdutos
    dominios.value = listaDominios
  } catch { /* interceptor handles */ } finally {
    loading.value = false
  }
}

function abrirCriar() {
  editando.value = false
  produtoEdit.value = null
  tentouSalvar.value = false
  form.codigo = ''
  form.nome = ''
  form.descricao = ''
  form.dominioCodigo = ''
  form.paginas = []
  form.ativo = true
  form.temAgente = true
  form.ordem = produtos.value.length + 1
  modalAberto.value = true
}

function abrirEditar(p: ProdutoAdminDto) {
  editando.value = true
  produtoEdit.value = p
  tentouSalvar.value = false
  form.codigo = p.codigo
  form.nome = p.nome
  form.descricao = p.descricao
  form.dominioCodigo = p.dominioCodigo
  form.paginas = [...p.paginas]
  form.ativo = p.ativo
  form.temAgente = p.temAgente
  form.ordem = p.ordem
  modalAberto.value = true
}

function fecharModal() {
  modalAberto.value = false
}

async function salvar() {
  tentouSalvar.value = true
  if (!podeSalvar.value) return
  salvando.value = true
  try {
    if (editando.value && produtoEdit.value) {
      // Sem `codigo`: imutável depois de criado.
      await atualizarProduto(produtoEdit.value.id, {
        nome: form.nome,
        descricao: form.descricao,
        dominioCodigo: form.dominioCodigo,
        paginas: form.paginas,
        ativo: form.ativo,
        temAgente: form.temAgente,
        ordem: form.ordem,
      })
    } else {
      await criarProduto({
        codigo: form.codigo,
        nome: form.nome,
        descricao: form.descricao,
        dominioCodigo: form.dominioCodigo,
        paginas: form.paginas,
        ativo: form.ativo,
        temAgente: form.temAgente,
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
.view-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin: 0 0 16px; max-width: 70ch; }
.view-desc code { font-family: var(--font-mono); font-size: 12px; background: var(--surface-page); padding: 1px 5px; border-radius: 3px; }

.linha-inativa { opacity: 0.55; }
.col-nome { font-weight: 500; }
.col-desc { font-size: 13px; color: var(--text-secondary); }
.tabular-nums { font-variant-numeric: tabular-nums; }
.codigo { font-family: var(--font-mono); font-size: 12px; color: var(--accent); background: var(--accent-suave); padding: 3px 8px; border-radius: 4px; }

.status-off { background: var(--surface-page); color: var(--text-muted); }

.modal-card { max-width: 540px; }
.form-row { display: flex; gap: 12px; }
.form-row .form-field { flex: 1; }
.form-field input:disabled, .form-field select:disabled { opacity: 0.6; cursor: not-allowed; }
.paginas-checklist { display: flex; flex-wrap: wrap; gap: 8px 16px; }
.paginas-checklist .checkbox-label { font-size: 13px; }
.form-hint { font-size: 12px; color: var(--text-muted); line-height: 1.5; }
.form-hint code { font-family: var(--font-mono); background: var(--surface-page); padding: 1px 5px; border-radius: 3px; }
.form-erro { font-size: 12px; color: var(--erro); }
.checkbox-field { justify-content: flex-start; }
.checkbox-label { display: flex; align-items: center; gap: 6px; font-size: 14px; color: var(--text-primary); cursor: pointer; }
.checkbox-label input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--accent); cursor: pointer; }
</style>
