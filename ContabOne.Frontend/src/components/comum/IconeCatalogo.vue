<template>
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    v-html="miolo"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * Mapa nome→ícone para domínio e ferramenta do catálogo. `nome` vem do
 * banco (Dominio.Icone / Produto.Icone) mas só é usado como CHAVE — o HTML
 * renderizado é sempre um dos valores fixos abaixo, nunca o dado em si, e
 * nome desconhecido cai no genérico em vez de deixar o item sem ícone.
 * Ferramenta nova entra no ar sem esperar arte dedicada.
 */
const ICONES: Record<string, string> = {
  'file-invoice': `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>`,
  mailbox: `<path d="M4 21V10a4 4 0 0 1 4-4h9a4 4 0 0 1 4 4v11"/><path d="M4 21h16"/><path d="M4 14h16"/><circle cx="16" cy="9" r="1"/>`,
  calculator: `<rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="8" y2="10"/><line x1="12" y1="10" x2="12" y2="10"/><line x1="16" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="8" y2="14"/><line x1="12" y1="14" x2="12" y2="14"/><line x1="16" y1="14" x2="16" y2="18"/><line x1="8" y1="18" x2="8" y2="18"/><line x1="12" y1="18" x2="12" y2="18"/>`,
}

const GENERICO = `<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>`

const props = defineProps<{ nome?: string | null }>()

const miolo = computed(() => (props.nome && ICONES[props.nome]) || GENERICO)
</script>
