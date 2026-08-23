import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

// Configuração da suíte rápida (unitários + componentes). Exclui e2e/ de
// propósito: as specs do Playwright seriam coletadas aqui e falhariam com um
// erro que não menciona a causa (design.md, Decisão 3).
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    exclude: ['**/node_modules/**', '**/e2e/**', '**/testes-ui/**'],
    setupFiles: ['./src/testes/setup.ts'],
    passWithNoTests: true,
  },
})
