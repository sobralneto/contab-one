## 1. Modelo de dados (API)

- [x] 1.1 Acrescentar em `Domain/Enums.cs` os enums `RecorrenciaTarefa` (Nenhuma, Diaria, Semanal, Mensal, Anual) e `StatusTarefa` (Aberta, Concluida), ambos ao fim do arquivo, sem reordenar nenhum enum existente
- [x] 1.2 Acrescentar em `Domain/Entities.cs` a entidade `Tarefa` (Id, EscritorioId, Titulo, Observacao?, Vencimento `DateOnly?`, Recorrencia, Status, ClienteId?, TarefaOrigemId?, CriadoPorUsuarioId, CriadoEm, AtualizadoEm, ConcluidaEm?, ConcluidaPorUsuarioId?) com XML doc explicando que a visibilidade dela é mais estreita que o tenant
- [x] 1.3 Acrescentar a entidade de junção `TarefaResponsavel` (TarefaId + UsuarioId, chave composta), no padrão de `UsuarioEscritorio`
- [x] 1.4 Configurar em `Infra/AppDbContext.cs` os `DbSet`s, a chave composta de `TarefaResponsavel`, o delete cascade de `Tarefa`→`TarefaResponsavel`, o `Restrict` nos FKs para `Usuario`, `Cliente` e `TarefaOrigemId`, e índices por `(EscritorioId, Status, Vencimento)` e por `TarefaResponsavel.UsuarioId`
- [x] 1.5 Adicionar o filtro global de tenant para `Tarefa` e `TarefaResponsavel` no mesmo formato das demais entidades (`VeTodosOsEscritorios || x.EscritorioId == ...`); para `TarefaResponsavel`, via a tarefa
- [x] 1.6 Gerar a migration com `dotnet ef migrations add AddTarefas --project ContabOne.Api` e conferir que ela é puramente aditiva

## 2. Regras de domínio (API)

- [x] 2.1 Implementar `ProximoVencimento(DateOnly vencimento, RecorrenciaTarefa recorrencia)` usando `AddDays`/`AddMonths`/`AddYears`, com o vencimento anterior como referência
- [x] 2.2 Escrever os testes de `ProximoVencimento` cobrindo os quatro períodos e os dois casos de borda (31/01 → 28 ou 29/02, e 29/02 → 28/02 do ano seguinte)
- [x] 2.3 Implementar o helper de validação de responsáveis contra `UsuarioEscritorio` do escritório da tarefa, no molde de `OnboardingEndpoints.ValidarResponsaveisAsync`, retornando 400 para id fora do escritório
- [x] 2.4 Implementar o predicado de visibilidade (`responsável OU criador`) como expressão reutilizada por todos os handlers de leitura

## 3. Endpoints (API)

- [x] 3.1 Criar `Features/Tarefas/TarefasEndpoints.cs` com `MapTarefasEndpoints()` e registrar o grupo `/api/tarefas` em `Program.cs` sob a política `EscritorioUsuario`, junto dos demais grupos
- [x] 3.2 `GET /api/tarefas/responsaveis` — usuários ativos do escritório em foco, só id e nome, ordenados por nome; 400 quando a sessão não tem escritório em foco
- [x] 3.3 `GET /api/tarefas` — listagem com filtros `de`/`ate` (`DateOnly`), `status`, `responsavelId`, `clienteId` e paginação, aplicando o predicado de visibilidade e resolvendo "atrasada" na query (nunca como propriedade computada)
- [x] 3.4 `GET /api/tarefas/resumo` — contadores por visão (hoje, próximas, atrasadas, concluídas) para os rótulos da página
- [x] 3.5 `POST /api/tarefas` — validar título obrigatório, ao menos um responsável, vencimento obrigatório quando há recorrência, e limite de tamanho de título e observação
- [x] 3.6 `PUT /api/tarefas/{id}` — mesma validação, restrito a quem enxerga a tarefa
- [x] 3.7 `PATCH /api/tarefas/{id}/status` — concluir grava `ConcluidaEm`/`ConcluidaPorUsuarioId` e, quando há recorrência com vencimento, cria a ocorrência seguinte na mesma transação copiando título, observação, cliente, responsáveis e recorrência, com `TarefaOrigemId` apontando para a concluída; reabrir limpa o registro de conclusão
- [x] 3.8 `DELETE /api/tarefas/{id}` — exclusão física, restrita a quem enxerga a tarefa, sem tocar nas ocorrências anteriores da série
- [x] 3.9 Validar `de <= ate` e a janela máxima do intervalo recebido, e limitar a visão de concluídas à janela de 90 dias com paginação

## 4. Testes de API

- [x] 4.1 Estender `IsolamentoTest.cs` com `Tarefa` e `TarefaResponsavel`
- [x] 4.2 Estender `TraducaoLinqTest.cs` com as consultas de tarefa, provando por `ToQueryString()` que o predicado de "atrasada" e o de visibilidade traduzem
- [x] 4.3 Testes da regra de visibilidade: colega não vê, `EscritorioAdmin` não vê, `PlatformAdmin` sem foco não vê, criador vê o que delegou, e tarefa do escritório B não aparece com A em foco
- [x] 4.4 Testes da conclusão compartilhada: A conclui, B lê como concluída; reabrir limpa o registro
- [x] 4.5 Testes da geração da próxima ocorrência: no prazo, com atraso (avança do vencimento, não de hoje), sem recorrência não gera, e recorrência sem vencimento é recusada na gravação
- [x] 4.6 Testes do endpoint de responsáveis: só ativos, só do escritório em foco, só id e nome, e 400 sem foco

## 5. Camada de API do frontend

- [x] 5.1 Acrescentar em `api/types.ts` os tipos `TarefaDto`, `TarefaRequest`, `ResponsavelTarefaDto`, `ResumoTarefasDto` e os literais de recorrência e status
- [x] 5.2 Criar `api/endpoints/tarefas.ts` com listar, resumo, listar responsáveis, criar, atualizar, alterar status e excluir
- [x] 5.3 Implementar o utilitário de data local do navegador usado para montar `de`/`ate` das visões, com teste Vitest do agrupamento hoje / próximas / atrasadas

## 6. Página de tarefas

- [x] 6.1 Criar `views/TarefasView.vue` com as visões Hoje, Próximas, Atrasadas e Concluídas, contador ao lado do título e a visão "Próximas" quebrada em blocos (Hoje / Amanhã / Esta semana)
- [x] 6.2 Criar `components/tarefas/LinhaTarefa.vue` — checkbox à esquerda, título riscado quando concluída, metadados em pílulas (vencimento, recorrência, cliente, responsáveis) e ações; usar as classes de `components.css`, sem `display:flex` em `<td>`
- [x] 6.3 Criar `components/tarefas/FormularioTarefa.vue` com o seletor de responsáveis alimentado por `GET /api/tarefas/responsaveis` e **pré-selecionado com o usuário logado**, além dos campos opcionais de vencimento, recorrência, observação e cliente
- [x] 6.4 Implementar a criação inline "＋ Adicionar tarefa" no topo de cada visão, sem recarregar a página
- [x] 6.5 Implementar os filtros por responsável e por cliente
- [x] 6.6 Implementar a confirmação de exclusão que avisa, para tarefa recorrente aberta, que a série termina ali
- [x] 6.7 Estado vazio por visão, no padrão de `EstadoVazio.vue`
- [x] 6.8 Registrar a rota transversal `/tarefas` em `router/index.ts` e o item fixo de menu, junto de clientes e agentes — sem catálogo, sem gate comercial

## 7. Hub em três colunas

- [x] 7.1 Criar `components/dashboard/TarefasDoDia.vue` — tarefas abertas do dia e atrasadas, conclusão inline, criação rápida, link para `/tarefas`, estado vazio e tratamento próprio de falha
- [x] 7.2 Reestruturar `views/HubView.vue` para o grid de três colunas (domínios / certificados / tarefas), com as seções de domínio empilhadas verticalmente dentro da coluna 1
- [x] 7.3 Implementar os breakpoints de duas e de uma coluna, preservando a ordem ferramentas → certificados → tarefas
- [x] 7.4 Garantir que a falha de qualquer uma das três cargas não derruba as demais colunas

## 8. Testes de frontend e fechamento

- [x] 8.1 Vitest de `TarefasView` e `FormularioTarefa`: valor padrão do responsável, obrigatoriedade de título e responsável, e vencimento exigido quando há recorrência
- [x] 8.2 Vitest de `TarefasDoDia`: lista do dia, conclusão inline e estado vazio (handlers MSW para todas as chamadas — `onUnhandledRequest: 'error'`)
- [x] 8.3 Playwright: criar tarefa na página → ver no hub → concluir → confirmar que sai da lista do dia
- [x] 8.4 Rodar `dotnet test`, `npm --prefix ContabOne.Frontend test` e `npm --prefix ContabOne.Frontend run build` (o typecheck do repositório) e corrigir o que aparecer
- [x] 8.5 Atualizar `README.md` com a rota `/tarefas`, o grupo `/api/tarefas` e a regra de visibilidade por participação

## 9. Revisão pedida após a primeira entrega

- [x] 9.1 Reordenar o hub para tarefas → ferramentas por domínio → certificados, com a coluna do meio em dobro e os breakpoints preservando a ordem
- [x] 9.2 Esconder a coluna de certificados quando não há certificado a vencer nem falha a comunicar, devolvendo a largura às outras duas
- [x] 9.3 Criar `components/tarefas/NotaRapida.vue` — texto livre, primeira linha vira título e o resto observação, sem vencimento, responsável é quem escreveu (sem seletor)
- [x] 9.4 Acrescentar a visão "Sem prazo" em `TarefasView` (o contador `semPrazo` já existia na API) — sem ela toda nota rápida ficaria inalcançável
- [x] 9.5 Ligar a nota rápida ao cabeçalho da página (indo para "Sem prazo" ao salvar) e ao card do hub (com aviso de onde a nota foi parar)
- [x] 9.6 Vitest da nota rápida (quebra título/observação, uma linha só, usuário sem vínculo) e da visão "Sem prazo"
- [x] 9.7 Atualizar E2E, proposal, design e specs para a nova ordem de colunas e a nota rápida

## 10. Segunda revisão de layout e confirmação de exclusão

- [x] 10.1 Trocar o `window.confirm` da exclusão de tarefa pelo `ConfirmarAcao.vue`, o mesmo modal já usado na listagem de clientes
- [x] 10.2 Manter no modal o aviso de que excluir a ocorrência aberta encerra a série recorrente, agora com a periodicidade escrita por extenso
- [x] 10.3 Reorganizar o hub: grupos de domínio em faixa horizontal no topo; abaixo, três colunas com tarefas, certificados e uma trilha reservada vazia
- [x] 10.4 Remover a lógica de esconder a coluna de certificados (9.2) — o grid agora tem trilha fixa e uma coluna deliberadamente vazia
- [x] 10.5 Vitest da confirmação em modal (cancelar não chama a API, confirmar exclui, aviso da série recorrente) e E2E ajustado à nova estrutura

## 11. Captura sem clique

- [x] 11.1 Remover o botão "Adicionar" da linha de captura da página — Enter é o único caminho de gravação
- [x] 11.2 Tornar a linha inteira clicável (clique em qualquer ponto foca o campo) e marcar `cursor: text`, na página e no card do hub
- [x] 11.3 Manter o foco no campo depois de gravar, com o valor limpo, para capturas em sequência
- [x] 11.4 Acrescentar ao card do hub o botão "Tarefa avançada", abrindo o `FormularioTarefa` completo com clientes carregados sob demanda
- [x] 11.5 Atualizar Vitest (Enter grava, sem botão, foco preservado; formulário avançado abre com os campos que a linha não cobre) e o E2E

## 12. Correção: Enter não gravava sem responsável possível

- [x] 12.1 Remover o desvio silencioso para o formulário completo quando o usuário não pode se atribuir — ele também não gravava, e o Enter parecia quebrado
- [x] 12.2 Introduzir o `impedimento` computado (sem foco / falha de carga / sem vínculo) na página e no card do hub, distinguindo os três casos
- [x] 12.3 Desabilitar a linha de captura e exibir o motivo em vez de aceitar texto que não seria gravado; oferecer nova tentativa quando a causa é falha de carga
- [x] 12.4 Vitest do impedimento (sem foco e sem vínculo) e ajuste dos testes que passaram a casar texto em dois lugares

## 13. Ações de linha iguais nas duas listas

- [x] 13.1 Trocar o botão de texto "Editar" pelo ícone de lápis, o mesmo da coluna de ações de `ClientesView`, ao lado do ícone de excluir
- [x] 13.2 Remover a prop `compacto` de `LinhaTarefa` — ela só existia para esconder as ações no hub, que agora as tem
- [x] 13.3 Extrair `mensagemExclusaoTarefa` para `features/tarefas/mensagens.ts`: o aviso de encerramento da série passou a valer em duas telas e não pode divergir
- [x] 13.4 Ligar editar e excluir no card do hub, reusando `FormularioTarefa` (criação e edição no mesmo componente) e `ConfirmarAcao`
- [x] 13.5 Vitest: editar é ícone sem texto na página, e o card do hub edita, confirma exclusão e repete o aviso da série
