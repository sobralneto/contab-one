/**
 * Verificação prévia do E2E: Postgres e API precisam estar no ar ANTES do
 * Playwright subir o vite — falha com instrução do que subir, em vez de dar
 * timeout genérico (design.md, Decisão 5).
 */
const API_URL = process.env.VITE_API_URL ?? 'http://localhost:5139'

export default async function globalSetup(): Promise<void> {
  // 1. API responde?
  let healthOk = false
  try {
    const resp = await fetch(`${API_URL}/health`)
    healthOk = resp.ok
  } catch {
    healthOk = false
  }
  if (!healthOk) {
    throw new Error(
      `API não respondeu em ${API_URL}/health.\n\n` +
        'Suba a stack antes de rodar o E2E:\n' +
        '  1. docker compose up -d postgres\n' +
        '  2. na pasta ContabOne.Api, com HMAC_CNPJ_KEY e JWT_SIGNING_KEY setadas:\n' +
        '       dotnet run  (Development é o perfil padrão do launchSettings — o /api/seed só existe fora de produção)\n' +
        '  3. rode: npm run test:e2e',
    )
  }

  // 2. O seed de desenvolvimento está acessível? (garante Development + banco migrado)
  let seedOk = false
  try {
    const resp = await fetch(`${API_URL}/api/seed/status`)
    seedOk = resp.status === 200
  } catch {
    seedOk = false
  }
  if (!seedOk) {
    throw new Error(
      `GET ${API_URL}/api/seed/status não respondeu 200.\n\n` +
        'Isso indica que a API não está em Development (o endpoint de seed só ' +
        'existe fora de produção) ou o banco não foi migrado. Confira o perfil ' +
        'do launchSettings e o log da API.',
    )
  }
}
