<template>
  <div class="admin-view">
    <div class="view-header">
      <h1>Regras de Coleta</h1>
    </div>

    <!-- Warning -->
    <div class="regras-aviso">
      ⚠️ <strong>Tela de alto risco.</strong> As regras publicadas aqui são distribuídas
      para <strong>todos os agentes de todos os escritórios</strong> no próximo handshake.
      Uma regra com erro de sintaxe pode interromper a coleta.
    </div>

    <!-- New rule editor -->
    <div class="editor-card" ref="editorCard">
      <h2>Nova versão</h2>
      <div class="editor-header">
        <span class="editor-version">Versão {{ proximaVersao }}</span>
      </div>
      <textarea
        v-model="novoJson"
        class="json-editor"
        rows="16"
        placeholder='{ "portal": { "urlLogin": "...", ... }, "parsing": { ... } }'
        spellcheck="false"
      ></textarea>
      <div class="editor-actions">
        <span class="json-status" :class="jsonValido ? 'json-ok' : 'json-err'">
          {{ jsonStatus }}
        </span>
        <button class="btn-primary" :disabled="!jsonValido || publicando" @click="confirmarPublicar">
          {{ publicando ? 'Publicando...' : 'Publicar versão ' + proximaVersao }}
        </button>
      </div>
    </div>

    <!-- Version history -->
    <div class="table-card" style="margin-top: 24px;">
      <h2 style="padding: 16px 16px 0; margin: 0;">Histórico de versões</h2>
      <table class="data-table" v-if="regras.length > 0">
        <thead>
          <tr>
            <th>Versão</th>
            <th>Publicada em</th>
            <th>Status</th>
            <th class="text-right">Tamanho</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="r in regras" :key="r.id">
            <tr
              :class="{ 'row-ativa': r.ativa, 'row-expandida': expandedId === r.id }"
              class="regra-row"
              :title="expandedId === r.id ? 'Clique para recolher' : 'Clique para visualizar o conteúdo'"
              @click="toggleExpand(r)"
            >
              <td class="col-versao">
                <span class="chevron" :class="{ 'chevron-open': expandedId === r.id }">▸</span>
                v{{ r.versao }}
              </td>
              <td>{{ formatDateTime(r.publicadaEm) }}</td>
              <td>
                <span class="status-chip" :class="r.ativa ? 'status-ok' : 'status-err'">
                  {{ r.ativa ? 'Ativa' : 'Inativa' }}
                </span>
              </td>
              <td class="text-right tabular-nums">{{ (r.tamanhoConteudo / 1024).toFixed(1) }} KB</td>
            </tr>
            <tr v-if="expandedId === r.id" class="row-detalhe">
              <td colspan="4">
                <div v-if="expandedLoading" class="loading-msg">Carregando conteúdo...</div>
                <div v-else-if="expandedError" class="loading-msg">
                  Não foi possível carregar o conteúdo desta versão.
                </div>
                <template v-else-if="expandedContent !== null">
                  <pre class="json-pre">{{ jsonFormatado }}</pre>
                  <div class="detalhe-actions">
                    <button class="btn-secundario" @click="copiarJson">Copiar JSON</button>
                    <button class="btn-secundario" @click="carregarNoEditor">Carregar no editor</button>
                    <button class="btn-secundario" @click="recolher">Fechar</button>
                    <span v-if="copiado" class="copiado-msg">Copiado!</span>
                  </div>
                </template>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
      <div v-if="loading" class="loading-msg">Carregando...</div>
    </div>

    <!-- Confirmar publicação -->
    <ConfirmarAcao
      :visible="confirmModal"
      title="Publicar regras de coleta"
      :message="`Publicar versão ${proximaVersao}? Esta regra será enviada para TODOS os agentes no próximo handshake.`"
      confirm-label="Publicar"
      @confirm="executarPublicar"
      @cancel="confirmModal = false"
    />

    <!-- Confirmar sobrescrita do editor ao carregar versão existente -->
    <ConfirmarAcao
      :visible="confirmCarregar"
      title="Carregar versão no editor"
      message="O editor já contém um JSON não publicado. Carregar esta versão vai substituir o conteúdo atual do editor."
      confirm-label="Substituir"
      @confirm="confirmCarregar = false; aplicarAoEditor()"
      @cancel="confirmCarregar = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import ConfirmarAcao from '@/components/comum/ConfirmarAcao.vue'
import { listarRegras, obterRegra, obterRegraAtiva, publicarRegra } from '@/api/endpoints/admin'
import { validarBundle } from '@/utils/validarBundle'
import type { RegraDto } from '@/api/types'

const loading = ref(true)
const regras = ref<RegraDto[]>([])
const novoJson = ref('')
const publicando = ref(false)
const confirmModal = ref(false)
const erroServidor = ref('')

// ── Expansão de versão no histórico ──
const expandedId = ref<string | null>(null)
const expandedContent = ref<string | null>(null)
const expandedLoading = ref(false)
const expandedError = ref(false)
const copiado = ref(false)
const confirmCarregar = ref(false)
const editorCard = ref<HTMLElement | null>(null)

const proximaVersao = computed(() => {
  if (regras.value.length === 0) return 1
  return Math.max(...regras.value.map((r) => r.versao)) + 1
})

// Editar o conteúdo zera o erro do servidor (vale para a tentativa anterior)
watch(novoJson, () => { erroServidor.value = '' })

const errosSchema = computed(() => {
  if (!novoJson.value.trim()) return ['Preencha o JSON']
  try {
    JSON.parse(novoJson.value)
  } catch (e) {
    return [`JSON inválido: ${(e as Error).message.split('\n')[0].slice(0, 60)}`]
  }
  return validarBundle(novoJson.value)
})

const jsonValido = computed(() => errosSchema.value.length === 0)

const jsonStatus = computed(() => {
  if (erroServidor.value) return erroServidor.value
  if (errosSchema.value.length === 0) return 'JSON válido'
  return errosSchema.value.slice(0, 3).join('; ')
})

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

async function carregar() {
  loading.value = true
  try {
    regras.value = await listarRegras()
    // Editor pré-preenchido com a versão ativa (formato legível) — o admin
    // ajusta o que precisa em vez de reescrever o bundle do zero.
    if (!novoJson.value.trim()) {
      try {
        const ativa = await obterRegraAtiva()
        if (ativa) {
          novoJson.value = JSON.stringify(JSON.parse(ativa.conteudo), null, 2)
        }
      } catch {
        // Sem regra ativa (ou falha ao ler) — editor fica vazio, sem quebrar a tela
      }
    }
  } catch { } finally { loading.value = false }
}

// ── Expansão de versão no histórico ──

async function toggleExpand(r: RegraDto) {
  if (expandedId.value === r.id) {
    recolher()
    return
  }
  expandedId.value = r.id
  expandedContent.value = null
  expandedError.value = false
  expandedLoading.value = true
  try {
    const detalhe = await obterRegra(r.id)
    expandedContent.value = detalhe.conteudo
  } catch {
    expandedError.value = true
  } finally {
    expandedLoading.value = false
  }
}

function recolher() {
  expandedId.value = null
  expandedContent.value = null
  expandedError.value = false
}

const jsonFormatado = computed(() => {
  if (expandedContent.value === null) return ''
  try {
    return JSON.stringify(JSON.parse(expandedContent.value), null, 2)
  } catch {
    return expandedContent.value
  }
})

async function copiarJson() {
  if (expandedContent.value === null) return
  try {
    await navigator.clipboard.writeText(expandedContent.value)
    copiado.value = true
    setTimeout(() => { copiado.value = false }, 2000)
  } catch { }
}

function carregarNoEditor() {
  if (expandedContent.value === null) return
  if (novoJson.value.trim()) {
    confirmCarregar.value = true
    return
  }
  aplicarAoEditor()
}

function aplicarAoEditor() {
  novoJson.value = expandedContent.value ?? ''
  editorCard.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function confirmarPublicar() {
  if (!jsonValido.value) return
  confirmModal.value = true
}

async function executarPublicar() {
  confirmModal.value = false
  publicando.value = true
  erroServidor.value = ''
  try {
    await publicarRegra({ conteudo: novoJson.value })
    novoJson.value = ''
    carregar()
  } catch (e: unknown) {
    // O servidor pode rejeitar um bundle que o validador do cliente aceitou
    // (os dois evoluem por conta própria) — mostra a lista de campos que ele
    // devolveu no ValidationProblem em vez de engolir o erro.
    const data = (e as { response?: { data?: { errors?: Record<string, string[]> } } })?.response?.data
    const campos = data?.errors?.conteudo
    if (campos && campos.length > 0) {
      erroServidor.value = campos.slice(0, 3).join('; ')
    } else {
      erroServidor.value = 'Não foi possível publicar. Tente novamente.'
    }
  } finally { publicando.value = false }
}

onMounted(carregar)
</script>

<style scoped>
.admin-view { max-width: 900px; }

.view-header { margin-bottom: 16px; }
.view-header h1 { margin: 0; }

.regras-aviso {
  font-size: 13px; color: var(--erro); background: var(--erro-suave);
  border: 1px solid var(--erro); border-radius: var(--radius-sm);
  padding: 12px 14px; margin-bottom: 20px; line-height: 1.6;
  /* Sem display:flex — não há ícone para alinhar e o texto com <strong>
     virava itens flex anônimos, quebrando o parágrafo em "colunas". */
}

.editor-card {
  background: var(--surface-card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 22px 20px; box-shadow: var(--shadow-xs);
}
.editor-card h2 { font-size: 15px; font-weight: 600; margin: 0 0 12px; }

.editor-header { margin-bottom: 8px; }
.editor-version { font-size: 12px; font-weight: 600; color: var(--accent); background: var(--accent-suave); padding: 3px 10px; border-radius: 12px; }

.json-editor {
  width: 100%; padding: 14px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 13px; font-family: var(--font-mono); line-height: 1.6;
  background: var(--surface-page); color: var(--text-primary);
  resize: vertical; outline: none; tab-size: 2;
  transition: border-color 150ms, box-shadow 150ms;
}
.json-editor:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-suave); }

.editor-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; }

.json-status { font-size: 13px; font-weight: 500; }
.json-ok { color: var(--sucesso); }
.json-err { color: var(--erro); }

.btn-primary {
  height: 38px; padding: 0 22px;
  background: var(--accent-gradient); color: var(--accent-gradient-texto); border: none;
  border-radius: var(--radius-sm); font-size: 13px; font-weight: 600;
  font-family: var(--font-family); cursor: pointer;
  box-shadow: 0 2px 8px rgba(var(--accent-rgb), 0.25);
  transition: all 150ms ease;
}
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(var(--accent-rgb), 0.35); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.table-card { background: var(--surface-card); border: 1px solid var(--border); border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-xs); margin-top: 24px; }
.table-card h2 { padding: 18px 18px 0; margin: 0; font-size: 15px; font-weight: 600; }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { text-align: left; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted); padding: 10px 14px; background: var(--surface-page); border-bottom: 1px solid var(--border); }
.data-table td { padding: 10px 14px; border-bottom: 1px solid var(--border); color: var(--text-primary); }
.data-table tbody tr { transition: background-color 120ms; }
.data-table tbody tr:hover { background: var(--surface-page); }
.data-table tbody tr:last-child td { border-bottom: none; }
.regra-row { cursor: pointer; }
.row-expandida { background: var(--accent-suave); }
.row-expandida:hover { background: var(--accent-suave); }
.chevron {
  display: inline-block; width: 14px; font-size: 11px; color: var(--text-muted);
  transition: transform 150ms ease; transform: rotate(0deg);
}
.chevron-open { transform: rotate(90deg); }
.col-versao { font-weight: 600; font-variant-numeric: tabular-nums; color: var(--accent); }
.row-ativa { background: var(--accent-suave); }

/* conteúdo expandido */
.row-detalhe td { background: var(--surface-page); padding: 14px 16px; }
.json-pre {
  margin: 0; padding: 12px 14px; background: var(--surface-card);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-family: var(--font-mono); font-size: 12px; line-height: 1.6;
  color: var(--text-primary); max-height: 320px; overflow: auto;
  white-space: pre-wrap; overflow-wrap: anywhere; tab-size: 2;
}
.detalhe-actions { display: flex; align-items: center; gap: 10px; margin-top: 10px; flex-wrap: wrap; }
.btn-secundario {
  height: 34px; padding: 0 16px; background: transparent;
  color: var(--text-secondary); border: 1px solid var(--border);
  border-radius: var(--radius-sm); font-size: 13px; font-weight: 500;
  font-family: var(--font-family); cursor: pointer; transition: all 120ms;
}
.btn-secundario:hover { background: var(--surface-page); color: var(--text-primary); }
.copiado-msg { font-size: 12px; font-weight: 600; color: var(--sucesso); }

.status-chip { display: inline-block; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 12px; letter-spacing: 0.02em; }
.status-ok { background: var(--sucesso-suave); color: var(--sucesso); }
.status-err { background: var(--surface-page); color: var(--text-muted); }

.loading-msg { padding: 32px; text-align: center; color: var(--text-muted); font-size: 14px; }
</style>
