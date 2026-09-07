#!/usr/bin/env node
/**
 * Runner seletivo: roda só as suítes afetadas pelo que você mexeu.
 *
 *   node scripts/testes-afetados.mjs               # mudanças não commitadas (vs HEAD)
 *   node scripts/testes-afetados.mjs --base main   # + tudo que já foi commitado na branch
 *   node scripts/testes-afetados.mjs --listar      # só mostra o que rodaria
 *   node scripts/testes-afetados.mjs --tudo        # suíte completa dos 3 projetos
 *
 * Como cada camada é reduzida:
 *
 * - Frontend: `vitest run --changed` — o próprio Vitest resolve o grafo de
 *   módulos, então mexer em ClientesView.vue roda ClientesView.spec.ts e não a
 *   suíte inteira. Nada de mapa manual aqui.
 * - API: mapa derivado do código, não escrito à mão (ver `testesApi`). Arquivos
 *   compartilhados (Program.cs, Infra/, Domain/Entities.cs, Migrations/,
 *   tests/TestSupport/) disparam a suíte completa de propósito — é o que
 *   invalida qualquer seleção.
 * - Agente Python: mapa por `import` — um teste é afetado pelo módulo que ele
 *   importa. Fixtures e harness compartilhados disparam a suíte toda.
 *
 * Em qualquer camada, arquivo que o mapa não souber classificar cai na suíte
 * completa daquela camada: verde falso é pior do que suíte lenta.
 *
 * As suítes Playwright (e2e/ e testes-ui/) nunca entram aqui: precisam da stack
 * no ar. O script avisa quando elas parecem relevantes.
 */

import { execFileSync, spawnSync } from 'node:child_process'
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const NPM = process.platform === 'win32' ? 'npm.cmd' : 'npm'
const PY = process.env.PYTHON_AGENTE ?? (process.platform === 'win32' ? 'py' : 'python3')
const PY_ARGS = process.platform === 'win32' ? ['-3.14'] : []

// ── Argumentos ────────────────────────────────────────────────────────────
const argv = process.argv.slice(2)
const opcoes = {
  base: null,
  listar: argv.includes('--listar') || argv.includes('--dry-run'),
  tudo: argv.includes('--tudo') || argv.includes('--all'),
}
const iBase = argv.findIndex((a) => a === '--base')
if (iBase !== -1) opcoes.base = argv[iBase + 1]

// ── Git ───────────────────────────────────────────────────────────────────
//
// Atenção: isto NÃO é um repositório só. ContabOne.Api/, ContabOne.Frontend/,
// Nfse.Agent/ e Det.Agent/ são repos git independentes, ignorados pelo repo da
// raiz (.gitignore, seção 6). Consultar só o git da raiz devolveria "nada
// mudou" para todo o código — por isso perguntamos a cada repo separadamente e
// prefixamos o resultado com a pasta, para o resto do script enxergar caminhos
// como `ContabOne.Api/Features/...`.
const SUBREPOS = ['.', 'ContabOne.Api', 'ContabOne.Frontend', 'Nfse.Agent', 'Det.Agent', 'Rfb.Agent']

function git(repo, args) {
  try {
    return execFileSync('git', args, { cwd: path.join(RAIZ, repo), encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
  } catch {
    return []
  }
}

function arquivosMudados() {
  const arquivos = new Set()
  for (const repo of SUBREPOS) {
    if (!existsSync(path.join(RAIZ, repo, '.git'))) continue
    const prefixo = repo === '.' ? '' : `${repo}/`
    const doRepo = new Set()
    // Working tree (rastreados) + não rastreados: o caso do dia a dia.
    for (const f of git(repo, ['diff', '--name-only', 'HEAD'])) doRepo.add(f)
    for (const f of git(repo, ['ls-files', '--others', '--exclude-standard'])) doRepo.add(f)
    // Com --base, soma o que já foi commitado na branch (se o ref existir aqui).
    if (opcoes.base) {
      for (const f of git(repo, ['diff', '--name-only', `${opcoes.base}...HEAD`])) doRepo.add(f)
    }
    for (const f of doRepo) arquivos.add(prefixo + f.replace(/\\/g, '/'))
  }
  return [...arquivos].filter((f) => !RUIDO.some((r) => r.test(f)))
}

/**
 * Nada aqui muda o resultado de um teste — documentação, CI, artefatos de
 * build, dados locais. Sem esta lista, mexer num README derrubaria a seleção
 * no "não sei mapear" e rodaria a suíte inteira.
 */
const RUIDO = [
  /(^|\/)\.github\//,
  /(^|\/)\.vscode\//,
  /(^|\/)\.claude\//,
  /(^|\/)\.opencode\//,
  /(^|\/)openspec\//,
  /(^|\/)docs\//,
  /\.md$/i,
  /\.ya?ml$/,
  /(^|\/)Dockerfile$/,
  /(^|\/)Caddyfile$/,
  /(^|\/)railway\.json$/,
  /(^|\/)\.gitignore$/,
  /(^|\/)\.env/,
  /(^|\/)(bin|obj|dist|node_modules|__pycache__|test-results|playwright-report)\//,
  // Dados locais de produção dos agentes (nunca entram em teste).
  /(^|\/)(notas|certificados|logs|resultado|debug|perfil|config)\//,
  /\.(pfx|p12|xlsx|log|txt|toml)$/,
]

const ler = (rel) => {
  try {
    return readFileSync(path.join(RAIZ, rel), 'utf8')
  } catch {
    return ''
  }
}

const listar = (rel) => {
  try {
    return readdirSync(path.join(RAIZ, rel))
  } catch {
    return []
  }
}

// ── API (.NET) ────────────────────────────────────────────────────────────

/** Mudou algo aqui, a seleção não vale mais — roda a suíte inteira. */
const GATILHOS_AMPLOS_API = [
  /^ContabOne\.Api\/Program\.cs$/,
  /^ContabOne\.Api\/Infra\//,
  /^ContabOne\.Api\/Migrations\//,
  /^ContabOne\.Api\/Domain\/(Entities|Enums)\.cs$/,
  /^ContabOne\.Api\/appsettings/,
  /^ContabOne\.Api\/.*\.csproj$/,
  /^ContabOne\.Api\/tests\/TestSupport\//,
  /^ContabOne\.slnx$/,
]

/**
 * Ligações que não aparecem em rota nem no nome do arquivo — os contratos
 * compartilhados com o Python e os testes sem HTTP. Cada linha aqui é uma
 * dependência real documentada no AGENTS.md.
 */
const MAPA_EXTRA_API = [
  { padrao: /^ContabOne\.Api\/Security\/CnpjHasher\.cs$/, testes: ['HashersTest'] },
  { padrao: /^ContabOne\.Api\/Security\/ApiKeyHasher\.cs$/, testes: ['HashersTest', 'ProdutoApiKeyTest'] },
  {
    padrao: /^ContabOne\.Api\/Security\/ConfiguracaoCipher\.cs$/,
    testes: ['HandshakeConfiguracaoTest', 'ConfiguracaoPorFerramentaTest'],
  },
  { padrao: /^ContabOne\.Api\/Domain\/RegraColeta/, testes: ['BundleCorpusTest', 'BundleSeedTest'] },
  { padrao: /^ContabOne\.Api\/Domain\/RegraSeedV1\.cs$/, testes: ['BundleSeedTest', 'BundleCorpusTest'] },
  { padrao: /^ContabOne\.Api\/Domain\/AlertaExpressoes\.cs$/, testes: ['AlertaJobTest', 'TraducaoLinqTest'] },
  { padrao: /^ContabOne\.Api\/Domain\/ApuracaoExpressoes\.cs$/, testes: ['PgdasTest', 'TraducaoLinqTest'] },
  { padrao: /^ContabOne\.Api\/Jobs\//, testes: ['AlertaJobTest'] },
  // Vetores/corpus compartilhados C# ↔ Python: mexeu na fixture, os dois lados testam.
  { padrao: /^Nfse\.Agent\/testes\/fixtures\/cnpj_vetores\.json$/, testes: ['HashersTest'] },
  { padrao: /^Nfse\.Agent\/testes\/fixtures\/bundles\//, testes: ['BundleCorpusTest'] },
]

/** Nomes das classes de teste da API (pelo nome do arquivo). */
function classesDeTeste() {
  return listar('ContabOne.Api/tests')
    .filter((f) => f.endsWith('Test.cs'))
    .map((f) => f.replace(/\.cs$/, ''))
}

/** `MapGroup("/api/x").MapXEndpoints()` → prefixo de rota por arquivo de feature. */
function prefixosPorArquivoDeFeature() {
  const programa = ler('ContabOne.Api/Program.cs')
  const grupos = [
    ...programa.matchAll(/MapGroup\(\s*"([^"]+)"\s*\)\s*\.\s*(Map[A-Za-z0-9]+Endpoints)\s*\(/g),
  ]
  const arquivos = new Map() // caminho do arquivo → Set(prefixos)
  const featuresDir = 'ContabOne.Api/Features'
  for (const area of listar(featuresDir)) {
    for (const nome of listar(`${featuresDir}/${area}`)) {
      if (!nome.endsWith('.cs')) continue
      const rel = `${featuresDir}/${area}/${nome}`
      const fonte = ler(rel)
      const prefixos = new Set()
      for (const [, prefixo, extensao] of grupos) {
        if (new RegExp(`\\b${extensao}\\b`).test(fonte)) prefixos.add(prefixo)
      }
      if (prefixos.size) arquivos.set(rel, prefixos)
    }
  }
  return arquivos
}

/** Rotas "/api/..." citadas por cada arquivo de teste. */
function rotasPorTeste() {
  const mapa = new Map()
  for (const nome of listar('ContabOne.Api/tests')) {
    if (!nome.endsWith('Test.cs')) continue
    const fonte = ler(`ContabOne.Api/tests/${nome}`)
    mapa.set(
      nome.replace(/\.cs$/, ''),
      [...fonte.matchAll(/"(\/api\/[a-zA-Z0-9/_{}:-]*)/g)].map((m) => m[1]),
    )
  }
  return mapa
}

function testesApi(mudados) {
  const doApi = mudados.filter((f) => f.startsWith('ContabOne.Api/'))
  const fixturesCompartilhadas = mudados.filter(
    (f) => f.startsWith('Nfse.Agent/') && MAPA_EXTRA_API.some((r) => r.padrao.test(f)),
  )
  if (!doApi.length && !fixturesCompartilhadas.length) return { modo: 'nenhum', classes: [], motivos: [] }

  const amplos = doApi.filter((f) => GATILHOS_AMPLOS_API.some((r) => r.test(f)))
  if (amplos.length) return { modo: 'tudo', classes: [], motivos: [`compartilhado: ${amplos.join(', ')}`] }

  const classes = new Set()
  const motivos = []
  const conhecidas = classesDeTeste()
  const prefixos = prefixosPorArquivoDeFeature()
  const rotas = rotasPorTeste()
  const naoMapeados = []

  for (const arquivo of [...doApi, ...fixturesCompartilhadas]) {
    const antes = classes.size

    // 1. O próprio arquivo de teste mudou.
    const m = arquivo.match(/^ContabOne\.Api\/tests\/(\w+Test)\.cs$/)
    if (m) {
      classes.add(m[1])
      motivos.push(`${arquivo} → ${m[1]} (o teste mudou)`)
      continue
    }

    // 2. Mesmo nome: ValidadorArquivo.cs → ValidadorArquivoTest.
    const talo = path.basename(arquivo).replace(/\.cs$/, '').replace(/Endpoints$/, '')
    const porNome = conhecidas.filter((c) => c === `${talo}Test` || (c.startsWith(talo) && c.endsWith('Test')))
    porNome.forEach((c) => classes.add(c))
    if (porNome.length) motivos.push(`${arquivo} → ${porNome.join(', ')} (mesmo nome)`)

    // 3. Rota: testes que batem nas rotas do grupo desta feature.
    const meusPrefixos = new Set()
    const pasta = path.dirname(arquivo)
    for (const [rel, ps] of prefixos) {
      if (path.dirname(rel) === pasta) ps.forEach((p) => meusPrefixos.add(p))
    }
    if (meusPrefixos.size) {
      const porRota = []
      for (const [classe, rotasDoTeste] of rotas) {
        if (classes.has(classe)) continue
        if (rotasDoTeste.some((r) => [...meusPrefixos].some((p) => r === p || r.startsWith(`${p}/`)))) {
          classes.add(classe)
          porRota.push(classe)
        }
      }
      if (porRota.length) motivos.push(`${arquivo} (${[...meusPrefixos].join(' ')}) → ${porRota.join(', ')}`)
    }

    // 4. Ligações explícitas (contratos compartilhados, testes sem HTTP).
    for (const regra of MAPA_EXTRA_API) {
      if (!regra.padrao.test(arquivo)) continue
      regra.testes.forEach((c) => classes.add(c))
      motivos.push(`${arquivo} → ${regra.testes.join(', ')} (contrato)`)
    }

    if (classes.size === antes) naoMapeados.push(arquivo)
  }

  // Não soube mapear: melhor rodar tudo do que dar um verde falso.
  if (naoMapeados.length) {
    return { modo: 'tudo', classes: [], motivos: [...motivos, `sem mapa para: ${naoMapeados.join(', ')}`] }
  }
  return { modo: 'filtro', classes: [...classes].sort(), motivos }
}

// ── Agentes Python ────────────────────────────────────────────────────────

function testesPython(mudados, pasta) {
  const doAgente = mudados.filter(
    (f) => f.startsWith(`${pasta}/`) && !f.includes('/notas/') && !f.includes('/certificados/'),
  )
  if (!doAgente.length) return { modo: 'nenhum', arquivos: [], motivos: [] }

  const compartilhados = doAgente.filter(
    (f) =>
      /\/testes\/(_harness|_fake_api|executar_tudo)\.py$/.test(f) ||
      /\/testes\/fixtures\//.test(f) ||
      /\/requirements\.txt$/.test(f),
  )
  if (compartilhados.length) {
    return { modo: 'tudo', arquivos: [], motivos: [`compartilhado: ${compartilhados.join(', ')}`] }
  }

  const testes = listar(`${pasta}/testes`).filter((f) => /^teste_.*\.py$/.test(f))
  const importados = new Map(
    testes.map((t) => {
      const fonte = ler(`${pasta}/testes/${t}`)
      const mods = new Set()
      for (const [, m] of fonte.matchAll(/^\s*(?:import|from)\s+([A-Za-z_][\w.]*)/gm)) mods.add(m.split('.')[0])
      return [t, mods]
    }),
  )

  const escolhidos = new Set()
  const motivos = []
  const naoMapeados = []
  for (const arquivo of doAgente) {
    const antes = escolhidos.size
    const nome = path.basename(arquivo)

    if (/^teste_.*\.py$/.test(nome) && arquivo.includes('/testes/')) {
      escolhidos.add(nome)
      motivos.push(`${arquivo} → ${nome} (o teste mudou)`)
      continue
    }
    if (!nome.endsWith('.py')) continue // README, config de exemplo, ferramenta solta

    const modulo = nome.replace(/\.py$/, '')
    const porImport = testes.filter((t) => importados.get(t)?.has(modulo))
    porImport.forEach((t) => escolhidos.add(t))
    if (porImport.length) motivos.push(`${arquivo} → ${porImport.join(', ')} (importam ${modulo})`)

    // Roda o agente inteiro por subprocess: qualquer módulo o afeta.
    const subprocesso = testes.find((t) => t === 'teste_subprocess_agente.py')
    if (subprocesso && !arquivo.includes('/testes/')) {
      escolhidos.add(subprocesso)
      motivos.push(`${arquivo} → ${subprocesso} (roda o agente por subprocess)`)
    }

    if (escolhidos.size === antes) naoMapeados.push(arquivo)
  }

  if (naoMapeados.length) {
    return { modo: 'tudo', arquivos: [], motivos: [...motivos, `sem mapa para: ${naoMapeados.join(', ')}`] }
  }
  if (!escolhidos.size) return { modo: 'nenhum', arquivos: [], motivos }
  return { modo: 'filtro', arquivos: [...escolhidos].sort(), motivos }
}

// ── Frontend ──────────────────────────────────────────────────────────────

function precisaVitest(mudados) {
  return mudados.some(
    (f) =>
      f.startsWith('ContabOne.Frontend/') &&
      !f.startsWith('ContabOne.Frontend/e2e/') &&
      !f.startsWith('ContabOne.Frontend/testes-ui/') &&
      !f.startsWith('ContabOne.Frontend/dist/') &&
      !f.includes('/node_modules/'),
  )
}

function playwrightAfetado(mudados) {
  return mudados.filter(
    (f) => f.startsWith('ContabOne.Frontend/e2e/') || f.startsWith('ContabOne.Frontend/testes-ui/'),
  )
}

// ── Execução ──────────────────────────────────────────────────────────────

const planejados = []
function plano(nome, comando, args, cwd = RAIZ) {
  planejados.push({ nome, comando, args, cwd })
}

if (opcoes.tudo) {
  plano('API (.NET) — suíte completa', 'dotnet', ['test'])
  plano('Frontend (Vitest) — suíte completa', NPM, ['--prefix', 'ContabOne.Frontend', 'run', 'test'])
  plano('Nfse.Agent (Python) — suíte completa', PY, [...PY_ARGS, 'Nfse.Agent/testes/executar_tudo.py'])
  plano('Det.Agent (Python) — suíte completa', PY, [...PY_ARGS, 'Det.Agent/testes/executar_tudo.py'])
} else {
  const mudados = arquivosMudados()
  if (!mudados.length) {
    console.log('Nada mudou em relação a HEAD — nenhuma suíte para rodar.')
    console.log('Use --base <ref> para comparar com outra referência, ou --tudo para a suíte completa.')
    process.exit(0)
  }

  console.log(`Arquivos mudados (${mudados.length}):`)
  for (const f of mudados.slice(0, 40)) console.log(`  ${f}`)
  if (mudados.length > 40) console.log(`  … e mais ${mudados.length - 40}`)
  console.log('')

  const api = testesApi(mudados)
  for (const m of api.motivos) console.log(`  api: ${m}`)
  if (api.modo === 'tudo') {
    plano('API (.NET) — suíte completa', 'dotnet', ['test'])
  } else if (api.modo === 'filtro') {
    const filtro = api.classes.map((c) => `FullyQualifiedName~${c}`).join('|')
    plano(`API (.NET) — ${api.classes.join(', ')}`, 'dotnet', ['test', '--filter', filtro])
  }

  if (precisaVitest(mudados)) {
    // cwd no próprio repo do frontend: é lá que o `--changed` do Vitest procura
    // o git (o repo da raiz ignora ContabOne.Frontend/ e não veria nada).
    const args = ['exec', '--', 'vitest', 'run', '--changed']
    if (opcoes.base) args.push(opcoes.base)
    plano('Frontend (Vitest) — arquivos afetados', NPM, args, path.join(RAIZ, 'ContabOne.Frontend'))
  }

  for (const pasta of ['Nfse.Agent', 'Det.Agent']) {
    const py = testesPython(mudados, pasta)
    for (const m of py.motivos) console.log(`  ${pasta.toLowerCase()}: ${m}`)
    if (py.modo === 'tudo') {
      plano(`${pasta} (Python) — suíte completa`, PY, [...PY_ARGS, `${pasta}/testes/executar_tudo.py`])
    } else if (py.modo === 'filtro') {
      plano(`${pasta} (Python) — ${py.arquivos.join(', ')}`, PY, [
        ...PY_ARGS,
        `${pasta}/testes/executar_tudo.py`,
        ...py.arquivos,
      ])
    }
  }

  const e2e = playwrightAfetado(mudados)
  if (e2e.length) {
    console.log('')
    console.log(`Aviso: ${e2e.length} arquivo(s) de Playwright mudaram — rode à mão, com a stack no ar:`)
    console.log('  npm --prefix ContabOne.Frontend run test:e2e')
  }
}

console.log('')
if (!planejados.length) {
  console.log('Nenhuma suíte afetada pelo que mudou.')
  process.exit(0)
}

console.log('Vai rodar:')
for (const p of planejados) console.log(`  • ${p.nome}`)
console.log('')

if (opcoes.listar) process.exit(0)

let falhou = false
const resumo = []
for (const p of planejados) {
  console.log(`${'='.repeat(70)}\n${p.nome}\n${'='.repeat(70)}`)
  const inicio = Date.now()
  const r = spawnSync(p.comando, p.args, { cwd: p.cwd, stdio: 'inherit' })
  const ok = r.status === 0
  resumo.push([p.nome, ok, (Date.now() - inicio) / 1000])
  falhou = falhou || !ok
}

console.log(`\n${'='.repeat(70)}\nResumo\n${'='.repeat(70)}`)
for (const [nome, ok, seg] of resumo) console.log(`  ${ok ? 'OK    ' : 'FALHOU'}  ${nome}  (${seg.toFixed(1)}s)`)
process.exit(falhou ? 1 : 0)
