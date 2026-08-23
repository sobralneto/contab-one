import { defineConfig } from '@playwright/test'

/**
 * E2E contra a stack real: Postgres + API (Development) + `vite dev`.
 * O Playwright sobe o vite pelo webServer e assume Postgres e API já no ar —
 * o globalSetup falha com instrução clara se não estiverem (design.md,
 * Decisão 5): esconder esse pré-requisito dentro do runner tornaria a falha
 * mais difícil de diagnosticar do que um pré-requisito explícito.
 */
export default defineConfig({
  testDir: 'e2e',
  timeout: 60_000,
  globalSetup: './e2e/global-setup.ts',
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
  use: {
    baseURL: 'http://localhost:5173',
    locale: 'pt-BR',
  },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
  // Serial: o rate limiter de auth da API (10/min, fila 2) vira flake quando
  // os logins de vários workers disparam no mesmo instante — com 6 testes o
  // custo é mínimo e o comportamento fica determinístico.
  workers: 1,
})
