<template>
  <div class="execucoes-card">
    <h2 class="execucoes-title">Últimas execuções</h2>

    <div v-if="execucoes.length === 0" class="execucoes-empty">
      Nenhuma execução registrada.
    </div>

    <table v-else class="execucoes-table">
      <thead>
        <tr>
          <th>Início</th>
          <th>Status</th>
          <th class="text-right">Duração</th>
          <th class="text-right">Baixadas</th>
          <th class="text-right">Falhas</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="e in execucoes" :key="e.id">
          <td class="exec-col-data">{{ formatDateTime(e.iniciadoEm) }}</td>
          <td>
            <span class="status-chip" :class="statusClass(e.status)">
              {{ statusLabel(e.status) }}
            </span>
          </td>
          <td class="text-right tabular-nums">{{ formatDuracao(e.duracaoMs) }}</td>
          <td class="text-right tabular-nums">{{ e.totalBaixadas.toLocaleString('pt-BR') }}</td>
          <td class="text-right tabular-nums">{{ e.totalFalhas.toLocaleString('pt-BR') }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import type { ExecucaoResumo, StatusExecucao } from '@/api/types'

defineProps<{
  execucoes: ExecucaoResumo[]
}>()

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
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
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
</script>

<style scoped>
.execucoes-card {
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 18px;
  box-shadow: var(--shadow-xs);
}

.execucoes-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 14px;
}

.execucoes-empty {
  font-size: 13px;
  color: var(--text-muted);
}

.execucoes-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.execucoes-table th {
  text-align: left;
  font-weight: 500;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  padding: 8px 10px;
  background: var(--surface-page);
  border-bottom: 1px solid var(--border);
  border-radius: 6px 6px 0 0;
}

.execucoes-table td {
  padding: 9px 10px;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
}

.execucoes-table tbody tr:last-child td {
  border-bottom: none;
}

.execucoes-table tbody tr:hover {
  background: var(--surface-page);
  border-radius: 6px;
}

.exec-col-data {
  white-space: nowrap;
  color: var(--text-secondary);
  font-size: 12px;
}

.status-chip {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
  letter-spacing: 0.02em;
}

.status-ok {
  background: var(--sucesso-suave);
  color: var(--sucesso);
}

.status-warn {
  background: var(--atencao-suave);
  color: var(--atencao);
}

.status-err {
  background: var(--erro-suave);
  color: var(--erro);
}
</style>
