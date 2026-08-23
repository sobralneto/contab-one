# Frontend — Contab One

Interface web (Vue 3 + TypeScript + Vite) do SaaS de coleta de NFS-e.

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
- Caminhos cobertos: login→dashboard (inclui sobrevivência do cookie de
  refresh a um reload), login inválido, cadastrar cliente (com e sem código
  duplicado), gerar chave de agente, admin suspender escritório.
- Execução serial (`workers: 1`): o rate limiter de auth da API
  (10/min por IP, fila 2) vira flake com logins simultâneos de vários workers.
  Se rodar várias execuções seguidas, reinicie a API entre elas — a janela do
  limiter é de 1 minuto e acumula logins de execuções anteriores.
- Cada teste que cria dado usa sufixo único, então execuções repetidas não
  colidem nos índices únicos. O banco de teste acumula — aceito para execução
  local; para isolar, aponte `DATABASE_URL` para um banco separado.
