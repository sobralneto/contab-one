<template>
  <div class="execucoes-view animate-fade-in">
    <div class="view-header">
      <h1>Execuções</h1>
    </div>

    <!-- Admin: agrupado por escritório, com detalhamento expansível -->
    <div class="table-card" v-if="isAdmin">
      <table class="data-table" v-if="gruposEscritorio.length > 0">
        <thead>
          <tr>
            <th></th>
            <th>Escritório</th>
            <th class="text-right">Execuções</th>
            <th>Status</th>
            <th class="text-right">Baixadas</th>
            <th class="text-right">Falhas</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="g in gruposEscritorio" :key="g.escritorioId">
            <tr @click="toggleGrupo(g.escritorioId)" class="grupo-row" :class="{ expanded: grupoExpandido === g.escritorioId }">
              <td class="col-expand">
                <span class="expand-icon">{{ grupoExpandido === g.escritorioId ? '▾' : '▸' }}</span>
              </td>
              <td class="col-nome">{{ g.escritorioNome }}</td>
              <td class="text-right tabular-nums">{{ g.total }}</td>
              <td>
                <span class="status-chip status-ok" v-if="g.sucesso > 0">{{ g.sucesso }} ok</span>
                <span class="status-chip status-warn" v-if="g.parcial > 0">{{ g.parcial }} parcial</span>
                <span class="status-chip status-err" v-if="g.falha > 0">{{ g.falha }} falha</span>
                <span v-if="g.sucesso === 0 && g.parcial === 0 && g.falha === 0">—</span>
              </td>
              <td class="text-right tabular-nums">{{ totalBaixadas(g).toLocaleString('pt-BR') }}</td>
              <td class="text-right tabular-nums">{{ g.falha }}</td>
            </tr>
            <tr v-if="grupoExpandido === g.escritorioId" class="detail-row">
              <td colspan="6">
                <div class="detail-content">
                  <table class="inner-table" v-if="g.execucoes.length > 0">
                    <thead>
                      <tr>
                        <th></th>
                        <th>Início</th>
                        <th>Status</th>
                        <th class="text-right">Duração</th>
                        <th class="text-right">Baixadas</th>
                        <th class="text-right">Falhas</th>
                      </tr>
                    </thead>
                    <tbody>
                      <template v-for="e in g.execucoes" :key="e.id">
                        <tr @click="toggleExpand(e.id)" class="exec-row" :class="{ expanded: expandido === e.id }">
                          <td class="col-expand">
                            <span class="expand-icon">{{ expandido === e.id ? '▾' : '▸' }}</span>
                          </td>
                          <td class="col-data">{{ formatDateTime(e.iniciadoEm) }}</td>
                          <td>
                            <span class="status-chip" :class="statusClass(e.status)">
                              {{ statusLabel(e.status) }}
                            </span>
                          </td>
                          <td class="text-right tabular-nums">{{ formatDuracao(e.duracaoMs) }}</td>
                          <td class="text-right tabular-nums">{{ e.totalBaixadas.toLocaleString('pt-BR') }}</td>
                          <td class="text-right tabular-nums">
                            <span :class="e.totalFalhas > 0 ? 'text-err' : ''">{{ e.totalFalhas }}</span>
                          </td>
                        </tr>
                        <tr v-if="expandido === e.id" class="inner-detail">
                          <td colspan="6">
                            <div v-if="e.mensagemErro" class="detail-erro">
                              <strong>Erro:</strong> {{ e.mensagemErro }}
                            </div>
                            <div v-if="metricas[e.id]?.length" class="detail-metricas">
                              <h3>Métricas por cliente</h3>
                              <table class="metricas-table">
                                <thead>
                                  <tr>
                                    <th>Cliente</th>
                                    <th>Tipo</th>
                                    <th>Competência</th>
                                    <th class="text-right">Baixadas</th>
                                    <th class="text-right">Puladas</th>
                                    <th class="text-right">Falhas</th>
                                    <th class="text-right">Duração</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  <tr v-for="m in metricas[e.id]" :key="m.clienteId + m.competencia + m.tipo">
                                    <td>{{ m.clienteNome || m.clienteId }}</td>
                                    <td>{{ m.tipo }}</td>
                                    <td>{{ m.competencia }}</td>
                                    <td class="text-right tabular-nums">{{ m.qtdBaixadas }}</td>
                                    <td class="text-right tabular-nums">{{ m.qtdPuladas }}</td>
                                    <td class="text-right tabular-nums">{{ m.qtdFalhas }}</td>
                                    <td class="text-right tabular-nums">{{ formatDuracao(m.duracaoMs) }}</td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>
                            <div v-else-if="carregandoMetrica[e.id]" class="detail-loading">Carregando métricas...</div>
                          </td>
                        </tr>
                      </template>
                    </tbody>
                  </table>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
      <EstadoVazio
        v-else-if="!loading"
        title="Nenhuma execução"
        description="As execuções aparecerão aqui quando o agente rodar pela primeira vez."
      />
      <div v-if="loading" class="loading-msg">Carregando...</div>
    </div>

    <!-- Escritório/usuário: métricas agregadas por cliente -->
    <div class="table-card" v-else>
      <table class="data-table" v-if="gruposCliente.length > 0">
        <thead>
          <tr>
            <th>Cliente</th>
            <th class="text-right">Execuções</th>
            <th>Status</th>
            <th class="text-right">Baixadas</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="g in gruposCliente" :key="g.clienteId">
            <td class="col-nome">{{ g.clienteNome }}</td>
            <td class="text-right tabular-nums">{{ g.total }}</td>
            <td>
              <span class="status-chip status-ok" v-if="g.sucesso > 0">{{ g.sucesso }} ok</span>
              <span class="status-chip status-warn" v-if="g.parcial > 0">{{ g.parcial }} parcial</span>
              <span class="status-chip status-err" v-if="g.falha > 0">{{ g.falha }} falha</span>
              <span v-if="g.sucesso === 0 && g.parcial === 0 && g.falha === 0">—</span>
            </td>
            <td class="text-right tabular-nums">{{ g.totalBaixadas.toLocaleString('pt-BR') }}</td>
          </tr>
        </tbody>
      </table>
      <EstadoVazio
        v-else-if="!loading"
        title="Nenhuma execução"
        description="As execuções aparecerão aqui quando o agente rodar pela primeira vez."
      />
      <div v-if="loading" class="loading-msg">Carregando...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import EstadoVazio from '@/components/comum/EstadoVazio.vue'
import {
  listarExecucoesAgrupadas,
  detalheExecucao,
} from '@/api/endpoints/execucoes'
import type {
  ExecucaoGrupoEscritorio,
  ExecucaoGrupoCliente,
  ExecucaoMetricaDto,
  StatusExecucao,
} from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const isAdmin = auth.isPlatformAdmin
// Execuções são por ferramenta — :produto vem da rota /f/:produto/execucoes.
const produtoCodigo = useRoute().params.produto as string

const loading = ref(true)
const gruposEscritorio = ref<ExecucaoGrupoEscritorio[]>([])
const gruposCliente = ref<ExecucaoGrupoCliente[]>([])

const grupoExpandido = ref<string | null>(null)
const expandido = ref<string | null>(null)
const metricas = reactive<Record<string, ExecucaoMetricaDto[]>>({})
const carregandoMetrica = reactive<Record<string, boolean>>({})

function toggleGrupo(id: string) {
  grupoExpandido.value = grupoExpandido.value === id ? null : id
}

async function toggleExpand(id: string) {
  if (expandido.value === id) {
    expandido.value = null
    return
  }
  expandido.value = id
  if (!metricas[id]) {
    carregandoMetrica[id] = true
    try {
      const det = await detalheExecucao(id)
      metricas[id] = det.metricas
    } catch { /* interceptor handles */ } finally {
      carregandoMetrica[id] = false
    }
  }
}

function totalBaixadas(g: ExecucaoGrupoEscritorio): number {
  return g.execucoes.reduce((s, e) => s + e.totalBaixadas, 0)
}

function statusClass(s: StatusExecucao): string {
  switch (s) {
    case 'Sucesso': return 'status-ok'
    case 'Parcial': return 'status-warn'
    case 'Falha': return 'status-err'
  }
}

function statusLabel(s: StatusExecucao): string {
  switch (s) {
    case 'Sucesso': return 'Sucesso'
    case 'Parcial': return 'Parcial'
    case 'Falha': return 'Falha'
  }
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit', month: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatDuracao(ms: number | null): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  const s = Math.floor(ms / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  return `${m}min ${s % 60}s`
}

async function carregar() {
  loading.value = true
  try {
    const grupos = await listarExecucoesAgrupadas(isAdmin ? 'escritorio' : 'cliente', produtoCodigo)
    if (isAdmin) {
      gruposEscritorio.value = grupos as ExecucaoGrupoEscritorio[]
    } else {
      gruposCliente.value = grupos as ExecucaoGrupoCliente[]
    }
  } catch { /* interceptor handles */ } finally {
    loading.value = false
  }
}

onMounted(carregar)
</script>

<style scoped>
.execucoes-view { max-width: 1100px; }

.view-header { margin-bottom: 16px; }
.view-header h1 { margin: 0; }

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
.data-table tbody tr:last-child td { border-bottom: none; }

.grupo-row { cursor: pointer; transition: background-color 120ms; }
.grupo-row:hover { background: var(--surface-page); }
.grupo-row.expanded { background: var(--accent-suave); }
.grupo-row .col-nome { font-weight: 600; }

.exec-row { cursor: pointer; transition: background-color 120ms; }
.exec-row:hover { background: var(--surface-page); }
.exec-row.expanded { background: var(--accent-suave); }

.col-expand { width: 32px; }
.expand-icon { font-size: 14px; color: var(--text-muted); }
.col-data { white-space: nowrap; font-size: 12px; color: var(--text-secondary); }
.col-nome { font-weight: 500; }

.status-chip { display: inline-block; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 12px; letter-spacing: 0.02em; margin-right: 4px; }
.status-ok { background: var(--sucesso-suave); color: var(--sucesso); }
.status-warn { background: var(--atencao-suave); color: var(--atencao); }
.status-err { background: var(--erro-suave); color: var(--erro); }

.text-err { color: var(--erro); font-weight: 600; }

.loading-msg { padding: 32px; text-align: center; color: var(--text-muted); font-size: 14px; }

.detail-row td { padding: 0; border-bottom: 2px solid var(--border); }
.detail-content { padding: 16px 24px; background: var(--surface-page); }

.inner-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.inner-table th {
  text-align: left; font-weight: 500; font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--text-muted); padding: 6px 10px;
  border-bottom: 1px solid var(--border);
}
.inner-table td { padding: 8px 10px; border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-primary); }
.inner-table tbody tr:last-child td { border-bottom: none; }
.inner-detail td { padding: 0 10px 10px; }

.detail-erro {
  font-size: 13px; color: var(--erro); background: var(--erro-suave);
  padding: 10px 14px; border-radius: var(--radius-sm); margin-bottom: 12px;
}

.detail-metricas h3 { font-size: 14px; font-weight: 600; margin: 0 0 10px; color: var(--text-primary); }
.metricas-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.metricas-table th {
  text-align: left; font-weight: 500; font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--text-muted); padding: 6px 10px;
  border-bottom: 1px solid var(--border);
}
.metricas-table td { padding: 6px 10px; border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-primary); }
.metricas-table tbody tr:last-child td { border-bottom: none; }

.detail-loading { font-size: 13px; color: var(--text-muted); padding: 8px 0; }
</style>
