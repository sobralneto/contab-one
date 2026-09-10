## 1. API — identidade do cliente na listagem

- [x] 1.1 Estender a projeção de `ListarApuracoesAsync` em `ContabOne.Api/Features/Pgdas/PgdasEndpoints.cs` com `ClienteCodigo = a.Cliente.Codigo` e `ClienteCnpjMascarado = a.Cliente.CnpjMascarado`
- [x] 1.2 Atualizar `ApuracaoListaDto` em `ContabOne.Frontend/src/api/types.ts` com os campos `clienteCodigo` e `clienteCnpjMascarado`
- [x] 1.3 Atualizar/estender `ContabOne.Api/tests/PgdasTest.cs` com assert de que a listagem expõe o código e o CNPJ mascarado do cliente (e não o CNPJ inteiro)

## 2. Frontend — visão geral agrupada por cliente

- [x] 2.1 Refazer a tabela de `PgdasVisaoGeralView.vue`: agrupar por `clienteId` num `computed` (uma linha por cliente, nome + última competência importada, ordenada da mais recente para a mais antiga), mantendo os filtros de busca e competências
- [x] 2.2 Adicionar laço de paginação em `carregar()` (incrementa `pagina` enquanto acumulado < `total`, teto de 10 páginas, aviso de amostra truncada acima do teto)
- [x] 2.3 Manter o ícone "Ver dashboard" (`ChartColumn`) na coluna de ações da tabela agrupada, apontando para `/f/pgdas/dashboard/{clienteId}`

## 3. Frontend — sidebar de detalhe do cliente

- [x] 3.1 Adicionar o ícone de detalhe (`PanelRight`) na coluna de ações, que abre a sidebar à direita
- [x] 3.2 Implementar a sidebar: cabeçalho com código, nome e CNPJ mascarado do cliente; abaixo, tabela das competências dele (competência, faturamento, DAS, vencimento, pago/aberto, pendências), carregada por demanda com `listarApuracoes({ clienteId })` e mesmo laço de paginação
- [x] 3.3 Estilizar com tokens do design system (`tokens.css`/`components.css`) e acessibilidade: `aria-label`, foco ao abrir/fechar, `Esc` fecha

## 4. Testes e verificação

- [x] 4.1 Criar `PgdasVisaoGeralView.spec.ts` (Vitest): agrupamento por cliente (uma linha por cliente com a última competência), abertura/fechamento da sidebar com código/nome/CNPJ mascarado, ícone "Ver dashboard" preservado
- [x] 4.2 Rodar `npm test` (runner seletivo) e corrigir o que falhar