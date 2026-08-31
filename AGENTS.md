# AGENTS.md

Guidance for AI coding agents working in this repository. Written to the
[agents.md](https://agents.md) convention — any tool that reads `AGENTS.md`
should start here.

> **Naming collision, read this first.** In this codebase "agente" is a *domain*
> word: the Python robot that runs on the accounting office's own machine
> (`Nfse.Agent`, `Det.Agent`, `Rfb.Agent`). This file is about *you*, the coding
> assistant. When code, commits or docs say "agent", they mean the robot.

## What this is

**Contab One** — a micro-SaaS hub for Brazilian accounting offices. One panel,
several *ferramentas* (tools), each automating a fiscal or labor obligation.
Four runnable pieces in one monorepo:

| Path | What | Stack |
|---|---|---|
| `ContabOne.Api/` | licensing, multi-tenant data, metrics, catalog | .NET 10 minimal APIs + EF Core + PostgreSQL |
| `ContabOne.Frontend/` | the panel (hub, dashboards, admin) | Vue 3 `<script setup>` + TS + Vite + PrimeVue 4 + Tailwind |
| `Nfse.Agent/` | NFS-e collector — the flagship agent (`nfse.exe`) | Python 3.14 + PyInstaller |
| `Det.Agent/`, `Rfb.Agent/` | DET caixa postal, RFB consumo-tributos credentials | Python + Playwright |

`ContabOne.slnx` covers only the two .NET projects. `Nfse.Agent/`, `Det.Agent/`
and `Rfb.Agent/` are standalone Python trees with their own `requirements.txt` —
they are *not* pip packages and are not installed into each other.

**Read [README.md](README.md) first** — it is the authoritative, up-to-date
description of all three layers and every test suite. This file covers only what
spans multiple files or projects and is easy to regress.
[`Nfse.Agent/CLAUDE.md`](Nfse.Agent/CLAUDE.md) is the deep guide for the NFS-e
robot (portal quirks, control-file invariants, licensing edge cases) — read it
before touching anything under `Nfse.Agent/`, whichever tool you are.

**Language convention:** identifiers, comments, DB columns, JSON fields and
routes are in **Portuguese** (`Escritorio`, `Execucao`, `podeExecutar`,
`/api/execucoes`). Framework-imposed names stay English. Match the surrounding
code — never "translate" existing names.

## Commands

Full stack (Postgres + API + Vite in one terminal, from the repo root):

```bash
npm install && npm run dev
```

Per layer:

```bash
docker compose up -d postgres
```

```bash
dotnet run --project ContabOne.Api
```

```bash
npm --prefix ContabOne.Frontend run dev
```

```bash
npm --prefix ContabOne.Frontend run build
```

`build` is `vue-tsc -b && vite build` — the only typecheck gate in the repo, so
run it after non-trivial frontend edits. API listens on http://localhost:5139
(perfil `http`), Vite on http://localhost:5173.

### Tests

There is no single runner across the three ecosystems. From the repo root:

```bash
dotnet test
```

```bash
dotnet test --filter "Category!=Banco"
```

```bash
dotnet test --filter "FullyQualifiedName~IsolamentoTest"
```

```bash
py -3.14 Nfse.Agent/testes/executar_tudo.py
```

```bash
py -3.14 Nfse.Agent/testes/teste_licenca.py
```

```bash
npm --prefix ContabOne.Frontend test
```

```bash
npm --prefix ContabOne.Frontend exec vitest run src/api/client.spec.ts
```

```bash
npm --prefix ContabOne.Frontend run test:e2e
```

- `Category=Banco` tests need Docker (ephemeral `postgres:18-alpine` via
  Testcontainers). `Category!=Banco` is the ~2s no-Docker layer — use it while
  iterating.
- The Python suite is fully offline (fake HTTP server, fixture folders, no real
  certificate). `py -3.14` matters on this machine: `python` resolves to 3.13
  **without** the dependencies installed.
- Vitest needs nothing running. Playwright E2E needs Postgres + API up and runs
  serial (`workers: 1`) — the API's auth rate limiter turns parallel logins into
  flakes.

### Migrations

```bash
dotnet ef migrations add NomeDaMigration --project ContabOne.Api
```

Never hand-edit `AppDbContextModelSnapshot.cs`. Migrations run automatically on
API startup **and** inside the Testcontainers Postgres on every `dotnet test`,
so a broken migration fails the suite.

> ⚠️ **Never run `dotnet test` with `DATABASE_URL` set.** `Program.cs` reads it
> *before* `ConnectionStrings:Default`, so the test host would migrate your dev
> database instead of the ephemeral container.

Required API env vars (see `ContabOne.Api/.env.example`): `DATABASE_URL`,
`JWT_SIGNING_KEY`, `HMAC_CNPJ_KEY` (**permanent** — rotating it invalidates every
stored `CnpjHash` and duplicates clients; the API refuses to boot without it),
`CORS_ORIGINS` (production only). Cron mode:
`dotnet ContabOne.Api.dll --job=alertas`.

## Architecture — the parts that span files

### The privacy contract that defines the product

The `.pfx` certificate **never leaves the office's machine**, and fiscal content
(note XML/PDF, PGDAS-D documents) **never reaches the API**. Only counts,
metadata and status go up. CNPJs travel as HMAC hashes plus a mask, never in
full. This is what lets the product exist without becoming custodian of hundreds
of third-party digital identities — treat it as a hard constraint in any scope
decision, not a preference.

Two consequences: `ExecucaoMetrica` rows are aggregate counts per
cliente/tipo/competência; and the PGDAS-D importer parses the PDF **in the
browser** (`ContabOne.Frontend/src/features/pgdas/parser/`, pdfjs-dist) and POSTs
only the extracted numbers.

### Multi-tenancy is enforced in one place

`Infra/TenantContext.cs` is populated by `TenantContextMiddleware` from JWT
claims or the agent API key — **never** from a route or query parameter (IDOR).
Every tenant-scoped entity gets a global query filter in `Infra/AppDbContext.cs`,
all shaped
`_tenantContext.VeTodosOsEscritorios || x.EscritorioId == _tenantContext.EscritorioId`.
That flag is **fail-closed**: only `FromAdmin()` sets it, and a null
`EscritorioId` without it means *zero rows*, not "everything" (that was a real
fail-open bug). A new tenant-scoped entity needs its filter added here or it
leaks across escritórios — `IsolamentoTest.cs` is the guard.

Related trap: LINQ predicates over computed properties (e.g. `Alerta.Aberto`)
break EF translation at runtime. `TraducaoLinqTest.cs` proves translatability
with `ToQueryString()` without a database — that defect reached production twice.

### Two auth schemes behind one policy scheme

`Program.cs` registers `JwtOrApiKey`, forwarding to `ApiKey` when the request
carries `X-Api-Key` and to JWT otherwise. Humans get short access tokens plus a
refresh cookie; agents get one API key each, stored hashed.

API key format is `<codigo>_<prefixo8>_<segredo32>` (`nfse_…`, `det_…`,
`pgdas_…`). Lookup is `prefixo8` + `SHA-256(segredo)`; the first field is only
provenance for logs and support. **Authentication never reads the `Produtos`
catalog** — the handler compares the key's código against the agent's own
`Produto.Codigo` from the same JOIN, so editing or disabling a catalog row can
neither grant nor revoke access to an agent already in the field.
`Produto.Codigo` is immutable and its FK is `Restrict`. The one mutable thing
authentication *does* consult is `EscritorioProdutos` — a deliberate commercial
gate, same family as `Escritorio.Status`.

`ApiKeyAuthenticationHandler` rejects non-`Ativo` escritórios with **401 before**
the handshake handler runs — and the Python agent treats 401 as "blocked", never
as "API unreachable", so revocation takes effect immediately and never inherits
the offline grace period. Changing either side breaks revocation.

Authorization policies are a role hierarchy: `EscritorioUsuario` ⊂
`EscritorioAdmin` ⊂ `PlatformAdmin`, plus a separate `Agente`.

### API layout: vertical slices

`Features/<Area>/<Area>Endpoints.cs` — one file per slice, handlers as static
methods, mapped by a `Map…Endpoints()` extension called from `Program.cs`, where
the route group also declares its authorization and rate-limit policies. Adding
an endpoint means editing one feature file plus, for a new group, the
`app.MapGroup` block. `Domain/Entities.cs` and `Domain/Enums.cs` hold the whole
model in two files.

**Enums cross the wire as integers.** No `JsonStringEnumConverter` is registered,
so System.Text.Json's numeric default applies and the Python agent translates in
`api_client.TIPO_NOTA`/`STATUS_EXECUCAO`. Appending an enum member is safe;
reordering is a data migration. JSON is camelCase in both directions.

### Catalog-driven navigation (frontend)

`GET /api/produtos` returns domínios, produtos and the pages each declares;
`stores/catalogo.ts` loads it once at session bootstrap, and the whole menu, the
hub and the `/f/:produto/:pagina` route family derive from it — **no hand-written
menu items**. Publishing a tool to an escritório is admin data work, not a
frontend deploy; only a genuinely new page component needs code.
`router/guards.ts` lets through only the pages the produto declares.

`Produto.TemAgente = false` (PGDAS-D) means the tool lives entirely in the panel:
no binary, no handshake, no `Execucao`.

### Frontend cross-cutting bits

- `src/api/client.ts` — axios with a 401 → refresh → retry interceptor and a
  queue for concurrent failures. `refreshAccessToken()` deliberately uses a raw
  axios instance; routing it through `apiClient` would make a failing refresh
  re-trigger the 401 interceptor recursively. `router/guards.ts` calls that same
  raw helper at bootstrap.
- `VITE_API_URL` is **baked into the build**, not read at runtime.
- Table/button/modal styling is centralized in `src/assets/styles/components.css`
  (design tokens in `tokens.css`). Use the shared classes — e.g. `.col-actions`
  for an action column — instead of per-view CSS, and never put `display:flex`
  on a `<td>`.
- MSW runs with `onUnhandledRequest: 'error'` (`src/testes/setup.ts`): an
  unmocked request fails the test.
- `npm install` may need `--legacy-peer-deps` (`@vee-validate/zod` wants zod@^3,
  the project is on zod@^4).

### Contracts shared between C# and Python

Three things must change in lockstep, each with a test that fails on drift:

1. **CNPJ hashing** — `Security/CnpjHasher.cs` and `Nfse.Agent/api_client.py`
   read the same vectors from `Nfse.Agent/testes/fixtures/cnpj_vetores.json`
   (`HashersTest.cs`).
2. **Encrypted handshake config** — `Security/ConfiguracaoCipher.cs` ↔
   `api_client.decifrar_configuracao()`; AES-256-GCM keyed by
   `HMAC-SHA256(api_key, "nfse-configuracao-v1")` (`HandshakeConfiguracaoTest.cs`).
3. **Collection-rules bundle** — `Domain/RegraColetaValidator.cs` ↔
   `Nfse.Agent/regras.py`, validated against the shared corpus in
   `Nfse.Agent/testes/fixtures/bundles/` (`BundleCorpusTest.cs`).

The Python suite's fake API server (`Nfse.Agent/testes/_fake_api.py`) is modeled
directly on `AgentEndpoints.cs` — changing an agent endpoint's contract means
updating it too.

## Workflow

This repo uses **OpenSpec** (`openspec/`): capability specs in `openspec/specs/`,
in-flight proposals in `openspec/changes/<nome>/`, history in
`openspec/changes/archive/`. Follow that flow — propose, apply, sync, archive —
rather than editing spec files by hand. Tools that ship OpenSpec commands or
skills (`openspec-*`, `opsx:*`, `.opencode/commands/opsx-*.md`) should use them.

The `PLANO_SAAS_*.md` documents were written *before* implementation and say so
in their own headers. Where plan and code disagree, **the code wins**.

Commits and docs are written in Portuguese or English interchangeably; match the
file you are editing.

## Sensitive local data — never commit or echo back

`Nfse.Agent/certificados/*.pfx` (filenames embed the PFX password), everything
under `Nfse.Agent/notas/`, `Rfb.Agent/empresas.xlsx`, `DadosAcesso.txt`, any
`config.toml` (`[api] chave` is a bearer credential) and `_agente_cache.json` are
real client production data. Never print them verbatim, never suggest committing
them, never paste them into an external service.
