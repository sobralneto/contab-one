<template>
  <component :is="layout">
    <router-view />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AuthLayout from '@/layouts/AuthLayout.vue'
import AppLayout from '@/layouts/AppLayout.vue'
import InitializingLayout from '@/layouts/InitializingLayout.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const layout = computed(() => {
  // Durante a verificação inicial de sessão, não resolver o layout pela
  // rota — exibe estado neutro para nunca revelar a área autenticada
  if (auth.isInitializing) return InitializingLayout

  const layoutName = route.meta.layout as string | undefined
  // Rota ainda não confirmada (meta vazio): manter estado neutro em vez
  // de cair no fallback AppLayout — evita flash da sidebar durante o
  // load lazy do componente da rota alvo
  if (!layoutName) return InitializingLayout

  switch (layoutName) {
    case 'auth':
      return AuthLayout
    case 'app':
    default:
      return AppLayout
  }
})
</script>
