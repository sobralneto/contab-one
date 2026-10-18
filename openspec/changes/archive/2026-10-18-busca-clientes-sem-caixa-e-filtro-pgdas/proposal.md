## Why

Dois atritos de busca por cliente que o escritório sente todo dia. Na tela de
clientes (`/clientes`), a busca por nome só encontra o cliente quando o termo é
digitado exatamente como foi gravado — na prática, em maiúsculas: o
`Contains` do EF vira um `LIKE`/`strpos` sensível a caixa no PostgreSQL, então
"silva" não acha "SILVA COMERCIO LTDA". O usuário espera o comportamento de um
`LIKE '%termo%'` do SQL Server (collation padrão, sem distinção de caixa). Na
visão geral do PGDAS-D (`/f/pgdas`), o filtro "Cliente" é um campo de texto
livre que só filtra o que já foi carregado em memória — o usuário precisa
lembrar como o nome está escrito, e quando a lista vem truncada (mais de 1000
apurações) o cliente procurado pode simplesmente não estar entre as linhas
carregadas.

## What Changes

- A busca por texto de `GET /api/clientes` (e, por compartilhar o mesmo
  predicado, de `GET /api/clientes/exportar`) passa a casar **sem distinção de
  maiúsculas/minúsculas e sem distinção de acentos**, por "contém" — "joao",
  "JOAO" e "João" acham "JOÃO DA SILVA ME". Vale para nome, código e CNPJ
  mascarado; a busca pelos dígitos do CNPJ completo continua como está.
- Os caracteres `%` e `_` digitados continuam sendo literais (como hoje com o
  `Contains`), não curingas.
- O banco ganha a extensão `unaccent` do PostgreSQL, criada por migration.
- Na visão geral do PGDAS-D, o campo de texto "Buscar por cliente" é
  substituído por um **select** com os clientes do escritório que têm ao menos
  uma apuração gravada, mais a opção "Todos os clientes" (padrão).
- Escolher um cliente no select refaz a listagem **no servidor** com
  `clienteId`, combinando com os filtros de competência — deixa de ser um
  filtro em memória e passa a funcionar mesmo quando a lista geral é truncada.
- Novo endpoint `GET /api/pgdas/clientes`, que devolve `id`, `codigo` e `nome`
  dos clientes com apuração, ordenados por nome, escopado ao escritório da
  sessão.

## Capabilities

### New Capabilities

_(nenhuma)_

### Modified Capabilities

- `gestao-clientes`: a busca por texto da listagem passa a ser insensível a
  maiúsculas/minúsculas e a acentos, com semântica de "contém".
- `apuracao-simples-nacional`: a visão geral ganha o filtro de cliente por
  seleção, aplicado no servidor, e a API expõe a lista de clientes com
  apuração para alimentá-lo.

## Impact

- **API**: `Features/Clientes/ClientesEndpoints.cs` (`AplicarFiltros`, usado por
  listagem e exportação); `Features/Pgdas/PgdasEndpoints.cs` (novo
  `GET /clientes`); nova migration habilitando `unaccent`
  (`Infra/AppDbContext.cs` declara a extensão).
- **Frontend**: `views/pgdas/PgdasVisaoGeralView.vue` (select no lugar do
  input, recarga com `clienteId`); `api/endpoints/pgdas.ts` e `api/types.ts`
  (nova chamada e DTO). `ClientesView.vue` não muda — o comportamento é todo
  do servidor.
- **Testes**: `ClientesTest.cs` (caixa e acento na busca), teste do novo
  endpoint PGDAS (incluindo isolamento por escritório), `TraducaoLinqTest.cs`
  (o predicado novo traduz para SQL), `PgdasVisaoGeralView.spec.ts`.
- **Banco/infra**: `unaccent` é um módulo contrib presente na imagem oficial
  do PostgreSQL (Testcontainers `postgres:18-alpine` e Railway); a migration
  usa `CREATE EXTENSION IF NOT EXISTS`.
- Nenhuma mudança de privacidade: nada novo sai da máquina do escritório, e o
  novo endpoint devolve só identificação já exibida na listagem.
