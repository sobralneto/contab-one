<template>
  <div class="dashboard animate-fade-in">
    <!-- ── Alertas (topo — é o que exige ação) ── -->
    <ListaAlertas
      :alertasAbertos="alertas"
      @resolver="onResolverAlerta"
    />

    <!-- ── KPIs ── -->
    <div class="kpi-row stagger-fade-in">
      <KpiCard label="Clientes ativos" :value="kpis?.totalClientes ?? 0">
        <template #icon>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </template>
      </KpiCard>
      <KpiCard
        label="Notas no mês"
        :value="kpis?.notasBaixadasMes ?? 0"
        :subtext="'via agente'"
      >
        <template #icon>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
        </template>
      </KpiCard>
      <KpiCard
        label="Cert. vencendo"
        :value="kpis?.certificadosVencendo30d ?? 0"
        :variant="(kpis?.certificadosVencendo30d ?? 0) > 0 ? 'warning' : 'default'"
        :subtext="'em 30 dias'"
      >
        <template #icon>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
        </template>
      </KpiCard>
      <KpiCard
        label="Última execução"
        :value="kpis?.ultimaExecucao ? 1 : 0"
        :subtext="ultimaExecucaoSubtext"
        :variant="ultimaExecucaoVariant"
      >
        <template #icon>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        </template>
      </KpiCard>
    </div>

    <!-- ── Estado vazio ── -->
    <EstadoVazio
      v-if="!loading && (kpis?.totalClientes ?? 0) === 0 && execucoes.length === 0"
      title="Nenhum dado ainda"
      description="Instale o agente e gere sua primeira chave em Agentes para começar a coletar notas."
      action-label="Ir para Agentes"
      @action="router.push('/agentes')"
    />

    <!-- ── Conteúdo ── -->
    <template v-else>
      <!-- Filtros -->
      <div class="filtros-card">
        <div class="filtro-group">
          <label>Período</label>
          <input type="month" v-model="filtroDe" class="filtro-input" />
          <span class="filtro-sep">até</span>
          <input type="month" v-model="filtroAte" class="filtro-input" />
        </div>
        <div class="filtro-group" v-if="auth.isPlatformAdmin">
          <label>Escritório</label>
          <select v-model="filtroEscritorioId" class="filtro-select">
            <option :value="null">Todos os escritórios</option>
            <option v-for="e in escritorios" :key="e.id" :value="e.id">
              {{ e.nome }}
            </option>
          </select>
        </div>
        <div class="filtro-group" v-else>
          <label>Cliente</label>
          <select v-model="filtroClienteId" class="filtro-select">
            <option :value="null">Todos os clientes</option>
            <option v-for="c in clientes" :key="c.id" :value="c.id">
              {{ c.codigo }} — {{ c.nome }}
            </option>
          </select>
        </div>
      </div>

      <!-- Gráfico mensal -->
      <GraficoMensal :series="seriesFiltradas" />

      <!-- Ranking + Execuções (side-by-side on wide screens) -->
      <div class="dashboard-grid">
        <RankingEscritorios v-if="auth.isPlatformAdmin" :escritorios="ranking" />
        <RankingClientes v-else :clientes="ranking" />
        <UltimasExecucoes :execucoes="execucoes" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import KpiCard from '@/components/dashboard/KpiCard.vue'
import GraficoMensal from '@/components/dashboard/GraficoMensal.vue'
import RankingClientes from '@/components/dashboard/RankingClientes.vue'
import RankingEscritorios from '@/components/dashboard/RankingEscritorios.vue'
import ListaAlertas from '@/components/dashboard/ListaAlertas.vue'
import UltimasExecucoes from '@/components/dashboard/UltimasExecucoes.vue'
import EstadoVazio from '@/components/comum/EstadoVazio.vue'
import { fetchKpis, fetchSeries, fetchRanking } from '@/api/endpoints/dashboard'
import { listarAlertas, resolverAlerta } from '@/api/endpoints/alertas'
import { listarExecucoes } from '@/api/endpoints/execucoes'
import { listarClientes } from '@/api/endpoints/clientes'
import { listarEscritorios } from '@/api/endpoints/admin'
import type {
  DashboardKpis,
  SerieItem,
  RankingItem,
  AlertaDto,
  ExecucaoResumo,
  ClienteDto,
  EscritorioDto,
} from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

// ── State ──
const loading = ref(true)
const kpis = ref<DashboardKpis | null>(null)
const alertas = ref<AlertaDto[]>([])
const series = ref<SerieItem[]>([])
const ranking = ref<RankingItem[]>([])
const execucoes = ref<ExecucaoResumo[]>([])
const clientes = ref<ClienteDto[]>([])
const escritorios = ref<EscritorioDto[]>([])

const filtroDe = ref('')
const filtroAte = ref('')
const filtroClienteId = ref<string | null>(null)
const filtroEscritorioId = ref<string | null>(null)

// ── Computed ──
// A API já aplica os filtros (de/ate/escritorioId/clienteId) e devolve a série
// agregada por entidade com competencia vazia — filtrar de novo aqui zeraria o
// gráfico ("" >= "2026-01" é falso).
const seriesFiltradas = computed(() => series.value)

const ultimaExecucaoSubtext = computed(() => {
  const ult = kpis.value?.ultimaExecucao
  if (!ult) return 'Nunca executou'
  const status = ult.status === 'Sucesso' ? 'Concluída' : ult.status === 'Parcial' ? 'Parcial' : 'Falha'
  const rel = dataRelativa(ult.iniciadoEm)
  return `${status} · ${rel}`
})

const ultimaExecucaoVariant = computed(() => {
  const status = kpis.value?.ultimaExecucao?.status
  if (!status) return 'default' as const
  if (status === 'Falha') return 'critical' as const
  if (status === 'Parcial') return 'warning' as const
  return 'default' as const
})

// ── Watchers ──
watch([filtroDe, filtroAte, filtroClienteId, filtroEscritorioId], () => {
  carregarSeries()
})

// ── Data fetching ──
async function carregarTudo() {
  loading.value = true
  await Promise.all([
    carregarKpis(),
    carregarAlertas(),
    carregarSeries(),
    carregarRanking(),
    carregarExecucoes(),
    carregarClientes(),
    carregarEscritorios(),
  ])
  loading.value = false
}

async function carregarKpis() {
  try { kpis.value = await fetchKpis() } catch { /* handled */ }
}

async function carregarAlertas() {
  try {
    const todos = await listarAlertas()
    alertas.value = todos.filter((a) => a.aberto)
  } catch { /* handled */ }
}

async function carregarSeries() {
  try {
    series.value = await fetchSeries({
      de: filtroDe.value || undefined,
      ate: filtroAte.value || undefined,
      // Admin filtra por escritório; demais papéis por cliente
      escritorioId: auth.isPlatformAdmin ? (filtroEscritorioId.value ?? undefined) : undefined,
      clienteId: !auth.isPlatformAdmin ? (filtroClienteId.value ?? undefined) : undefined,
    })
  } catch { /* handled */ }
}

async function carregarRanking() {
  try { ranking.value = await fetchRanking() } catch { /* handled */ }
}

async function carregarExecucoes() {
  try {
    const res = await listarExecucoes({ pagina: 1, tamanho: 10 })
    execucoes.value = res.dados
  } catch { /* handled */ }
}

async function carregarClientes() {
  try {
    const res = await listarClientes({ pagina: 1, tamanho: 200 })
    clientes.value = res.dados
  } catch { /* handled */ }
}

async function carregarEscritorios() {
  if (!auth.isPlatformAdmin) return
  try {
    escritorios.value = await listarEscritorios()
  } catch { /* handled */ }
}

async function onResolverAlerta(id: string) {
  try {
    await resolverAlerta(id)
    alertas.value = alertas.value.filter((a) => a.id !== id)
  } catch { /* handled */ }
}

function dataRelativa(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime()
  const diffMin = Math.floor(diffMs / 60_000)
  if (diffMin < 1) return 'agora'
  if (diffMin < 60) return `há ${diffMin} min`
  const diffHrs = Math.floor(diffMin / 60)
  if (diffHrs < 24) return `há ${diffHrs} h`
  const diffDays = Math.floor(diffHrs / 24)
  return `há ${diffDays} dia${diffDays > 1 ? 's' : ''}`
}

onMounted(carregarTudo)
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

/* ── KPIs row ── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

/* ── Filtros ── */
.filtros-card {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: flex-end;
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 14px 18px;
}

.filtro-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filtro-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.filtro-input,
.filtro-select {
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: var(--font-family);
  background: var(--surface-card);
  color: var(--text-primary);
  outline: none;
  transition: border-color 150ms, box-shadow 150ms;
}

.filtro-input:focus,
.filtro-select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-suave);
}

.filtro-sep {
  font-size: 13px;
  color: var(--text-muted);
}

/* ── Grid ── */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 24px;
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
