<template>
  <div class="certs-card" v-if="certificados.length > 0">
    <div class="certs-header">
      <div class="certs-title-row">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        <h2 class="certs-title">Certificados</h2>
      </div>
      <span class="certs-count">{{ certificados.length }} cliente{{ certificados.length > 1 ? 's' : '' }}</span>
    </div>
    <div class="certs-list">
      <router-link
        v-for="c in certificados"
        :key="c.clienteId"
        to="/clientes"
        class="cert-item"
        :class="severityClass(c.certificadoValidade)"
      >
        <div class="cert-item-bar"></div>
        <span class="cert-item-nome">{{ c.codigo }} — {{ c.nome }}</span>
        <span class="cert-chip" :class="certClass(c.certificadoValidade)">
          {{ certLabel(c.certificadoValidade) }}
        </span>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CertificadoVencimentoItem } from '@/api/types'

defineProps<{
  certificados: CertificadoVencimentoItem[]
}>()

function diasRestantes(validade: string): number {
  const d = new Date(validade)
  const hoje = new Date()
  return Math.ceil((d.getTime() - hoje.getTime()) / 86_400_000)
}

// O endpoint só devolve clientes com validade <= hoje+30, então o resultado
// é sempre "vencido" ou "vencendo" (nunca "ok").
function certClass(validade: string): string {
  return diasRestantes(validade) < 0 ? 'cert-vencido' : 'cert-vencendo'
}

function severityClass(validade: string): string {
  return diasRestantes(validade) < 0 ? 'sev-vencido' : 'sev-vencendo'
}

function certLabel(validade: string): string {
  const dias = diasRestantes(validade)
  const fmt = new Date(validade).toLocaleDateString('pt-BR')
  if (dias < 0) return `Vencido (${fmt})`
  if (dias === 0) return 'Vence hoje'
  return `Vence em ${dias} dias`
}
</script>

<style scoped>
.certs-card {
  max-width: 420px;
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px 16px;
  box-shadow: var(--shadow-xs);
}

.certs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.certs-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
}

.certs-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.certs-count {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  background: var(--surface-page);
  padding: 3px 10px;
  border-radius: 12px;
}

.certs-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cert-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  background: var(--surface-page);
  position: relative;
  overflow: hidden;
  text-decoration: none;
  transition: background-color 150ms;
}

.cert-item:hover {
  background: var(--border);
}

.cert-item-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
}
.sev-vencido .cert-item-bar { background: var(--erro); }
.sev-vencendo .cert-item-bar { background: var(--atencao); }

.cert-item-nome {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
  font-weight: 500;
}

.cert-chip {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
  white-space: nowrap;
  letter-spacing: 0.02em;
  flex-shrink: 0;
}
.cert-vencendo { background: var(--atencao-suave); color: var(--atencao); }
.cert-vencido { background: var(--erro-suave); color: var(--erro); }
</style>
