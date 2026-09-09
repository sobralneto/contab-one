## 1. Backend — modelo de dados

- [x] 1.1 Adicionar `Tem2FA` (bool, não-nulo, default `false`) a `Cliente` em
      `ContabOne.Api/Domain/Entities.cs`
- [x] 1.2 Remover `TemDoisFatores` de `TarefaOnboarding` em
      `ContabOne.Api/Domain/Entities.cs`
- [x] 1.3 Gerar uma única migration EF Core cobrindo as duas mudanças
      (`dotnet ef migrations add Cliente2FA --project ContabOne.Api`) e
      conferir o `Up`/`Down` gerado

## 2. Backend — cadastro, edição, busca e filtro de cliente

- [x] 2.1 Adicionar `Tem2FA` a `ClienteDto` e `ClienteRequest` em
      `ContabOne.Api/Features/Clientes/ClientesEndpoints.cs`
- [x] 2.2 Mapear `Tem2FA` em `CriarAsync` e `AtualizarAsync`
- [x] 2.3 Adicionar parâmetro de query opcional `tem2FA` (bool?) a
      `ListarAsync` e aplicar o predicado quando informado
- [x] 2.4 Atualizar `ClienteRequestValidator` se necessário (campo é bool com
      default, não deve exigir preenchimento explícito)

## 3. Backend — remoção da flag de tarefa de onboarding

- [x] 3.1 Remover leitura/escrita de `TemDoisFatores` em
      `DuplicarModeloAsync`, `ObterGruposDoModeloAsync`, `CriarTarefaAsync`,
      `AtualizarTarefaAsync` e nas projeções do checklist, em
      `ContabOne.Api/Features/Onboarding/OnboardingEndpoints.cs`
- [x] 3.2 Remover `TemDoisFatores` de `TarefaDto`, `TarefaBaseDto`,
      `TarefaChecklistDto` e `TarefaRequest`
- [x] 3.3 Atualizar `Nfse.Agent/testes/_fake_api.py` se ele espelhar algum
      desses contratos (conferir se referencia `temDoisFatores`)

## 4. Frontend — tipos e API client

- [x] 4.1 Adicionar `tem2FA` a `ClienteDto` e `ClienteRequest` em
      `ContabOne.Frontend/src/api/types.ts`
- [x] 4.2 Adicionar parâmetro `tem2FA` a `listarClientes` em
      `ContabOne.Frontend/src/api/endpoints/clientes.ts`
- [x] 4.3 Remover `temDoisFatores` de `TarefaOnboardingDto`,
      `TarefaOnboardingRequest` e `TarefaChecklistOnboardingDto` em
      `ContabOne.Frontend/src/api/types.ts`

## 5. Frontend — cadastro, busca e filtro de cliente

- [x] 5.1 Adicionar campo de 2FA ao formulário de cadastro/edição em
      `ContabOne.Frontend/src/views/ClientesView.vue` (`form` e payload de
      salvar)
- [x] 5.2 Adicionar coluna "2FA" (Sim/Não) à tabela de listagem
- [x] 5.3 Adicionar filtro de 2FA (Todos/Sim/Não) à barra de filtros, incluído
      em `aplicarFiltros()` e resetando a paginação para a primeira página

## 6. Frontend — remoção da flag de tarefa de onboarding

- [x] 6.1 Remover coluna "2FA", badge e checkbox de
      `ContabOne.Frontend/src/views/onboarding/OnboardingModeloDetalheView.vue`
      (tabela, modal de tarefa, `formTarefa`, CSS `.badge-2fa`)
- [x] 6.2 Remover badge de 2FA por tarefa de
      `ContabOne.Frontend/src/views/onboarding/OnboardingClienteView.vue`
      (marcação na tarefa e CSS `.badge-2fa`)
- [x] 6.3 Remover badge de 2FA de
      `ContabOne.Frontend/src/features/onboarding/exportacao/documento.ts`
      (`tarefaHtml()` e CSS `.exp-badge-2fa`)

## 7. Frontend — aviso de 2FA na tela de onboarding do cliente

- [x] 7.1 Em `OnboardingClienteView.vue`, exibir o aviso "Cliente possui 2FA
      habilitado para acesso ao site do GOV.br" acima do primeiro grupo de
      tarefas, condicionado a `cliente.tem2FA`
- [x] 7.2 Garantir que o aviso aparece mesmo quando o cliente ainda não tem
      checklist criado

## 8. Testes

- [x] 8.1 Atualizar `ContabOne.Api/tests/OnboardingTest.cs` removendo os
      literais `temDoisFatores`
- [x] 8.2 Adicionar/atualizar testes de `ClientesEndpoints` (xUnit) cobrindo
      criação, edição, listagem e filtro por `Tem2FA`
- [x] 8.3 Atualizar `ContabOne.Frontend/src/views/ClientesView.spec.ts` com o
      novo campo, coluna e filtro
- [x] 8.4 Atualizar
      `ContabOne.Frontend/src/views/onboarding/OnboardingClienteView.spec.ts`
      removendo fixtures/expectativas de `temDoisFatores` e cobrindo o novo
      aviso de 2FA
- [x] 8.5 Atualizar
      `ContabOne.Frontend/src/features/onboarding/exportacao/documento.spec.ts`
      removendo a cobertura do badge de 2FA no PDF

## 9. Fechamento

- [x] 9.1 Rodar `npm test` a partir da raiz e revisar o que foi afetado
- [ ] 9.2 Rodar `npm run test:tudo` antes de abrir o PR
- [x] 9.3 Rodar `npm --prefix ContabOne.Frontend run build` (typecheck) após
      as mudanças de frontend
