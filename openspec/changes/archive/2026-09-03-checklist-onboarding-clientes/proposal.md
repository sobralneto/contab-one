## Why

A entrada de um cliente novo no escritório passa por uma sequência longa de
procurações, portais governamentais, cadastros em sistemas internos e
apresentações — hoje controlada fora da plataforma, em planilha ou no projeto
avulso `checklistonboardingclientes`, sem vínculo com o cadastro de clientes que
o Contab One já mantém. Quem assume um cliente no meio do caminho não sabe o que
falta, e nada indica quem é o responsável por cada etapa.

O Contab One já é o lugar onde o cliente existe, onde os usuários do escritório
existem e onde o isolamento por escritório é resolvido. Trazer o checklist para
cá elimina a planilha paralela e dá ao onboarding o mesmo escopo multi-tenant do
resto do produto.

## What Changes

- **Modelo de onboarding por escritório (CRUD).** Grupos de tarefas com nome,
  título, descrição e ordenação, cada um com suas tarefas (1:N). Cada tarefa tem
  nome, responsáveis (N usuários do escritório), link da página do portal/sistema,
  flag de site com 2FA e ordenação. Definido uma vez por escritório e reaproveitado
  por todo cliente. Restrito a `EscritorioAdmin`.
- **Checklist por cliente, criado por ação explícita.** Um cliente novo NÃO nasce
  com checklist — o usuário decide, cliente a cliente, quando adicionar um,
  acionando a ação na listagem de clientes. A partir daí o checklist guarda, por
  tarefa do modelo, o status (aberto/concluído), a observação e quando/por quem foi
  concluída, além do percentual de conclusão persistido no próprio checklist.
  Operado por `EscritorioUsuario`.
- **Página de onboarding do cliente**, com a mesma estrutura da referência —
  círculo de percentual no topo, barra de progresso com marcadas/faltantes antes do
  primeiro grupo, grupos em blocos e tarefa com checkbox que risca o título quando
  concluída — desenhada com os tokens e classes de `components.css`, não com o CSS
  do projeto de referência. Sem exportação em PDF.
- **Botão na coluna de ações da listagem de clientes**, com dois estados: cliente
  sem checklist mostra "Adicionar checklist"; cliente com checklist mostra o acesso
  direto à página dele.
- **Rotas transversais** `/clientes/:clienteId/onboarding` e `/onboarding/modelos`,
  fora da família `/f/:produto` — o checklist não é particionado por ferramenta,
  como já acontece com `/clientes` e `/agentes`. Sem produto novo no catálogo e sem
  gate comercial.
- Endpoints novos sob `/api/onboarding`, seguindo o padrão de fatia vertical
  (`Features/Onboarding/OnboardingEndpoints.cs`).
- Nenhum conteúdo fiscal novo trafega: o checklist guarda status e texto de
  observação escrito pelo próprio usuário, nada derivado de documento do cliente.

## Capabilities

### New Capabilities

- `checklist-onboarding`: modelo de grupos e tarefas de onboarding por escritório,
  checklist por cliente derivado desse modelo, percentual de conclusão, atribuição
  de responsáveis e a página que apresenta tudo isso.

### Modified Capabilities

- `gestao-clientes`: a listagem de clientes passa a oferecer, na coluna de ações,
  o acesso ao checklist de onboarding daquele cliente.

## Impact

**API (`ContabOne.Api/`)**
- `Domain/Entities.cs`: entidades novas `GrupoTarefaOnboarding`,
  `TarefaOnboarding`, `TarefaOnboardingResponsavel`, `ChecklistOnboardingCliente`,
  `ItemChecklistOnboarding`.
- `Domain/Enums.cs`: `StatusTarefaOnboarding` (Aberto, Concluido) — membro
  acrescentado ao fim de qualquer enum existente, nunca reordenado.
- `Infra/AppDbContext.cs`: `DbSet`s, filtros globais de tenant para cada entidade
  nova e a configuração de índices/relacionamentos.
- `Features/Onboarding/OnboardingEndpoints.cs` + grupo `/api/onboarding` em
  `Program.cs`, com as políticas `EscritorioAdmin` (modelo) e `EscritorioUsuario`
  (checklist), incluindo a criação explícita do checklist do cliente.
- `Features/Clientes/ClientesEndpoints.cs`: a listagem passa a expor se o cliente já
  tem checklist de onboarding, para a coluna de ações escolher entre "Adicionar" e
  "Abrir".
- Migration EF nova.

**Frontend (`ContabOne.Frontend/`)**
- `views/onboarding/OnboardingClienteView.vue` e
  `views/onboarding/OnboardingModelosView.vue`.
- `views/ClientesView.vue`: botão novo em `.col-actions`.
- `router/index.ts`: duas rotas transversais novas.
- `api/types.ts` e o cliente de API correspondente.
- Menu lateral: as duas telas não vêm do catálogo (`GET /api/produtos`), então o
  acesso é pela linha do cliente e por um item transversal, como `/clientes`.

**Testes**
- `IsolamentoTest.cs` e `TraducaoLinqTest.cs` cobrindo as entidades novas.
- Vitest para o cálculo de percentual e a marcação/desmarcação.
- Playwright para o caminho listagem de clientes → checklist → marcar tarefa.

**Fora de escopo**
- Exportação em PDF do checklist (existe na referência; não pedida aqui).
- Qualquer participação de agente Python — o onboarding é só painel.
