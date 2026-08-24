# Frontend — Contab One

Interface web (Vue 3 + TypeScript + Vite) do painel do hub Contab One.

## Navegação: hub, domínios e ferramentas

O painel atende mais de uma ferramenta (NFS-e, DET, e as que vierem depois),
agrupadas por domínio — o departamento do escritório contábil que cada uma
atende (Fiscal, DP, Contábil). A navegação inteira é **derivada do catálogo**
que `GET /api/produtos` devolve, carregado uma vez no bootstrap da sessão em
`stores/catalogo.ts` — nada de item de menu escrito à mão.

- **`/`** é o hub: cards de ferramenta agrupados por domínio. Escritório vê
  card navegável só do que contratou; o que é ativo mas não contratado
  aparece como card informativo (sem link, sem contato comercial). Admin da
  plataforma sempre navega para qualquer ferramenta ativa.
- **`/f/:produto/:pagina`** é a família de rotas de cada ferramenta —
  `:produto` é o mesmo `codigo` do catálogo que prefixa a chave de API
  (`nfse`, `det`, …). `:pagina` é uma de `visao-geral`, `clientes`,
  `execucoes`, `agentes`, `configuracao`; o guard (`router/guards.ts`) só
  deixa passar a que a ferramenta declara em `Produto.Paginas`.
- As rotas de antes de existir mais de uma ferramenta (`/dashboard`,
  `/clientes`, `/execucoes`, `/agentes`, `/configuracao`) continuam
  existindo como redirect permanente para o equivalente em `/f/nfse/…`.
- `layouts/AppLayout.vue` monta o menu lateral a partir do catálogo:
  domínio vira título de seção, ferramenta contratada vira item, página
  declarada vira submenu. `IconeCatalogo.vue` resolve `Dominio.Icone` (nome
  de ícone salvo no banco) contra um mapa local; nome desconhecido cai num
  ícone genérico — nunca deixa o item sem ícone.

**Para publicar uma ferramenta nova**, o trabalho é praticamente todo do
lado da API: cadastrar o produto em `/admin/produtos` com domínio e páginas
(criando o domínio antes, se for novo) e contratá-lo para os escritórios
certos. O frontend não precisa de deploy — o menu, o hub e as rotas
aparecem sozinhos assim que o catálogo os declara. O que ainda exige código
novo é a página em si (o componente Vue de cada `pagina` que a ferramenta
declarar) e, hoje, `Cliente`/`Execucao`/`Configuracao` continuam sendo dados
globais por escritório, não por produto — ferramenta nova convive com essa
limitação até isso ser escopado.

## Desenvolvimento

```bash
npm install        # instala dependências (usa --legacy-peer-deps: o
                   # @vee-validate/zod pede zod@^3 e o projeto usa zod@^4)
npm run dev        # vite dev server em http://localhost:5173
npm run build      # vue-tsc -b && vite build (typecheck + build de produção)
```

`VITE_API_URL` é embutida no build (não lida em runtime) — ver `.env.development`
(`http://localhost:5139`, o perfil `http` do launchSettings da API).

## Suítes de teste

### Rápida — Vitest (unitários + componentes)

```bash
npm test           # roda uma vez
npm run test:watch # modo watch
npm run test:ui    # interface web do Vitest
```

- Ambiente jsdom, `src/**/*.spec.ts` ao lado do código.
- **MSW** intercepta a rede no nível do transporte: os testes do interceptor
  de refresh do `apiClient` (fila de requisições, `_retry`, redirecionamento)
  passam pelos interceptors de verdade.
- `src/testes/setup.ts` liga o MSW com `onUnhandledRequest: 'error'` — uma
  requisição não mockada falha o teste.
- **Não precisa de nenhum serviço no ar** (nem API, nem Postgres).

### E2E — Playwright (stack real)

```bash
# 1. Postgres no ar
docker compose up -d postgres

# 2. API em Development (o /api/seed só existe fora de produção), com as
#    variáveis obrigatórias:
#    cd ContabOne.Api && dotnet run    (com HMAC_CNPJ_KEY e JWT_SIGNING_KEY setadas)

# 3. Navegadores do Playwright (passo único de preparação):
npx playwright install chromium

# 4. Rodar
npm run test:e2e
```

- O `globalSetup` verifica `/health` e `/api/seed/status` **antes** de subir o
  vite e falha com instruções se a stack não estiver no ar.
- O Playwright sobe o `vite dev` sozinho (`webServer` do config).
- Caminhos cobertos: login→hub→visão geral do NFS-e (inclui sobrevivência do
  cookie de refresh a um reload e o redirect dos endereços de antes de
  existir mais de uma ferramenta), login inválido, cadastrar cliente (com e
  sem código duplicado), gerar chave de agente, admin suspender escritório.
- Execução serial (`workers: 1`): o rate limiter de auth da API
  (10/min por IP, fila 2) vira flake com logins simultâneos de vários workers.
  Se rodar várias execuções seguidas, reinicie a API entre elas — a janela do
  limiter é de 1 minuto e acumula logins de execuções anteriores.
- Cada teste que cria dado usa sufixo único, então execuções repetidas não
  colidem nos índices únicos. O banco de teste acumula — aceito para execução
  local; para isolar, aponte `DATABASE_URL` para um banco separado.
