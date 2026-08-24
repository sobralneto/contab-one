/**
 * Verificação prévia do E2E: Postgres e API precisam estar no ar ANTES do
 * Playwright subir o vite — falha com instrução do que subir, em vez de dar
 * timeout genérico (design.md, Decisão 5).
 */
import { EXPLICACOES_PAGINA } from '../src/constants/explicacoesPagina'

const API_URL = process.env.VITE_API_URL ?? 'http://localhost:5139'

const CREDENCIAIS_SEED = [
  { email: 'admin@nfse.local', senha: 'Admin123!' },
  { email: 'escritorio@nfse.local', senha: 'Admin123!' },
  { email: 'usuario@nfse.local', senha: 'Admin123!' },
]

// Espelha PaginaFerramenta em src/api/types.ts — as páginas de rota de
// ferramenta (/f/:produto/...), cuja chave de "visto" é composta
// (`${produto}.${pagina}`), diferente das rotas transversais (chave = name).
// Clientes e Agentes NÃO entram aqui: não são páginas de ferramenta, são
// rotas transversais (`/clientes`, `/agentes`) — a chave delas é a bare
// (`clientes`, `agentes`), já coberta por chavesTransversais abaixo.
const PAGINAS_FERRAMENTA = ['visao-geral', 'execucoes', 'configuracao', 'regras']
const PRODUTOS_SEEDADOS = ['nfse', 'det']

/**
 * Marca a explicação de todas as páginas como já vista, para os três usuários
 * do seed.
 *
 * Sem isto o E2E não passa em banco novo: o modal de `ExplicacaoPagina` abre
 * na primeira visita de cada página, é teleportado para o body e intercepta
 * todo clique — o sintoma é `<div class="modal-overlay"> intercepts pointer
 * events` em qualquer teste que clique em algo. O tour é comportamento
 * legítimo do produto; quem tem que se preparar é o teste.
 *
 * As chaves transversais (usuários, admin/*) saem de EXPLICACOES_PAGINA, e
 * não de um array copiado aqui — página nova com explicação passa a ser
 * coberta sozinha. As de ferramenta são compostas (`nfse.clientes`, não só
 * `clientes`) e por isso precisam do cruzamento explícito com os produtos
 * do seed; marcar uma combinação que o produto não declara é inofensivo.
 */
async function marcarTourComoVisto(): Promise<void> {
  const chavesTransversais = Object.keys(EXPLICACOES_PAGINA).filter(
    (chave) => !PAGINAS_FERRAMENTA.includes(chave),
  )
  const chavesFerramenta = PRODUTOS_SEEDADOS.flatMap((produto) =>
    PAGINAS_FERRAMENTA.map((pagina) => `${produto}.${pagina}`),
  )
  const paginas = [...chavesTransversais, ...chavesFerramenta]

  for (const { email, senha } of CREDENCIAIS_SEED) {
    const respLogin = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: senha }),
    })
    if (!respLogin.ok) {
      throw new Error(
        `Login de ${email} falhou com ${respLogin.status} ao preparar o tour. ` +
          'O seed de desenvolvimento rodou?',
      )
    }
    const { accessToken } = (await respLogin.json()) as { accessToken: string }

    // Sequencial de propósito: o rate limiter de /auth é por IP, e disparar
    // tudo em paralelo transforma a preparação em fonte de flake.
    for (const pagina of paginas) {
      await fetch(`${API_URL}/api/tour/${pagina}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${accessToken}` },
      })
    }
  }
}

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

  // 3. Estado dos usuários. O seed é idempotente; os testes o chamam de novo
  //    por conta própria, mas aqui ele precisa ter rodado ao menos uma vez
  //    para os logins do passo seguinte existirem.
  const respSeed = await fetch(`${API_URL}/api/seed/dev`, { method: 'POST' })
  if (!respSeed.ok) {
    throw new Error(`POST ${API_URL}/api/seed/dev falhou com ${respSeed.status}.`)
  }

  await marcarTourComoVisto()
}
