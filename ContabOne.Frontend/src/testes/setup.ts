import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { cleanup } from '@testing-library/vue'
import { servidor } from './servidor'

// Testing Library limpa o DOM entre casos; jest-dom estende os matchers
// (toBeVisible, toHaveTextContent, etc.). O cleanup automático do
// @testing-library/vue só roda com globals: true — fazemos na mão.
afterEach(() => {
  cleanup()
})

// MSW: liga no início, reseta handlers entre casos, fecha no fim.
// onUnhandledRequest: 'error' faz uma requisição não mockada falhar o teste
// — pega chamadas acidentais de rede logo, em vez de dar timeout confuso.
beforeAll(() => servidor.listen({ onUnhandledRequest: 'error' }))
afterEach(() => servidor.resetHandlers())
afterAll(() => servidor.close())
