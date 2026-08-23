# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Windows tool that downloads received and issued NFS-e (Brazilian municipal
service invoices) from the Portal Nacional NFS-e for one or more companies,
authenticating with an A1 digital certificate (`.pfx`) via mTLS — no browser,
no captcha — and generates a DANFSe v2.0 PDF for each note. Distributed as a
single-file Windows executable (`nfse.exe`, PyInstaller) so end users need no
Python installed. Not a git repository — there's no `git log`/history to
consult; treat [HANDOFF.md](HANDOFF.md) as the changelog/decision record
instead.

Since 01/08/2026 this is also the **agent** of a small SaaS
(`ContabOne.Api`, a sibling .NET project one level up at `../ContabOne.Api/`;
see [PLANO_SAAS_AGENTE.md](../PLANO_SAAS_AGENTE.md)): with an optional
`[api]` section filled in `config.toml`, it identifies itself, checks
licensing, reports aggregate metrics and certificate metadata (never note
content, never the `.pfx`, never a password, never a full CNPJ), and can
pull collection rules from the server. Without `[api]` configured, behavior
is byte-for-byte what it was before — zero network calls beyond the portal
itself. See the "Agent/SaaS integration" section below for the parts that
are easy to regress.

For deep rationale beyond what's below, read (in this order):
[README.md](README.md) (user-facing usage), [HANDOFF.md](HANDOFF.md)
(architecture decisions and bugs already found/fixed, including a whole
section on the agent — read before "fixing" something that looks odd),
[PLANO_SAAS_AGENTE.md](../PLANO_SAAS_AGENTE.md) (the plan behind the agent
integration — mostly implemented now; "if code and plan disagree, code
wins" per that doc's own header). [PLANO_DASHBOARD.md](PLANO_DASHBOARD.md)
is the design doc of the local dashboard, a feature that was implemented and
then removed on 09/08/2026 — read it only as history, never as a to-do list.

## Commands

```
python -m pip install -r requirements.txt   # requests, requests-pkcs12, reportlab, cryptography
python nfse.py                              # run: current month, all companies in certificados/
python nfse.py --mes 2026-06                # closed month
python nfse.py --inicio 01/05/2026 --fim 15/05/2026
python nfse.py --empresa 0001               # only that company code
python nfse.py --tipos recebidas            # or emitidas; default is both
python nfse.py --somente-lista              # only CSV listing, no XML/PDF download
python nfse.py --sem-pdf                    # download XML but skip PDF generation
python danfse.py nota.xml [saida.pdf]       # generate a DANFSe PDF standalone from one XML

python -m pip install pyinstaller
python build.py                             # builds dist/nfse/nfse.exe (see build.py notes below)

python testes/executar_tudo.py              # run the whole offline test suite (~20s)
python testes/teste_licenca.py              # or just one file
```

`testes/` (added 01/08/2026) holds the offline suite, checked in — not a
Claude session scratchpad like the tool's earlier tests were (see
[HANDOFF.md](HANDOFF.md) "Testes existentes" for what was lost when the
original `teste_nfse.py`/`teste_controle.py`/`teste_interrupcao.py`
scratchpad files became unreachable across sessions, and what was
reconstructed to cover the same ground). `testes/_fake_api.py` and
`testes/_harness.py` are shared fixtures, not tests themselves — a local
`http.server`-based fake of `/api/agent/*`, modeled directly on
`ContabOne.Api/Features/Agent/AgentEndpoints.cs`. When changing parsing,
control-file, backfill, or agent/licensing logic, add or extend an offline
`testes/teste_*.py` (fake folders/HTML/HTTP fixtures — no network, no real
certificate needed) rather than trusting a manual run against the live
portal or a live API.

## Architecture

Four independent, individually-importable modules plus a packaging script:

- **`nfse.py`** — CLI entry point, auth, listing/download, per-client control
  state, and orchestration of the agent bits below. Everything routes through
  `main()`.
- **`api_client.py`** — all HTTP dialogue with `ContabOne.Api` (handshake/
  licensing incl. the signed offline-grace cache, remote-rules fetch, metrics/
  execution reporting, client upsert, the local pending-queue), plus the pure
  CNPJ masking/hashing functions. No dependency on `nfse.py` (import
  direction is always `nfse.py → api_client.py`, never the reverse) — fully
  testable in isolation against a fake HTTP server.
- **`regras.py`** — fetches/caches/validates the remote collection-rules
  bundle and holds the embedded factory-default bundle. Depends on
  `api_client.py` for the actual HTTP call, not on `nfse.py`.
- **`danfse.py`** — pure XML→PDF renderer for the DANFSe v2.0 layout (NT
  008/2026). No network. Callable standalone (`python danfse.py nota.xml`) or
  imported (`gerar(xml_bytes, destino)` / `gerar_de_arquivo(path)`).
- **`build.py`** — PyInstaller packaging. Not part of the runtime; only run
  when producing a distributable.

Unlike `danfse` (lazily imported inside `gerar_pdf()`, degrades gracefully if
missing), `nfse.py` imports `api_client`/`regras` at module top level, same
tier as `requests` — they're core to what this tool is now, not optional
add-ons; a missing one is a packaging bug, not a "feature unavailable" case.

There used to be a fifth module, `dashboard.py` (+ a `dashboard.html`
template), producing a local HTML report out of the `notas/` tree. **Removed
on 09/08/2026** — the escritório's panel is the SaaS frontend
(`../ContabOne.Frontend/`), fed by the metrics the agent already reports, and a second
implementation of the same report with client names and full CNPJs sitting
in clear text under `notas/` was sensitive-data surface with no upside.
Nothing else in the code depended on it. `PLANO_DASHBOARD.md` stays in the
folder as history only — do not treat it, or the leftover `_dashboard.*`
files on machines that ran older versions, as something to restore.

### Why no Playwright/browser

mTLS with `requests` + `requests-pkcs12` does everything a browser would for
certificate auth, at a fraction of the size (no ~150MB Chromium runtime). The
`.pfx` is loaded into memory per run and never written to disk in clear text
or installed into the Windows certificate store (`requests_pkcs12` uses a
temp file with a random 128-bit password, deleted immediately). Don't
reintroduce a browser dependency for this without a strong reason — it was a
deliberate rejection, not an oversight.

### Portal quirks nfse.py works around (non-obvious, easy to regress)

- **31-day filter limit.** Longer ranges return "Nenhum registro encontrado"
  with no error. `janelas()` splits any requested range into ≤31-day windows.
- **Pagination param is `pg`, not `pagina`.** Getting this wrong silently
  truncates results to the first page (15 rows) with no error — this exact
  bug shipped once and was only caught by a month with 53 notes.
- **`/Notas/Recebidas` requires `executar=1` in the querystring;
  `/Notas/Emitidas` must NOT have it** (returns empty otherwise). See the
  `LISTAGENS` dict in `nfse.py` for both routes' quirks side by side.
- Listing HTML is parsed with regex, not BeautifulSoup, deliberately — the
  only assumption relied on is the stable URL pattern
  `/Notas/Download/NFSe/{chave}` for extracting the key; everything else
  about the table structure is treated as unstable.

### Certificate → company parsing (`ler_certificado` in nfse.py)

Every `.pfx` in `pasta_certificados` becomes one company. Filename pattern:
`codigoEmpresa_CNPJ_NomeEmpresa_s.SENHA_v.DD.MM.AAAA.pfx`. Password and
validity are optional in the filename; the one field that must always
resolve is `codigo` (text before the first `_`, or the whole stem if there's
no `_`) — it's the join key for the client folder, so parsing degrades
gracefully rather than failing on an off-pattern filename.

**Password resolution order** (`senha_da_empresa`) — filename → `config.toml
[senhas]` **by the certificate's filename** (`empresa.pfx.name`, not
`codigo` — changed by `agente-config-minima-cifrada` so password lookup
doesn't depend on any filename convention) → `config.toml senha_padrao` →
env var `NFSE_PFX_SENHA` → immediate `RuntimeError`. There is deliberately
**no interactive password prompt anywhere**, ever. A prior version tried to
detect "is someone at the console?" via `isatty()` and that check failed in
testing, hanging an unattended run for 5 minutes waiting on input that would
never come. Do not add `input()`/`getpass()` here even for a "nicer"
interactive mode.

### Client folder resolution (`pasta_da_empresa` in nfse.py)

The client's output folder is found **by company code prefix**, not by the
current name in the certificate — scans `pasta_saida` for a folder starting
with `{codigo}_`. This means a company renaming itself (new cert filename)
keeps writing into the same folder instead of forking history. If duplicate
code-prefixed folders exist, the tool warns and picks the most recently
modified one (manual consolidation is on the user).

### Per-client control file (`_controle.json`, one per client folder)

```json
{"versao": 1,
 "backfill_concluido": {"recebidas": true, "emitidas": false},
 "notas_baixadas": {"recebidas": ["chave1", ...], "emitidas": [...]}}
```

Two responsibilities, both load-bearing for correctness:

1. **Backfill.** A client with no `backfill_concluido[tipo]` yet has its
   search start date extended back to `primeira_busca_desde` (config.toml)
   regardless of what was requested, so onboarding a new client doesn't
   require someone remembering to run an old date manually once.
2. **Dedup.** Before hitting the XML API for a key, skip if the `.xml`
   already exists on disk OR the key is already in `notas_baixadas` — the
   second check matters for notes whose file was later moved/archived out of
   the folder; disk existence alone isn't reliable for "already fetched."

**Critical invariant: `backfill_concluido` is only set after the entire
download loop for that period finishes with zero failures** — never right
after listing. Setting it earlier was a real bug: an interruption mid-download
(power loss, window closed) would make the next run see "backfill already
done" and only re-query the originally requested period, permanently
orphaning the months in between. If you touch backfill logic, preserve this
ordering and the "zero failures" gate (`falhas_neste_tipo == 0` in
`processar_empresa`).

Writes are atomic (`.tmp` + `replace`) to survive a crash mid-write.
PDF generation is **not** gated by this control file at all — only the XML
download is (network cost); PDF re-generation is checked purely by whether
the `.pdf` file already exists on disk, since it's a free local operation
(this is why fixing a `danfse.py` rendering bug and re-running is enough to
regenerate all PDFs — just delete the ones you want rebuilt).

### Agent/SaaS integration (`api_client.py`, `regras.py`)

Only active when `config.toml` has `[api]` with both `url` and `chave`
non-empty (`carregar_config` sets `config["api"] = {}` otherwise, and that's
the gate everything checks — `if config["api"]:`). Without it, `main()`
never imports past the module-level `import api_client`/`import regras`, and
makes zero network calls beyond the portal. Runs, in order, at the top of
`main()`, before `listar_empresas()` — i.e. before any `.pfx` is touched:

1. **`api_client.avaliar_licenca()`** — handshake, then the offline-grace
   decision. The single most important non-obvious fact here: **HTTP 401
   from `/api/agent/*` (bad/revoked key, or an escritório whose `Status` in
   the real API isn't `Ativo`) is never treated as "API unreachable."** It's
   its own exception (`ApiCredenciaisInvalidas`) and always blocks
   immediately — never falls into the offline-grace path, even with a
   perfectly valid, fresh, signed cache sitting right there. Getting this
   wrong would mean revoking a key or suspending a delinquent account takes
   up to `tolerancia_offline_dias` to actually take effect, defeating the
   point of revocation. Confirmed by reading `ApiKeyAuthenticationHandler.cs`
   directly: it rejects non-`Ativo` escritórios at 401 before the handshake
   handler's own `podeExecutar`/`mensagem` logic for
   Inadimplente/Suspenso/Cancelado is ever reached — that switch statement in
   `AgentEndpoints.HandshakeAsync` is currently dead code for those statuses;
   this file wasn't changed to fix that (out of scope), just documented and
   covered by `teste_licenca.py`'s
   `teste_401_nunca_herda_carencia_mesmo_com_cache_valido`.
2. The offline-grace cache (`_agente_cache.json`) is HMAC-signed with the
   agent's own configured API key as the secret — not a server signature (the
   real API doesn't sign anything). This is not tamper-proof against someone
   willing to read the code (the key that signs it lives in the same
   `config.toml` a user can already edit); it only stops the *trivial* attack
   the plan calls out — hand-editing `podeExecutar`/the timestamp in a text
   editor to reset the grace-period clock. See the long comment on
   `api_client._assinar_payload`.
3. **The handshake's `configuracao` block (escritório settings — tipos,
   `primeira_busca_desde`, `pasta_saida`, `gerar_pdf`, `dias_busca_padrao`)
   arrives encrypted** as `configuracaoCifrada` (AES-256-GCM,
   `base64(nonce[12] ‖ ciphertext ‖ tag[16])`), not as a plain dict. The
   symmetric key is `HMAC-SHA256(key=api_key_bruta, msg="nfse-configuracao-v1")`
   — **not a new secret**: the API already sees the raw API key on every
   authenticated request (even though it only persists the SHA-256 hash via
   `ApiKeyHasher`), and the agent already has the same key in
   `config["api"]["chave"]`. `api_client.decifrar_configuracao()` decrypts
   right after the handshake responds, before `salvar_cache_licenca()` — the
   cache stores the decrypted dict, never the envelope. Decrypt failure
   (wrong/rotated key, corrupted payload, or an old API that doesn't send
   the field) is never `erro_fatal()` — same "invalid remote value" policy
   as everything else here: log a warning, fall back to `config.toml`
   local. Mirror image on the API side:
   `ContabOne.Api/Security/ConfiguracaoCipher.cs`.
4. **`regras.resolver_bundle()`** then **`nfse.aplicar_regras()`** —
   overwrite the module globals `LISTAGENS`, `MAX_DIAS_FILTRO`,
   `PARAM_PAGINA`, `URL_NOTAS`, `URL_LOGIN_CERTIFICADO`, `URL_API_NFSE`, and
   the three parsing regexes (`REGEX_CHAVE`/`REGEX_LINHA`/
   `REGEX_TOTAL_REGISTROS`) from a validated remote bundle. Without `[api]`
   configured, `aplicar_regras()` is simply never called and every one of
   those globals keeps its original factory value — the pure functions that
   read them (`montar_url`, `extrair_notas`, `total_registros`, `janelas`)
   didn't change signature or logic, only which values populate the globals
   they already read. **A subtle bug fixed while wiring this up**:
   `janelas(inicio, fim, max_dias: int = MAX_DIAS_FILTRO)` used to have the
   limit as a parameter default — evaluated once at function-definition
   time, so it would have permanently stuck at 31 regardless of what
   `aplicar_regras()` did later, since Python doesn't re-evaluate defaults on
   each call. Fixed to `max_dias: int | None = None` with the global read
   inside the function body. If you add code that needs one of these
   "regras-substitutable" globals, read it inside the function body — never
   as a parameter default — or you'll reintroduce the same bug.
   `regras.validar_bundle()` runs before any bundle is ever cached or
   applied; an invalid bundle from the server is logged and discarded, never
   adopted (`teste_regras.py`, `teste_bundle_invalido_nao_substitui_o_bom`).
5. Per-run reporting, at the very end of `main()`, after the real download
   work is done: `processar_empresa()` returns `(resumo, metricas)` — the
   granular `metricas` list (one row per `cliente`/`tipo`/`competência`) is
   accumulated across companies and sent via
   `api_client.enviar_relatorio_execucao()` (upsert clientes → open execução
   → send metrics → finalize), which **never raises** — a failed POST here
   can't invalidate work that's already on disk. Failures write to
   `_pendencias/`, retried at the start of the *next* run
   (`api_client.reenviar_pendencias`, called right after step 1, before this
   run's own downloads start) and discarded after 30 days.
6. `TipoNota`/`StatusExecucao` travel over the wire as **plain integers**,
   not strings — `ContabOne.Api`'s `Program.cs` doesn't register a
   `JsonStringEnumConverter`, so System.Text.Json's default (enum-as-number)
   applies. `api_client.TIPO_NOTA`/`STATUS_EXECUCAO` do this translation.
   Easy to "fix" back to a string thinking it's more readable, without
   noticing the API would then reject it with 400.
7. `certificadoNomeArquivo` sent to `/api/agent/clientes` is **never the
   original `.pfx` filename** — `nfse._nome_arquivo_sanitizado()`
   reconstructs it from just `codigo` + the file suffix. The recommended
   certificate filename pattern
   (`codigoEmpresa_CNPJ_NomeEmpresa_s.SENHA_v.DD.MM.AAAA.pfx`) embeds the
   **full CNPJ and the plaintext password** — sending the raw filename would
   leak both. Found by writing `teste_payload_vazamento.py`, not after; fixed
   before that test was ever run for the first time. If this field ever
   looks "wrong" because it doesn't match the real file on disk, that's the
   point — don't "fix" it back to the original name.
8. `POST /api/agent/clientes` returns a `clientes: [{codigo, id}]` mapping —
   added to `ContabOne.Api/Features/Agent/AgentEndpoints.cs` in the same
   session as this file, alongside the Python side. Without it there'd be no
   way to learn the server-assigned `Cliente.Id` (Guid) that
   `ExecucaoMetrica.ClienteId` is FK-enforced against — metrics reporting
   would be structurally impossible. Small, additive, backward-compatible;
   confirmed against the real API (`ContabOne.Api` + Postgres via
   `docker-compose.yml`) with a real handshake→upsert→metrics round trip,
   verified afterward directly in Postgres.

### Output layout

```
notas/
└── {codigo}_{nome}/
    ├── _controle.json
    └── {ano-mes}/                 ← month of the note's OWN issue date, not the queried period
        ├── Recebidas/notas-{ano-mes}.csv, {chave}.xml, {chave}.pdf
        └── Emitidas/...
```

### DANFSe PDF generation (`danfse.py`)

Renders the DANFSe v2.0 layout with ReportLab from scratch (the portal's own
PDF-generation API was suspended 2026-07-01 per NT 008 item 1, hence
building it locally from the signed XML is the norm-sanctioned path, not a
workaround). Validated field-by-field (30/30) against a real portal-issued
DANFSe. Layout constants (margins, line weights, shading, font sizes, QR
position) are pulled directly from NT 008 §2.2–2.4.5 — if you touch layout
code, check the section reference in the nearby comment against the actual
Nota Técnica before changing a number. Uses Arial/Microsoft Sans Serif from
`C:/Windows/Fonts` when available (required by the NT), falling back to
Helvetica off-Windows. **Never overwrites an existing PDF**, including ones
downloaded straight from the portal — `gerar_pdf()` in `nfse.py` checks
existence before calling into `danfse.py`.

### Packaging (`build.py`)

Builds outside the project directory (`%TEMP%\build-nfse`) because
PyInstaller's temp-file churn triggers `PermissionError` when the project
lives inside a OneDrive-synced folder (it does here). `logo_nfse.png` and
`municipios_ibge.json` are embedded as PyInstaller data files and read back
via `sys._MEIPASS` at runtime (see `_pasta_recursos()` in `danfse.py`);
`danfse` is a `--hidden-import` since `nfse.py` imports it dynamically inside
`gerar_pdf()` rather than at module load time. `api_client`/`regras` get a
`--hidden-import` too even though they're top-level imports PyInstaller
would find on its own — cheap, explicit belt-and-suspenders, matching the
existing style. `build.py` reads `VERSAO_AGENTE` out of `api_client.py` by
regex (`_versao_agente()`), deliberately **not** by importing the module —
`api_client.py` imports `requests`/`urllib3` at its top, a dependency
`build.py` itself never needed before and shouldn't gain just to print a
version string during packaging. `dist/` is a build artifact — don't
hand-edit it or treat its contents as source. The compiled `.exe` was
smoke-tested against a fake `/api/agent/handshake` returning
`podeExecutar: false` on 01/08/2026 and behaved identically to the raw
`.py` (exit code 3, message from the server, `.pfx` untouched) — see
[HANDOFF.md](HANDOFF.md) for the manual steps if you need to repeat that;
it isn't part of `testes/executar_tudo.py` since it requires a build first.

## Sensitive local data — do not commit or exfiltrate

`certificados/*.pfx` and everything under `notas/` (client names, CNPJs,
invoice contents, `_controle.json`) are real production data for real
accounting clients, including cert files whose names may embed the PFX
password. Never print full certificate filenames or `.pfx` contents back
verbatim in ways that could leak the embedded password, and never suggest
committing `certificados/` or `notas/` anywhere.

Since the agent integration, also treat as sensitive: `config.toml`'s
`chave` (the agent's API key — a bearer credential, functionally equivalent
to a password for everything under `/api/agent/*`) and `_agente_cache.json`
(contains the same escritório info the handshake returned, signed but not
encrypted). Neither is as sensitive as a `.pfx`+password, but neither
belongs in a commit, a shared log, or pasted back verbatim either. The
`_pendencias/*.json` and `_regras_cache.json` files are lower-stakes
(aggregate counts, portal URLs/regexes) but still local operational data,
not something to casually share.
