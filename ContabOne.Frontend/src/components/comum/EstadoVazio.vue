<template>
  <div class="empty-state">
    <div class="empty-icon">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
    </div>
    <h2 class="empty-title">{{ title }}</h2>
    <p class="empty-description">{{ description }}</p>
    <button v-if="actionLabel" class="empty-action" @click="$emit('action')">
      {{ actionLabel }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description: string
  actionLabel?: string
}>()

defineEmits<{
  action: []
}>()
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 1.5rem;
  text-align: center;
}

.empty-icon {
  color: var(--text-muted);
  opacity: 0.3;
  margin-bottom: 1.25rem;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem;
  letter-spacing: -0.01em;
}

.empty-description {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
  max-width: 380px;
  line-height: 1.6;
}

.empty-action {
  margin-top: 1.5rem;
  height: 38px;
  padding: 0 1.25rem;
  background: var(--accent-gradient);
  color: var(--accent-gradient-texto);
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font-family);
  cursor: pointer;
  transition: all 150ms ease;
  box-shadow: 0 2px 8px rgba(var(--accent-rgb), 0.25);
}

.empty-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(var(--accent-rgb), 0.35);
}
</style>
