## 1. Modelo de dados

- [x] 1.1 Adicionar `bool Ativo { get; set; } = true` em `Cliente`
  (`ContabOne.Api/Domain/Entities.cs`)
- [x] 1.2 Gerar migration EF Core (`dotnet ef migrations add
  AdicionaAtivoEmCliente --project ContabOne.Api`) e conferir que a coluna
  nasce `NOT NULL DEFAULT true`

## 2. Endpoint de inativar/reativar

- [x] 2.1 Adicionar `PATCH /{id:guid}/situacao` em `MapClientesEndpoints`
  (`ClientesEndpoints.cs`), recebendo `{ ativo: bool }`
- [x] 2.2 Implementar `AtualizarSituacaoAsync`: busca o cliente pelo id
  (escopado pelo filtro global de tenant), 404 se não achar, grava `Ativo` e
  `AtualizadoEm`, devolve `{ id, ativo }`
- [x] 2.3 Incluir `Ativo` no `ClienteDto` (`ListarAsync` e `ObterAsync`)

## 3. Filtro de situação na listagem

- [x] 3.1 Adicionar parâmetro `situacao` (`"ativos" | "inativos" | "todos"`)
  em `ListarAsync`
- [x] 3.2 Sem `situacao` informado (ou valor desconhecido), aplicar
  `Where(c => c.Ativo)` — mesma regra de "endereço antigo mostra a lista, não
  falha" já usada nos demais filtros de token
- [x] 3.3 `"inativos"` aplica `Where(c => !c.Ativo)`; `"todos"` não filtra por
  situação

## 4. Limite de plano e cadastro

- [x] 4.1 Confirmar que a checagem de `plano.MaxClientes` em `CriarAsync`
  conta todos os clientes do escritório, ativos e inativos (comportamento já
  existente — sem mudança de código, só cobrir com teste)

## 5. Indicadores do painel

- [x] 5.1 Em `DashboardEndpoints.cs`, aplicar `Where(c => c.Ativo)` (ou
  equivalente) em `totalClientes`, `clientesEmOnboarding`,
  `certificadosVencendo`, `certificadosVencidos`, `certificadosVencendo3d`,
  `certificadosVencendoMais3d` e na consulta de certificados que alimenta a
  lista detalhada do painel

## 6. Sincronização do agente

- [x] 6.1 Conferir em `AgentEndpoints.cs` que a atualização de cliente
  existente (bloco de sincronização) não toca no campo `Ativo` — mesma lista
  curta de campos que já poupa `RegimeTributario`/`ModeloOnboardingId`
- [x] 6.2 Conferir que o cadastro de cliente novo pela sincronização nasce
  com `Ativo` no valor padrão (`true`), sem atribuição explícita

## 7. Frontend — API client e tipos

- [x] 7.1 Adicionar `ativo: boolean` em `ClienteDto` (tipos do frontend)
- [x] 7.2 Adicionar função `alterarSituacaoCliente(id, ativo)` chamando
  `PATCH /api/clientes/{id}/situacao`

## 8. Frontend — listagem de clientes

- [x] 8.1 Adicionar controle de situação (Ativos / Inativos / Todos) na tela
  de busca de clientes (`ClientesView.vue`), padrão "Ativos" quando nada é
  escolhido
- [x] 8.2 Ler/escrever a escolha de situação na query string, como os demais
  filtros da tela
- [x] 8.3 Voltar à primeira página ao trocar a situação
- [x] 8.4 Na coluna de ações, adicionar botão "Inativar" (cliente ativo) ou
  "Reativar" (cliente inativo), ao lado de editar e excluir
- [x] 8.5 Confirmar visualmente (ex.: diálogo de confirmação, mesmo padrão do
  de exclusão) antes de inativar; reativar pode ser direto

## 9. Testes

- [x] 9.1 xUnit: `ClientesEndpointsTest` — inativar, reativar, cliente novo
  nasce ativo, listagem sem filtro mostra só ativos, filtro "inativos",
  filtro "todos", combinação com busca, token de situação desconhecido cai no
  padrão
- [x] 9.2 xUnit: `DashboardEndpointsTest` — indicadores não contam cliente
  inativo
- [x] 9.3 xUnit: teste do agente confirmando que a sincronização preserva
  `Ativo` de cliente existente e não define nada além do padrão em cliente
  novo
- [x] 9.4 Vitest: `ClientesView` — ação de inativar/reativar aparece
  corretamente por linha, controle de situação filtra e persiste na URL
- [x] 9.5 Rodar `npm test` (suíte afetada) e, antes de arquivar a change,
  `npm run test:tudo`
