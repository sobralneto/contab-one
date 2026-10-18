## 1. Banco: extensão unaccent

- [x] 1.1 Declarar `modelBuilder.HasPostgresExtension("unaccent")` em `Infra/AppDbContext.cs`
- [x] 1.2 Gerar a migration com `dotnet ef migrations add HabilitaUnaccent --project ContabOne.Api` e conferir que ela só cria a extensão (sem tocar o snapshot à mão)

## 2. API: busca de clientes sem caixa e sem acento

- [x] 2.1 Criar em `ClientesEndpoints.cs` o helper de escape de `LIKE` (`\`, `%`, `_`) e o montador do padrão `%termo%` a partir do termo aparado
- [x] 2.2 Trocar, em `AplicarFiltros`, os `Contains(busca)` de `Nome`, `Codigo` e `CnpjMascarado` por `EF.Functions.ILike(EF.Functions.Unaccent(coluna), EF.Functions.Unaccent(padrao))`, mantendo a busca pelos dígitos do CNPJ completo como está
- [x] 2.3 Adicionar em `TraducaoLinqTest.cs` o caso que prova, via `ToQueryString()`, que o predicado novo traduz para SQL (com `ILIKE` e `unaccent`)
- [x] 2.4 Adicionar em `ClientesTest.cs` os cenários da spec: minúsculas × maiúsculas, caixa mista, sem acento × acentuado, termo no meio, espaços nas pontas, `%` literal, código com caixa diferente
- [x] 2.5 Adicionar em `ClientesTest.cs` o cenário de exportação CSV com o mesmo termo e o de isolamento (cliente homônimo em outro escritório não aparece)

## 3. API: clientes com apuração do PGDAS-D

- [x] 3.1 Mapear `GET /clientes` em `PgdasEndpoints.cs` devolvendo `id`, `codigo`, `nome` dos clientes do escritório com ao menos uma apuração, ordenados por nome, com o guarda `EscopoOuNull` → 403
- [x] 3.2 Adicionar em `PgdasTest.cs`: lista sem repetição e ordenada, cliente sem apuração fora, isolamento entre escritórios e 403 sem escritório na sessão

## 4. Frontend: select de cliente na visão geral do PGDAS-D

- [x] 4.1 Adicionar `listarClientesPgdas()` em `api/endpoints/pgdas.ts` e o DTO correspondente em `api/types.ts`
- [x] 4.2 Em `PgdasVisaoGeralView.vue`, trocar o `<input>` "Buscar por cliente" por um `<select>` com "Todos os clientes" (valor `null`) e as opções "código — nome", com rótulo acessível
- [x] 4.3 Carregar as opções no `onMounted` em paralelo com lista e resumo; ao mudar o select, chamar `carregar()` passando `clienteId` para `listarTodas` junto das competências
- [x] 4.4 Remover o filtro por termo em memória do `computed` `clientesAgrupados`
- [x] 4.5 Estilizar o select no mesmo bloco `.view-toolbar` dos inputs, só com tokens (conferir o design system em `ContabOne.Frontend/.claude/contab-one-design-system-claude.md`)
- [x] 4.6 Atualizar `PgdasVisaoGeralView.spec.ts` (MSW): select lista as opções do endpoint, padrão "Todos", escolher cliente refaz a chamada com `clienteId`, combinação com competência, voltar para "Todos"

## 5. Verificação

- [x] 5.1 Rodar `npm --prefix ContabOne.Frontend run build` (typecheck)
- [x] 5.2 Rodar `npm test` na raiz e confirmar verde nas suítes afetadas (API com `Category=Banco`, Vitest)
- [x] 5.3 Conferir na tela: `/clientes` buscando "silva"/"joao" em minúsculas e `/f/pgdas` filtrando por um cliente escolhido no select
