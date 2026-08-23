<template>
  <div class="chart-card">
    <div class="chart-header">
      <h2 class="chart-title">Notas por mês</h2>
      <div class="chart-legend">
        <span class="legend-item"><span class="legend-swatch rec"></span>Recebidas</span>
        <span class="legend-item"><span class="legend-swatch emi"></span>Emitidas</span>
      </div>
    </div>
    <Chart type="bar" :data="chartData" :options="chartOptions" class="chart-canvas" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Chart from 'primevue/chart'
import type { SerieItem } from '@/api/types'
import { useUiStore } from '@/stores/ui'

const props = defineProps<{
  series: SerieItem[]
}>()

const ui = useUiStore()

/**
 * O Chart.js precisa de cor concreta, então lemos o token do CSS em vez de
 * repetir o hex aqui: os quadradinhos da legenda já usam `var(--series-*)` e,
 * com um literal nas barras, legenda e barra mostrariam verdes diferentes —
 * e diferentes de novo no dark mode, onde os tokens viram.
 */
function corDoToken(nome: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(nome).trim()
}

function rotuloSerie(s: SerieItem): string {
  return s.label || formatCompetencia(s.competencia)
}

function formatCompetencia(m: string): string {
  const [ano, mes] = m.split('-')
  return `${mes}/${ano.slice(2)}`
}

const chartData = computed(() => {
  const rotulos = [...new Set(props.series.map(rotuloSerie))]
  const recebidas = rotulos.map((l) =>
    props.series
      .filter((s) => rotuloSerie(s) === l && s.tipo === 'Recebidas')
      .reduce((sum, s) => sum + s.qtd, 0),
  )
  const emitidas = rotulos.map((l) =>
    props.series
      .filter((s) => rotuloSerie(s) === l && s.tipo === 'Emitidas')
      .reduce((sum, s) => sum + s.qtd, 0),
  )

  // Depender de ui.darkMode aqui é de propósito: é o que faz o computed
  // recalcular as cores quando o tema vira.
  void ui.darkMode

  return {
    labels: rotulos,
    datasets: [
      {
        label: 'Recebidas',
        data: recebidas,
        backgroundColor: corDoToken('--series-recebidas'),
        borderRadius: 6,
        borderSkipped: false,
      },
      {
        label: 'Emitidas',
        data: emitidas,
        backgroundColor: corDoToken('--series-emitidas'),
        borderRadius: 6,
        borderSkipped: false,
      },
    ],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  stacked: true,
  interaction: {
    mode: 'index' as const,
    intersect: false,
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#ffffff',
      titleColor: '#0f172a',
      bodyColor: '#475569',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      cornerRadius: 8,
      padding: 12,
      callbacks: {
        label: (ctx: { dataset: { label: string }; raw: number }) =>
          ` ${ctx.dataset.label}: ${ctx.raw.toLocaleString('pt-BR')}`,
      },
    },
  },
  scales: {
    x: {
      stacked: true,
      grid: { display: false },
      ticks: { color: '#64748b', font: { size: 11 } },
    },
    y: {
      stacked: true,
      grid: { color: '#e2e8f0' },
      ticks: { color: '#64748b', font: { size: 11 }, callback: (v: number) => v.toLocaleString('pt-BR') },
      beginAtZero: true,
    },
  },
}))
</script>

<style scoped>
.chart-card {
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 18px 14px;
  box-shadow: var(--shadow-xs);
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.chart-legend {
  display: flex;
  gap: 18px;
  font-size: 12px;
  color: var(--text-secondary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: 500;
}

.legend-swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

.legend-swatch.rec { background: var(--series-recebidas); }
.legend-swatch.emi { background: var(--series-emitidas); }

.chart-canvas {
  height: 300px;
}
</style>
