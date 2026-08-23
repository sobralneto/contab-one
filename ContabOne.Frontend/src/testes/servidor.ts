import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

/**
 * Servidor de mock (MSW) compartilhado pelos testes de componente e do
 * apiClient. Intercepta no nível de rede: a requisição percorre os
 * interceptors de verdade (token, refresh, fila) e só o transporte é
 * substituído — um teste que quebre a fila de refresh falha (design.md,
 * Decisão 1).
 *
 * Handlers base; cada teste pode adicionar os próprios com
 * servidor.use(...) e restaurar com resetHandlers().
 */
export const handlers = [
  // O refresh do axios "cru" não passa pelos interceptors — devolve o token
  // novo direto, como a API de verdade.
  http.post('*/api/auth/refresh', () =>
    HttpResponse.json({ accessToken: 'token-novo-de-teste' })),
]

export const servidor = setupServer(...handlers)
