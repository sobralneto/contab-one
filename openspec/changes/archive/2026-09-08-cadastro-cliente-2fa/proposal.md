## Why

O escritório precisa saber, por cliente, se o acesso ao site do GOV.br exige o
segundo fator de autenticação (2FA) — essa é uma informação da empresa, não de
uma tarefa específica do onboarding. Hoje existe uma flag equivalente presa a
cada tarefa de onboarding (`TemDoisFatores`), fruto de um entendimento errado do
pedido original: ela obriga o escritório a marcar 2FA tarefa por tarefa, modelo
por modelo, em vez de registrar uma única vez no cadastro do cliente. Essa flag
antiga deve sair, e o dado deve migrar para onde sempre devia ter estado: o
cadastro do cliente.

## What Changes

- Novo campo booleano `Tem2FA` no cadastro do cliente, indicando se o cliente
  tem 2FA habilitado no site do GOV.br.
- O campo aparece no formulário de cadastro e de edição de cliente.
- A listagem/busca de clientes ganha uma coluna "2FA" com "Sim"/"Não", e um
  filtro para restringir a listagem por esse valor.
- Na tela de onboarding do cliente, um aviso fixo logo acima do primeiro grupo
  de tarefas exibe o texto "Cliente possui 2FA habilitado para acesso ao site
  do GOV.br" quando a flag do cliente estiver marcada (some quando não estiver).
- **BREAKING**: remoção completa da flag `TemDoisFatores` de tarefa de
  onboarding — campo no modelo de tarefa, indicador/badge na tabela de tarefas
  do modelo, badge no checklist do cliente, e a informação correspondente no
  PDF exportado do checklist. Escritórios que hoje marcam tarefas como "exige
  2FA" perdem essa marcação; a informação de 2FA passa a existir apenas em nível
  de cliente.

## Capabilities

### New Capabilities

(nenhuma — o comportamento novo entra como requisito adicional de uma
capability já existente)

### Modified Capabilities

- `gestao-clientes`: cadastro, edição, listagem e filtro de clientes passam a
  incluir a flag de 2FA.
- `checklist-onboarding`: remove a indicação de "segundo fator" por tarefa (no
  modelo, no checklist do cliente e no PDF exportado), e a tela de onboarding
  do cliente passa a exibir o aviso de 2FA do cliente acima do primeiro grupo
  de tarefas.

## Impact

- **Backend** (`ContabOne.Api`): `Domain/Entities.cs` — novo campo `Tem2FA` em
  `Cliente`, remoção de `TemDoisFatores` em `TarefaOnboarding`;
  `Features/Clientes/ClientesEndpoints.cs` — `ClienteDto`, `ClienteRequest`,
  `ClienteRequestValidator` e `ListarAsync` (novo filtro);
  `Features/Onboarding/OnboardingEndpoints.cs` — remoção de todas as leituras e
  escritas de `TemDoisFatores` (criação/edição/duplicação de tarefa, DTOs de
  grupo, checklist e request); duas migrations EF Core (adicionar `Tem2FA` em
  `Clientes`, remover `TemDoisFatores` de `TarefasOnboarding`).
- **Frontend** (`ContabOne.Frontend`): `api/types.ts` e
  `api/endpoints/clientes.ts` — novo campo e parâmetro de filtro;
  `views/ClientesView.vue` — campo no formulário, coluna e filtro na listagem;
  `views/onboarding/OnboardingClienteView.vue` — novo aviso de 2FA do cliente,
  remoção do badge de 2FA da tarefa; `views/onboarding/
  OnboardingModeloDetalheView.vue` — remoção do campo, coluna e badge de 2FA da
  tarefa; `features/onboarding/exportacao/documento.ts` — remoção do badge de
  2FA no PDF exportado.
- **Testes**: `ContabOne.Api/tests/OnboardingTest.cs` (remover literais
  `temDoisFatores`), `ClientesView.spec.ts`,
  `OnboardingClienteView.spec.ts`, `documento.spec.ts` — ajustar fixtures e
  expectativas.
- **OpenSpec**: `openspec/specs/gestao-clientes/spec.md` e
  `openspec/specs/checklist-onboarding/spec.md` recebem os requisitos
  alterados desta change.
