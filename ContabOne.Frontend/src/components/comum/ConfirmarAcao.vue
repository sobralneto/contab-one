<template>
  <Teleport to="body">
    <div class="modal-overlay" v-if="visible" @click.self="$emit('cancel')">
      <div class="modal-card animate-fade-in">
        <div class="modal-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <h3 class="modal-title">{{ title }}</h3>
        <p class="modal-message">{{ message }}</p>
        <div class="modal-actions">
          <button class="btn-secondary" @click="$emit('cancel')">Cancelar</button>
          <button
            class="btn-danger"
            :disabled="!!(confirmText && confirmInput !== confirmText)"
            @click="$emit('confirm')"
          >
            {{ confirmLabel }}
          </button>
        </div>
        <div class="modal-confirm-input" v-if="confirmText">
          <label>Digite <strong>{{ confirmText }}</strong> para confirmar:</label>
          <input v-model="confirmInput" type="text" :placeholder="confirmText" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  visible: boolean
  title: string
  message: string
  confirmLabel?: string
  confirmText?: string
}>()

defineEmits<{
  confirm: []
  cancel: []
}>()

const confirmInput = ref('')
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.modal-card {
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 28px;
  max-width: 440px;
  width: 90%;
  box-shadow: var(--shadow-lg);
  text-align: center;
}

.modal-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--atencao-suave);
  color: var(--atencao);
  margin: 0 auto 16px;
}

.modal-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.modal-message {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 1.5rem;
  line-height: 1.6;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.btn-secondary {
  height: 38px;
  padding: 0 18px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-family);
  cursor: pointer;
  transition: all 120ms;
}

.btn-secondary:hover {
  background: var(--surface-page);
}

.btn-danger {
  height: 38px;
  padding: 0 18px;
  background: var(--erro);
  color: #ffffff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font-family);
  cursor: pointer;
  transition: all 120ms;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2);
}

.btn-danger:hover:not(:disabled) {
  filter: brightness(1.1);
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-confirm-input {
  margin-top: 14px;
}

.modal-confirm-input label {
  font-size: 12px;
  color: var(--text-muted);
  display: block;
  margin-bottom: 6px;
}

.modal-confirm-input input {
  width: 100%;
  height: 38px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-family: var(--font-family);
  background: var(--surface-page);
  color: var(--text-primary);
  outline: none;
}

.modal-confirm-input input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-suave);
}
</style>
