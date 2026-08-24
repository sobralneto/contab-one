import { expect, type Page } from '@playwright/test'

const API_URL = process.env.VITE_API_URL ?? 'http://localhost:5139'

export const CREDENCIAIS = {
  admin: { email: 'admin@nfse.local', senha: 'Admin123!' },
  escritorio: { email: 'escritorio@nfse.local', senha: 'Admin123!' },
  usuario: { email: 'usuario@nfse.local', senha: 'Admin123!' },
} as const

/**
 * Prepara o estado: /api/seed/dev é idempotente e garante escritório + três
 * usuários com senhas conhecidas (design.md, Decisão 6).
 */
export async function prepararSeed(): Promise<void> {
  const resp = await fetch(`${API_URL}/api/seed/dev`, { method: 'POST' })
  expect(resp.ok, `seed/dev falhou com ${resp.status}`).toBeTruthy()
}

/** Sufixo único por execução — dois testes paralelos não colidem no índice
 * único (design.md, Decisão 6 / tarefa 7.7). */
export function sufixoUnico(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
}

/** Cria um escritório próprio via API (sem plano, sem limite) — evita bater
 * no limite de agentes de escritórios compartilhados. */
export async function criarEscritorioViaApi(nome: string): Promise<void> {
  const loginResp = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: CREDENCIAIS.admin.email, password: CREDENCIAIS.admin.senha }),
  })
  expect(loginResp.ok, `login admin falhou com ${loginResp.status}`).toBeTruthy()
  const { accessToken } = (await loginResp.json()) as { accessToken: string }

  const criarResp = await fetch(`${API_URL}/api/admin/escritorios`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ nome }),
  })
  expect(criarResp.ok, `criação do escritório falhou com ${criarResp.status}`).toBeTruthy()
}

/**
 * Login pelo formulário real (o fluxo inteiro — inclui o cookie de refresh
 * HttpOnly que o teste de reload precisa). Pousa no hub (`/`) — é para lá
 * que o login manda por padrão desde que a navegação passou a ser agrupada
 * por domínio.
 */
export async function login(page: Page, email: string, senha: string): Promise<void> {
  await page.goto('/login')
  await page.fill('#email', email)
  await page.fill('#password', senha)
  await page.click('.btn-login')
  await page.waitForURL((url) => url.pathname === '/')
}
