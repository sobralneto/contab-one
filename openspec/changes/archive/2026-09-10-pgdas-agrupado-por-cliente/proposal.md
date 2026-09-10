## Why

A visão geral do PGDAS-D lista uma linha por apuração (cliente + competência), o que com dezenas de clientes vira uma tabela longa e difícil de varrer — o usuário quer ver, de relance, quais clientes têm apuração e qual a competência mais recente de cada um. Agrupar a lista por cliente e concentrar o histórico de competências numa sidebar deixa a lista compacta e o detalhe a um clique, sem remover a ação "Ver dashboard" que já existe.

## What Changes

- A tabela da visão geral (`PgdasVisaoGeralView.vue`) passa a exibir **uma linha por cliente**: nome do cliente e última competência importada, ordenada pela competência mais recente (mais nova primeiro).
- Cada linha ganha um ícone que abre uma **sidebar à direita** com a identificação do cliente (código, nome e CNPJ mascarado) e, abaixo, uma tabela das competências do cliente com seus respectivos valores (faturamento, DAS, vencimento, status pago/aberto, pendências).
- O ícone "Ver dashboard" **continua na tabela principal** (coluna de ações), comportamento inalterado.
- `GET /api/pgdas/apuracoes` passa a devolver também `clienteCodigo` e `clienteCnpjMascarado` na projeção de cada apuração (dados que o front precisa para a sidebar e que hoje só chegam via `identificarClientePgdas`).

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `apuracao-simples-nacional`: a listagem de apurações da visão geral passa a ser agrupada por cliente — uma linha por cliente com a última competência, com o histórico de competências exibido numa sidebar — e a resposta da listagem carrega a identidade do cliente (código e CNPJ mascarado).

## Impact

- **Frontend**: `ContabOne.Frontend/src/views/pgdas/PgdasVisaoGeralView.vue` (reestruturação da tabela + sidebar) e seu spec de teste `PgdasImportacaoView.spec.ts` vizinho (novo teste da visão geral); `src/api/types.ts` (`ApuracaoListaDto`).
- **API**: `ContabOne.Api/Features/Pgdas/PgdasEndpoints.cs` — projeção de `ListarApuracoesAsync` ganha dois campos (`ClienteCodigo = a.Cliente.Codigo`, `ClienteCnpjMascarado = a.Cliente.CnpjMascarado`); nenhum dado sensível novo (CNPJ só mascarado, como já é em `Cliente.CnpjMascarado`).
- **Testes**: `PgdasTest.cs` (assert do novo campo), Vitest da view de visão geral.