## Why

A dashboard do PGDAS-D (`/f/pgdas/dashboard`) já sabe se pintar com três
identidades visuais — as duas dos escritórios que originaram a ferramenta (L&J,
paleta vinho/dourada; MUDAHR, paleta roxa) e a neutra da plataforma —, mas
**nada no sistema grava qual delas vale para cada escritório**. O leitor existe
(`PgdasDashboardView.vue` lê a chave `marca` de `ConfiguracaoEscritorio`), o
escritor nunca foi construído: não há tela, endpoint nem seed que escreva essa
chave. Na prática todo escritório cai no fallback neutro, e as duas paletas de
marca são código morto.

Falta o outro lado: o admin da plataforma precisa de um campo, no cadastro do
escritório, que escolha o leiaute com que a dashboard daquele escritório será
entregue ao cliente final.

## What Changes

- **Novo campo `LayoutDashboard` no escritório**, com três valores:
  `contabone` (cores atuais do sistema), `lj` (paleta L&J) e `mudahr` (paleta
  MUDAHR). Persistido como coluna de `Escritorio`, não como configuração de
  ferramenta.
- **O campo aparece no CRUD de escritórios** (`/admin/escritorios`), nos modais
  de criação e edição. Como esse CRUD já vive inteiro sob a política
  `PlatformAdmin` (`Program.cs`, grupo `/api/admin`), a restrição "somente
  admin" é atendida pela colocação — o campo não entra em nenhuma tela de
  escritório nem em `ConfiguracaoView`.
- **Criação já vem preenchida com `contabone`**, e escritório existente sem
  valor é lido como `contabone` — a coluna nasce `NOT NULL DEFAULT 'contabone'`,
  de modo que o backfill da migration é o próprio default.
- **A dashboard passa a ler o leiaute do escritório**, não mais da chave `marca`
  de `ConfiguracaoEscritorio`. O valor viaja no próprio payload da dashboard
  (`GET /api/pgdas/clientes/{id}/dashboard`), eliminando a segunda requisição a
  `/api/configuracao` que a view faz hoje só para descobrir a marca.
- **O logotipo acompanha o leiaute**: escolher `lj` ou `mudahr` estampa também
  o logo daquela marca no cabeçalho do documento, como `temas.ts` já faz. Os
  três leiautes ficam sendo, portanto, identidades completas — decisão
  registrada em `design.md`, com a consequência operacional de que esses dois
  valores só devem ser atribuídos aos escritórios donos das marcas.
- **Sem mudança nas paletas**: `temas.ts` já traz as três, portadas verbatim de
  `conversor_dashboard_simples_v2.html`. Esta change não mexe em cor nenhuma.

Não há **BREAKING**: a chave `marca` de `ConfiguracaoEscritorio` nunca foi
gravada, então trocar a fonte de leitura não altera o comportamento de nenhum
escritório em produção — todos continuam em `contabone` até que o admin escolha
outro.

## Capabilities

### New Capabilities

Nenhuma. O comportamento novo cabe inteiro em duas capacidades existentes.

### Modified Capabilities

- `gestao-escritorios`: o CRUD de escritórios ganha o campo de leiaute da
  dashboard — visível apenas para o admin da plataforma, com valor padrão na
  criação e persistido junto com nome, CNPJ, plano e status.
- `apuracao-simples-nacional`: o requisito "A identidade visual da dashboard vem
  do escritório" passa a ter fonte definida — o leiaute escolhido no cadastro do
  escritório —, com três identidades nomeadas e a neutra como padrão de quem
  nunca escolheu, em vez de "identidade configurada para a ferramenta".

## Impact

**API (`ContabOne.Api`)**
- `Domain/Entities.cs` — `Escritorio.LayoutDashboard`.
- `Domain/Enums.cs` — enum `LayoutDashboard` (atravessa a fronteira como
  string, não inteiro; ver `design.md`).
- Migration nova + `AppDbContextModelSnapshot.cs` (gerado, nunca editado à mão).
- `Features/Admin/AdminEndpoints.cs` — `ObterEscritorioAsync`,
  `ListarEscritoriosAsync`, `CriarEscritorioAsync`, `AtualizarEscritorioAsync`,
  os DTOs `CriarEscritorioRequest`/`AtualizarEscritorioRequest` e seus
  validators.
- `Features/Pgdas/PgdasEndpoints.cs` — o payload da dashboard passa a carregar
  o leiaute do escritório.

**Frontend (`ContabOne.Frontend`)**
- `src/api/types.ts` — `EscritorioDto`, `CriarEscritorioRequest`,
  `AtualizarEscritorioRequest` e o payload da dashboard.
- `src/views/admin/EscritoriosView.vue` — campo no formulário, default na
  criação, coluna opcional na tabela.
- `src/views/pgdas/PgdasDashboardView.vue` — passa a tirar o tema do payload;
  some a chamada a `obterConfiguracao('pgdas')`.
- `src/features/pgdas/dashboard/temas.ts` — só o comentário e a assinatura de
  `temaPorCodigo`, que deixa de referenciar a chave `marca`. As paletas ficam
  intactas.

**Testes**
- `ContabOne.Api.Tests` — criação com default, edição do leiaute, valor inválido
  recusado, payload da dashboard trazendo o leiaute do escritório certo.
- Vitest — o campo aparece no modal, criação nasce em `contabone`, a dashboard
  monta com o tema vindo do payload.
- E2E — o admin escolhe um leiaute e ele persiste na reabertura do modal.

**Fora de escopo**
- Cadastrar identidades novas (upload de logo, paleta customizada): os três
  leiautes são fixos em código.
- Aplicar o leiaute a qualquer outra tela — ele governa só o documento da
  dashboard de apuração.
