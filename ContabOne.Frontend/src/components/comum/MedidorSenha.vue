<template>
  <div class="medidor" v-if="senha.length > 0">
    <div class="barra">
      <span
        v-for="n in 4"
        :key="n"
        class="segmento"
        :class="n <= forca.pontuacao ? forca.cssClass : ''"
      ></span>
    </div>
    <div class="linha-rotulo">
      <span class="rotulo" :class="forca.cssClass">{{ forca.rotulo }}</span>
      <span class="faltando" v-if="!forca.valida">{{ faltando }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSenha } from '@/composables/useSenha'

const props = defineProps<{ senha: string }>()

const { avaliarForca } = useSenha()

const forca = computed(() => avaliarForca(props.senha))

/** Lista só o que falta — repetir os requisitos já atendidos vira ruído. */
const faltando = computed(() => {
  const r = forca.value.requisitos
  const pendentes = [
    !r.comprimento && '8 caracteres',
    !r.maiuscula && 'maiúscula',
    !r.minuscula && 'minúscula',
    !r.numero && 'número',
  ].filter(Boolean)

  return pendentes.length > 0 ? `falta: ${pendentes.join(', ')}` : ''
})
</script>

<style scoped>
.medidor { display: flex; flex-direction: column; gap: 4px; margin-top: 2px; }

.barra { display: flex; gap: 4px; }

.segmento {
  flex: 1; height: 4px; border-radius: 2px;
  background: var(--border); transition: background-color 150ms ease;
}
.segmento.forca-fraca { background: var(--erro); }
.segmento.forca-media { background: var(--atencao); }
.segmento.forca-forte { background: var(--sucesso); }

.linha-rotulo { display: flex; justify-content: space-between; gap: 8px; }

.rotulo { font-size: 12px; font-weight: 600; }
.rotulo.forca-fraca { color: var(--erro); }
.rotulo.forca-media { color: var(--atencao); }
.rotulo.forca-forte { color: var(--sucesso); }

.faltando { font-size: 12px; color: var(--text-muted); text-align: right; }
</style>
