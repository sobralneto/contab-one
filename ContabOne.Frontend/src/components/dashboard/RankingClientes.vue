<template>
  <div class="ranking-card">
    <div class="ranking-header">
      <h2 class="ranking-title">Ranking de clientes</h2>
    </div>

    <div v-if="clientes.length === 0" class="ranking-empty">
      Nenhum cliente com dados.
    </div>

    <div v-else class="ranking-list">
      <div
        v-for="(c, i) in sortedClientes"
        :key="c.clienteId"
        class="ranking-row"
        :title="`${c.codigo} — ${c.nome}: ${c.total.toLocaleString('pt-BR')} notas`"
      >
        <span class="ranking-pos">{{ i + 1 }}</span>
        <span class="ranking-name">{{ c.codigo }} — {{ c.nome }}</span>
        <div class="ranking-bar-wrap">
          <div class="ranking-bar" :style="{ width: barWidth(c.total) }"></div>
        </div>
        <span class="ranking-total tabular-nums">{{ c.total.toLocaleString('pt-BR') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RankingItem } from '@/api/types'

const props = defineProps<{
  clientes: RankingItem[]
}>()

const sortedClientes = computed(() =>
  [...props.clientes].sort((a, b) => b.total - a.total).slice(0, 20),
)

const maxTotal = computed(() => sortedClientes.value[0]?.total || 1)

function barWidth(total: number): string {
  return `${(total / maxTotal.value) * 100}%`
}
</script>

<style scoped>
.ranking-card {
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 18px;
  box-shadow: var(--shadow-xs);
}

.ranking-header {
  margin-bottom: 14px;
}

.ranking-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.ranking-empty {
  font-size: 13px;
  color: var(--text-muted);
  padding: 8px 0;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ranking-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  min-width: 0;
  padding: 4px 6px;
  border-radius: 6px;
  transition: background-color 120ms;
}

.ranking-row:hover {
  background: var(--surface-page);
}

.ranking-pos {
  width: 22px;
  flex: none;
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
}

.ranking-row:nth-child(1) .ranking-pos,
.ranking-row:nth-child(2) .ranking-pos,
.ranking-row:nth-child(3) .ranking-pos {
  color: var(--accent);
}

.ranking-name {
  width: 190px;
  flex: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
  font-size: 13px;
}

.ranking-bar-wrap {
  flex: 1;
  height: 20px;
  border-radius: 4px;
  background: var(--border);
  overflow: hidden;
  min-width: 60px;
}

.ranking-bar {
  height: 100%;
  background: var(--accent-gradient);
  border-radius: 4px;
  transition: width 400ms cubic-bezier(0.4, 0, 0.2, 1);
}

.ranking-total {
  width: 56px;
  flex: none;
  text-align: right;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 12px;
}
</style>
