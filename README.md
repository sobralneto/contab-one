# contab-one

Micro-SaaS de coleta automatizada de NFS-e do **Portal Nacional**. O repositório
tem **três projetos** que só fazem sentido juntos: um agente que roda na máquina
do escritório contábil, uma API que licencia e recebe métricas, e um painel web
onde o escritório acompanha tudo.

**Vocabulário** — usado igual em todo o código e em toda a documentação:

| Termo | Quem é | Exemplo |
|---|---|---|
| **Plataforma** | dono do SaaS | admin único |
| **Escritório** (tenant) | o cliente pagante | "Contabilidade Silva ME" |
| **Cliente** | empresa dona do certificado, cliente do escritório | "Solution Farma LTDA" |
| **Agente** | o `nfse.exe` rodando na máquina do escritório | 1..N por escritório |

**A regra que sustenta o modelo inteiro:** o certificado `.pfx` **nunca sai da
máquina do escritório**, e o conteúdo fiscal (XML/PDF das notas) **nunca é
enviado para a API**. Sobe só contagem, metadado e status. É isso que permite
vender o produto sem virar custodiante da identidade digital de centenas de
empresas de terceiros — e é uma promessa a preservar em qualquer decisão futura
de escopo.

```
contab-one/
├── Nfse.Agent/          agente Python — mTLS, coleta, DANFSe (vira nfse.exe)
├── ContabOne.Api/       API .NET 10 + PostgreSQL — licenciamento, métricas, multi-tenant
├── ContabOne.Api.Tests/ suíte xUnit da API (Testcontainers)
├── ContabOne.Frontend/  painel Vue 3 + TypeScript + Vite
├── docker-compose.yml   Postgres local (postgres:17-alpine)
├── openspec/            specs e histórico de mudanças (fluxo OpenSpec)
└── PLANO_SAAS_*.md      documentos de projeto das três camadas
```

---

## 1. `Nfse.Agent` — o agente (Python)

Baixa os XML das NFS-e **recebidas e emitidas** de várias empresas e gera o
DANFSe v2.0 em PDF de cada uma, autenticando com o certificado digital A1 via
**mTLS**. Sem navegador e sem captcha — pode ser agendado sem ninguém presente.
É distribuído como executável único (`nfse.exe`, PyInstaller), então o usuário
final não instala Python.

| Módulo | Responsabilidade |
|---|---|
| `nfse.py` | CLI, autenticação, listagem/download, `_controle.json`, orquestração |
| `api_client.py` | todo o diálogo HTTP com a API (handshake, licença, métricas, fila de pendências) |
| `regras.py` | busca/cacheia/valida o bundle de regras de coleta remoto |
| `danfse.py` | renderizador puro XML→PDF do DANFSe v2.0 (NT 008/2026) |
| `build.py` | empacotamento PyInstaller (`dist/nfse/`) |

**Dois modos.** Sem a seção `[api]` preenchida no `config.toml`, o agente roda
em modo legado: zero chamadas de rede além do próprio portal. Com `url` e
`chave` preenchidos, ele se identifica, checa licenciamento (com tolerância
offline assinada em cache), puxa regras de coleta do servidor e reporta métricas
agregadas ao final da execução.

```bash
py -3.14 -m pip install -r requirements.txt
cp Nfse.Agent/config.exemplo.toml Nfse.Agent/config.toml   # e preencha as senhas
py -3.14 nfse.py                      # mês corrente, todas as empresas
py -3.14 nfse.py --mes 2026-06        # mês fechado
py -3.14 nfse.py --empresa 0001       # só um código de empresa
py -3.14 nfse.py --sem-pausa          # para Tarefa Agendada do Windows
```

Detalhes de uso, configuração, padrão de nome dos certificados e conformidade do
PDF com a NT 008: [Nfse.Agent/README.md](Nfse.Agent/README.md). Decisões de
arquitetura e armadilhas do portal: [Nfse.Agent/CLAUDE.md](Nfse.Agent/CLAUDE.md)
e [Nfse.Agent/HANDOFF.md](Nfse.Agent/HANDOFF.md).

> ⚠️ `Nfse.Agent/certificados/*.pfx` e tudo em `notas/` são dados reais de
> clientes de contabilidade — incluindo certificados cujo nome de arquivo embute
> a senha do PFX. Não commitar, não compartilhar, não colar de volta verbatim.

---

## 2. `ContabOne.Api` — a API (.NET 10 + PostgreSQL)

O cérebro e o cofre de licenciamento. Minimal APIs organizadas em **vertical
slices** por área (`Features/Auth`, `Features/Agent`, `Features/Dashboard`, …),
EF Core 10 + Npgsql, multi-tenant por *global query filter*.

| Item | Escolha |
|---|---|
| Runtime | .NET 10 (LTS) |
| Banco | PostgreSQL (migrations rodam no startup) |
| Auth humano | ASP.NET Core Identity + JWT (access curto + refresh) |
| Auth agente | API key por agente, hash no banco (header `X-Api-Key`) |
| Validação | FluentValidation · Logs: Serilog · Docs: OpenAPI + Scalar |
| Rate limit | nativo, particionado por IP — `auth` 10/min, `agent` 60/min |

Grupos de rota: `/api/auth`, `/api/agent`, `/api/dashboard`, `/api/clientes`,
`/api/execucoes`, `/api/alertas`, `/api/configuracao`, `/api/agentes`,
`/api/admin`, mais `/health` (anônimo) e `/api/seed` (**só em Development**).
Há também um modo cron: `dotnet ContabOne.Api.dll --job=alertas`.

Entidades principais: `Escritorio`, `Plano`, `Usuario`, `Agente`, `Cliente`,
`Execucao`, `ExecucaoMetrica`, `RegraColeta`, `ConfiguracaoEscritorio`,
`Alerta`.

```bash
docker compose up -d postgres
cd ContabOne.Api
dotnet run                            # perfil http → http://localhost:5139
```

Variáveis de ambiente obrigatórias (ver [`.env.example`](ContabOne.Api/.env.example)):

| Variável | Observação |
|---|---|
| `DATABASE_URL` | aceita o formato `postgresql://…` do Railway; a API converte |
| `JWT_SIGNING_KEY` | assinatura dos tokens dos usuários |
| `HMAC_CNPJ_KEY` | ⚠️ **permanente** — trocar invalida todo `CnpjHash` gravado e duplica os clientes. A API se recusa a subir sem ela, de propósito |
| `CORS_ORIGINS` | só em produção (em Development qualquer `localhost` passa) |

Documento de projeto: [PLANO_SAAS_API.md](PLANO_SAAS_API.md).

---

## 3. `frontend` — o painel web (Vue 3)

Interface do escritório e da plataforma: dashboard com KPIs e gráficos, gestão
de clientes, agentes, execuções, alertas, configuração e as telas de admin
(escritórios, planos, regras de coleta).

Vue 3 com `<script setup>` + TypeScript + Vite; Pinia para sessão, Vue Router
com guards por papel, PrimeVue 4 (preset Nora) + Tailwind, Chart.js para os
gráficos, Axios com interceptor de refresh automático no 401, vee-validate +
zod nos formulários.

```bash
cd ContabOne.Frontend
npm install                           # use --legacy-peer-deps se necessário:
                                      # @vee-validate/zod pede zod@^3, o projeto usa zod@^4
npm run dev                           # http://localhost:5173
npm run build                         # vue-tsc -b && vite build
```

`VITE_API_URL` é **embutida no build**, não lida em runtime — ver
`.env.development` (`http://localhost:5139`, o perfil `http` do launchSettings
da API). Documento de projeto: [PLANO_SAAS_FRONTEND.md](PLANO_SAAS_FRONTEND.md).

---

## Subindo a stack completa localmente

Na ordem — cada passo em um terminal próprio:

```bash
docker compose up -d postgres
```

```bash
cd ContabOne.Api && dotnet run
```

```bash
cd ContabOne.Frontend && npm run dev
```

O seed de desenvolvimento (`/api/seed`) cria o usuário `admin@nfse.local` com
senha `Admin123!`. Ele só existe fora de produção.

---

## Como rodar os testes dos 3 projetos

Cada camada tem a própria suíte, com o próprio runner. **Nenhuma delas depende
das outras estarem no ar** — exceto os testes E2E do frontend, que são E2E de
verdade e exercitam a stack inteira.

| Camada | Suíte | Comando | Pré-requisito |
|---|---|---|---|
| API (.NET) | `ContabOne.Api.Tests` (xUnit) | `dotnet test` na raiz | Docker (só os `Category=Banco`) |
| Agente (Python) | `Nfse.Agent/testes/` | `py -3.14 testes/executar_tudo.py` | `requirements.txt` instalado |
| Frontend — rápida | Vitest, `src/**/*.spec.ts` | `npm test` | nada no ar |
| Frontend — E2E | Playwright, `ContabOne.Frontend/e2e/` | `npm run test:e2e` | Postgres + API + navegador |
| Frontend — telas de regras | Playwright, `ContabOne.Frontend/testes-ui/` | `npx playwright test` | Postgres + API + Vite |

### API — `dotnet test`

Rode na **raiz** do repositório (a solution `ContabOne.slnx` já aponta
para o projeto de testes):

```bash
dotnet test
```

```bash
dotnet test --filter "Category!=Banco"
```

- Sem filtro: suíte completa — hoje **51 testes**, ~15s com a imagem já baixada.
  Os testes marcados `[Trait("Category", "Banco")]` sobem um **Postgres efêmero**
  via Testcontainers (`postgres:17-alpine`, a mesma tag do `docker-compose.yml`)
  e exercitam os endpoints reais pelo host in-process
  (`WebApplicationFactory<Program>`).
- Com `Category!=Banco`: a camada rápida — hoje **21 testes**, ~2s, **sem
  Docker**. Útil no meio de uma edição.
- As migrations rodam no container a cada execução, inclusive o seed da
  `RegraColeta` v1 — então mudança de migration é exercitada pela suíte.

> ⚠️ **Nunca rode a suíte com `DATABASE_URL` setada apontando para o banco de
> desenvolvimento.** Os testes com banco usam a connection string do container
> efêmero, mas `DATABASE_URL` tem precedência no `Program.cs` (antes de
> `ConnectionStrings:Default`) — o startup do host de teste migraria o seu banco
> de dev.

O que a suíte cobre:

- **Guarda de tradução LINQ** (sem banco): `ToQueryString()` prova que os
  predicados com propriedades computadas (`Alerta.Aberto`) continuam traduzíveis
  — o defeito que já chegou duas vezes em produção.
- **Contrato dos endpoints do agente**: handshake (camelCase, chave HMAC),
  upsert de clientes (mapa `codigo → id`, limite do plano), métricas (`tipo`
  como inteiro), finalização, regras (304/404).
- **Isolamento multi-tenant**: agente e usuário de um escritório não enxergam
  dados de outro, nem forçando pelo parâmetro de query.
- **AlertaJob**: certificados vencidos/a vencer, agente silencioso,
  idempotência, varredura de todos os escritórios sem abortar no meio.
- **Hashers**: formato da API key, máscara de CNPJ, e **paridade do hash de CNPJ
  com o agente Python** — os dois lados leem os mesmos vetores de
  `Nfse.Agent/testes/fixtures/cnpj_vetores.json`.

### Agente — `testes/executar_tudo.py`

```bash
cd Nfse.Agent
py -3.14 testes/executar_tudo.py
```

```bash
py -3.14 testes/teste_licenca.py
```

- O runner executa cada `teste_*.py` em **subprocess isolado** (um teste que
  trava ou vaza estado não contamina o próximo) e devolve exit code 0/1 — dá
  para usar como gate antes de `py -3.14 build.py`.
- Hoje são **10 arquivos de teste**, ~30s no total.
- Suíte 100% **offline**: fake HTTP server local modelado em
  `AgentEndpoints.cs`, pastas e HTML de fixture, nenhum certificado real. Inclui
  o corpus de bundles de regras (`testes/fixtures/bundles/`) compartilhado com o
  validador C#.
- `_fake_api.py` e `_harness.py` são fixtures compartilhadas, não testes.

> **Escolha do interpretador:** "offline" não quer dizer "sem dependências" — os
> testes importam `api_client`, que importa `requests`. Use o Python onde o
> `requirements.txt` está instalado. Nesta máquina há dois: `python` resolve
> para 3.13 (**sem** as dependências) e `py -3.14` para 3.14 (**com**) — por isso
> os comandos acima usam `py -3.14`. Se `python` for o seu interpretador
> configurado, use `python` e ignore essa distinção.

### Frontend — três suítes

**Rápida (Vitest)** — unitários e componentes, hoje **61 testes em 8 arquivos**,
~15s:

```bash
cd ContabOne.Frontend
npm test
```

```bash
npm run test:watch
```

- Ambiente jsdom, specs ao lado do código (`src/**/*.spec.ts`).
- **MSW** intercepta a rede no nível do transporte, então os testes do
  interceptor de refresh do `apiClient` (fila de requisições, `_retry`,
  redirecionamento) passam pelos interceptors de verdade.
- `src/testes/setup.ts` liga o MSW com `onUnhandledRequest: 'error'` — uma
  requisição não mockada **falha** o teste.
- **Não precisa de nada no ar**: nem API, nem Postgres.

**E2E (Playwright)** — hoje **6 testes em 4 arquivos**, contra a stack real:

```bash
npx playwright install chromium
```

```bash
npm run test:e2e
```

Antes disso, Postgres e API precisam estar no ar (ver *Subindo a stack completa*
acima). O Vite o próprio Playwright sobe, pelo `webServer` do config.

- O `globalSetup` confere `/health` e `/api/seed/status` **antes** de subir o
  Vite e falha com instruções do que subir, em vez de dar um timeout genérico.
- Caminhos cobertos: login→dashboard (incluindo a sobrevivência do cookie de
  refresh a um reload), login inválido, cadastrar cliente (com e sem código
  duplicado), gerar chave de agente, admin suspender escritório.
- Execução **serial** (`workers: 1`): o rate limiter de auth da API (10/min por
  IP, fila 2) vira flake com logins simultâneos de vários workers. Rodando
  várias execuções seguidas, reinicie a API entre elas — a janela do limiter é
  de 1 minuto e acumula os logins das execuções anteriores.
- Cada teste que cria dado usa sufixo único, então repetir a execução não colide
  nos índices únicos. O banco de teste acumula — aceitável localmente; para
  isolar, aponte `DATABASE_URL` para um banco separado.

**Telas de regras (`testes-ui/`)** — 5 testes, pacote npm próprio para não
poluir as dependências do app:

```bash
cd ContabOne.Frontend/testes-ui
npm install
npx playwright test
```

Requer API em `http://localhost:5139` (com o seed dev) e Vite em
`http://localhost:5173` já no ar — este pacote **não** sobe o Vite sozinho e não
tem `globalSetup`, então uma stack fora do ar aparece como timeout, não como
mensagem explicativa.

### Rodando as três de uma vez

Não há runner único que agregue as três camadas — são três ecossistemas com três
gerenciadores de dependência. O equivalente prático, a partir da raiz:

```bash
dotnet test && py -3.14 Nfse.Agent/testes/executar_tudo.py && npm --prefix frontend test
```

Isso cobre a API completa, o agente e a suíte rápida do frontend (~1 min no
total, com Docker no ar). As duas suítes Playwright ficam de fora de propósito:
exigem a stack levantada e escrevem no banco de desenvolvimento.

---

## Documentação de referência

| Documento | Conteúdo |
|---|---|
| [PLANO_SAAS_API.md](PLANO_SAAS_API.md) | modelo do produto, stack e desenho da API |
| [PLANO_SAAS_FRONTEND.md](PLANO_SAAS_FRONTEND.md) | stack, identidade visual e telas do painel |
| [PLANO_SAAS_AGENTE.md](PLANO_SAAS_AGENTE.md) | o que mudou na ferramenta local ao virar agente |
| [Nfse.Agent/README.md](Nfse.Agent/README.md) | uso da ferramenta pelo usuário final |
| [Nfse.Agent/HANDOFF.md](Nfse.Agent/HANDOFF.md) | decisões de arquitetura e bugs já encontrados |
| [ContabOne.Frontend/README.md](ContabOne.Frontend/README.md) | detalhe das suítes do frontend |
| `openspec/specs/` | specs por capacidade · `openspec/changes/archive/` o histórico |

> Os três `PLANO_SAAS_*.md` foram escritos **antes** da implementação e trazem
> "Status: plano, nada implementado" no cabeçalho. Hoje as três camadas estão
> implementadas — vale o que o próprio documento diz: se o plano e o código
> discordarem, **o código manda**.
