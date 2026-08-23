<template>
  <div class="init-layout" role="status" aria-label="Carregando">
    <span class="init-spinner" aria-hidden="true"></span>
  </div>
</template>

<script setup lang="ts">
// Estado neutro exibido durante a verificação inicial de sessão:
// apenas um spinner, sem sidebar, topbar, logotipo ou navegação —
// nada que revele a área autenticada do sistema.
</script>

<style scoped>
.init-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-page);
}

.init-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: init-spin 0.7s linear infinite;
}

@keyframes init-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
