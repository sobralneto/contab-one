<template>
  <div class="alertas-card" v-if="alertasAbertos.length > 0">
    <div class="alertas-header">
      <div class="alertas-title-row">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
        <h2 class="alertas-title">Alertas</h2>
      </div>
      <span class="alertas-count">{{ alertasAbertos.length }} aberto{{ alertasAbertos.length > 1 ? 's' : '' }}</span>
    </div>
    <div class="alertas-list">
      <div
        v-for="a in alertasAbertos"
        :key="a.id"
        class="alerta-item"
        :class="severidadeClass(a.severidade)"
      >
        <div class="alerta-severity-bar" :class="severidadeClass(a.severidade)"></div>
        <span class="alerta-icon">{{ severidadeIcone(a.severidade) }}</span>
        <div class="alerta-body">
          <span class="alerta-mensagem">{{ a.mensagem }}</span>
          <span class="alerta-meta" v-if="a.clienteNome">{{ a.clienteNome }} · {{ dataRelativa(a.criadoEm) }}</span>
          <span class="alerta-meta" v-else>{{ dataRelativa(a.criadoEm) }}</span>
        </div>
        <button
          class="alerta-resolver"
          @click="$emit('resolver', a.id)"
          title="Marcar como resolvido"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AlertaDto, SeveridadeAlerta } from '@/api/types'

defineProps<{
  alertasAbertos: AlertaDto[]
}>()

defineEmits<{
  resolver: [id: string]
}>()

function severidadeClass(s: SeveridadeAlerta): string {
  switch (s) {
    case 'Critico': return 'alerta-crit'
    case 'Atencao': return 'alerta-warn'
    default: return 'alerta-info'
  }
}

function severidadeIcone(s: SeveridadeAlerta): string {
  switch (s) {
    case 'Critico': return '⚠'
    case 'Atencao': return '⚠'
    default: return 'ℹ'
  }
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
</script>

<style scoped>
.alertas-card {
  margin-bottom: 24px;
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 16px 18px;
  box-shadow: var(--shadow-xs);
}

.alertas-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.alertas-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
}

.alertas-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.alertas-count {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  background: var(--surface-page);
  padding: 3px 10px;
  border-radius: 12px;
}

.alertas-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.alerta-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  background: var(--surface-page);
  position: relative;
  overflow: hidden;
  transition: background-color 150ms;
}

.alerta-item:hover {
  background: var(--border);
}

.alerta-severity-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
}
.alerta-crit .alerta-severity-bar { background: var(--erro); }
.alerta-warn .alerta-severity-bar { background: var(--atencao); }
.alerta-info .alerta-severity-bar { background: var(--accent); }

.alerta-icon {
  flex-shrink: 0;
  font-size: 14px;
  padding-top: 1px;
}

.alerta-crit .alerta-icon { color: var(--erro); }
.alerta-warn .alerta-icon { color: var(--atencao); }
.alerta-info .alerta-icon { color: var(--accent); }

.alerta-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.alerta-mensagem {
  color: var(--text-primary);
  line-height: 1.4;
  font-weight: 500;
}

.alerta-meta {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.alerta-resolver {
  background: none;
  border: 1px solid var(--border);
  cursor: pointer;
  color: var(--text-muted);
  padding: 4px 6px;
  flex-shrink: 0;
  border-radius: 6px;
  display: flex;
  align-items: center;
  transition: all 120ms ease;
}

.alerta-resolver:hover {
  color: var(--sucesso);
  border-color: var(--sucesso);
  background: var(--sucesso-suave);
}
</style>
