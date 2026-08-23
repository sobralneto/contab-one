<template>
  <div class="kpi-card" :class="`kpi-card--${variant}`">
    <div class="kpi-icon" :class="`kpi-icon--${variant}`">
      <slot name="icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      </slot>
    </div>
    <div class="kpi-body">
      <div class="kpi-label">{{ label }}</div>
      <div class="kpi-value tabular-nums">{{ formattedValue }}</div>
      <div class="kpi-sub" v-if="subtext">{{ subtext }}</div>
    </div>
    <!-- Gradient background accent -->
    <div class="kpi-accent" :class="`kpi-accent--${variant}`"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    label: string
    value: number
    subtext?: string
    variant?: 'default' | 'warning' | 'critical'
  }>(),
  {
    variant: 'default',
  },
)

const formattedValue = computed(() => props.value.toLocaleString('pt-BR'))
</script>

<style scoped>
.kpi-card {
  position: relative;
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 22px 24px;
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  overflow: hidden;
  transition: all 200ms ease;
  box-shadow: var(--shadow-xs);
}

.kpi-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

/* ── Icon ── */
.kpi-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  flex-shrink: 0;
  color: var(--accent);
  background: var(--accent-suave);
}

.kpi-icon--warning {
  color: var(--atencao);
  background: var(--atencao-suave);
}

.kpi-icon--critical {
  color: var(--erro);
  background: var(--erro-suave);
}

/* ── Body ── */
.kpi-body {
  flex: 1;
  min-width: 0;
}

.kpi-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 2px;
}

.kpi-value {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.1;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.kpi-sub {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* ── Variants ── */
.kpi-card--warning .kpi-value {
  color: var(--atencao);
}

.kpi-card--critical .kpi-value {
  color: var(--erro);
}

/* ── Accent gradient bar (top) ── */
.kpi-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent-gradient);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.kpi-accent--warning {
  background: linear-gradient(135deg, #d97706, #f59e0b);
}

.kpi-accent--critical {
  background: linear-gradient(135deg, #dc2626, #ef4444);
}
</style>
