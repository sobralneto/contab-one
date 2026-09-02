## Context

`Nfse.Agent` already proved the agent↔SaaS pattern: `config.toml` with
`[api]`, handshake + offline-grace licensing, encrypted per-office config,
CNPJ upsert, execution/metrics reporting with a local pending-queue on
failure. `Det.Agent` is a separate Python tree (Playwright, not
`requests`/mTLS) that has none of this — it authenticates to gov.br with a
certificate the browser handles, reads a fixed `empresas.xlsx`, and writes
JSON + CSV to disk. This change wires `Det.Agent` into the same platform
contract without touching `Nfse.Agent` or the shared endpoints it already
uses.

The one real divergence from the NFS-e precedent: `ExecucaoMetrica` is
aggregate counts by design (`AGENTS.md`'s privacy contract — fiscal content
never reaches the API). DET messages are not fiscal documents, and the
whole point of this change is that the panel needs to *show* them, so this
change stores actual message content server-side. That's a deliberate,
narrower exception, not a precedent for loosening the NFS-e/PGDAS-D rule.

## Goals / Non-Goals

**Goals:**
- `Det.Agent` requires `[api] url`/`chave` to run, same as `Nfse.Agent`.
- Reuse `POST /api/agent/clientes`, `POST /api/agent/execucoes`,
  `.../finalizar` as-is — no changes to `Nfse.Agent`'s contract.
- Add one new endpoint pair (agent-side send, panel-side query) for DET
  message content, plus the table backing it.
- Add a catalog-driven page so the panel can list/filter those messages.
- Stop `Det.Agent` from writing the daily CSV as part of the normal run.

**Non-Goals:**
- Switching `empresas.xlsx` to the API as the source of truth for the
  company list (`fontes.py` already isolates that swap for later).
- Changing how `Det.Agent` authenticates to gov.br (certificate/Playwright
  flow is untouched).
- Building a rules-bundle equivalent (`regras.py`/`RegraColeta`) for DET —
  nothing in DET's scraping logic is server-tunable today, so it's not part
  of this change.
- Retrofitting `Nfse.Agent` or its endpoints.

## Decisions

**Reuse `api_client.py`'s shape, don't share the module.** `Det.Agent` gets
its own `api_client.py`, modeled line-for-line on `Nfse.Agent`'s (handshake,
licence/offline-grace cache, CNPJ hash/mask helpers, pending-queue), rather
than extracting a shared package. The two agent trees are already
independent (`AGENTS.md`: "not pip packages, not installed into each
other") and Playwright's async/sync model plus DET's CLI differ enough that
a shared abstraction would cost more than the ~300 lines of duplication it
saves. If a third agent needs this later, that's the point to extract a
shared package — not before.

**New table, not a repurposed `ExecucaoMetrica`.** `ExecucaoMetrica` is
`(ExecucaoId, ClienteId, Tipo, Competencia)` aggregate counts — there is no
row-per-notification shape to reuse, and forcing DET's content into it would
mean stashing message text in a metric field. A new `MensagemDet` entity
(`Id, ExecucaoId, ClienteId, IdMensagemPortal, Numero, DataEnvio,
DataLeitura, Prazo, Remetente, Tipo, Assunto, Situacao, Link, RecebidaEm`)
mirrors the CSV/JSON shape `Det.Agent` already produces
(`campos_extras` stays local-only — it's a calibration aid for the robot,
not something the panel needs).

**Upsert-by-key on resend, same pattern as `EnviarMetricasAsync`.** Identity
for dedup is `(ExecucaoId, ClienteId, IdMensagemPortal)`. `Det.Agent` already
computes `hash_linha`/`id_mensagem` per message; reusing `IdMensagemPortal`
(the portal's own message id) as the natural key avoids inventing a second
identity scheme.

**New endpoints live in `AgentEndpoints.cs` (agent-facing) and a small
`DetEndpoints.cs` (panel-facing query), not a parallel `Det` route group.**
`POST /api/agent/execucoes/{id}/mensagens-det` follows the existing
`.../metricas` sibling exactly (same guard helpers, same tenant-scoping
pattern via `clientesDoTenant`). The panel query
(`GET /api/det/mensagens?clienteId=`) is a new authenticated (JWT, not
agent key) endpoint scoped by `TenantContext`, parallel to how
`ExecucoesEndpoints.cs` already serves the panel.

**Produto `det` catalog row is data, not code.** Per `AGENTS.md`
("Publishing a tool to an escritório is admin data work, not a frontend
deploy"), creating the `Produto` row (código `det`, `Paginas` including the
new page id) happens through the existing admin flow, not a seed migration.
The migration in this change only adds the `MensagensDet` table and its
`IsolamentoTest` coverage.

**CSV generation removed from the main run, not deleted from the codebase.**
`relatorio.py`'s CSV writer stays, reachable only through
`tools/exportar_csv.py` (already a separate entry point per the current
README). `runner.py` stops calling it automatically when `[api]` is
configured and the send succeeds. If `[api]` is absent (e.g. someone runs a
checked-out copy of `Det.Agent` before onboarding), the CSV keeps being
written — same "no `[api]` means old behavior" rule `Nfse.Agent` follows.

## Risks / Trade-offs

- **[Duplicated agent-client logic across two Python trees]** → accepted per
  the decision above; the offline pending-queue and licence-cache signing
  code is small and stable, and `Nfse.Agent/testes/_fake_api.py`'s pattern
  (offline fake server modeled on the real endpoints) is reusable as a
  template for `Det.Agent`'s own test fixtures.
- **[Real message content — sender, subject, deadline — now leaves the
  office machine, unlike the NFS-e/PGDAS-D metrics-only rule]** → this is
  the explicit point of the change (the panel needs to show it), not an
  oversight. Scope stays narrow: only the fields already in the current CSV
  travel, nothing from `campos_extras`, and standard multi-tenant isolation
  (`AppDbContext` global query filter + `IsolamentoTest`) applies to the new
  table like every other tenant-scoped entity.
- **[Existing `Det.Agent` operators relying on the daily CSV lose it on
  upgrade]** → `tools/exportar_csv.py` covers the manual/ad-hoc case; the
  proposal calls this out as **BREAKING** for anyone depending on the
  automatic file.
- **[No rules-bundle for DET means portal-selector drift needs a code
  release, unlike NFS-e's remotely-updatable rules]** → acceptable for now
  per Non-Goals; DET's own README already documents `--dump` as the
  recalibration path when the portal's layout changes.

## Migration Plan

1. Ship the API side first (migration + endpoints) — additive, no impact on
   `Nfse.Agent` or existing panel views.
2. Ship `Det.Agent`'s `config.toml`/`api_client.py`/`runner.py` changes.
   Until an escritório's `Det.Agent` is reconfigured with `[api]`, behavior
   is unchanged (CSV still written, no network calls beyond gov.br) — same
   opt-in gate `Nfse.Agent` uses.
3. Create the `det` `Produto` catalog row and enable it per escritório
   through the admin panel (data work, done after the code ships, per
   escritório's rollout).
4. Ship the frontend page once the produto/página are in the catalog, so it
   never renders for an escritório that hasn't opted in.

No rollback complexity beyond normal deploy revert: the new table and
endpoints are additive, and an unconfigured `Det.Agent` keeps working
exactly as it does today.

## Open Questions

- Exact `Produto.Paginas` id/route for the new page — decide during
  implementation, following the existing `PaginaFerramenta` naming
  convention (`FerramentaVisaoGeralView.vue`/`ExecucoesView.vue` siblings).
- Whether `Det.Agent`'s existing `.env`/`empresas.xlsx` split should also
  fold the certificate password read out of `.env` entirely once
  `config.toml` exists, or keep `.env` around for `DET_PFX_SENHA` as a
  fallback env var (the modified `configuracao-local-agente` spec already
  allows both — a fallback env var per agent — so this is an implementation
  choice, not a spec question).
