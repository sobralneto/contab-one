## 1. Modelo de dados (API)

- [x] 1.1 Acrescentar `StatusTarefaOnboarding { Aberto, Concluido }` ao fim de `ContabOne.Api/Domain/Enums.cs`, com comentário lembrando que enum é persistido como inteiro e não pode ser reordenado
- [x] 1.2 Criar em `Domain/Entities.cs` as entidades `GrupoTarefaOnboarding` (EscritorioId, Nome, Titulo, Descricao, Ordem, CriadoEm, AtualizadoEm) e `TarefaOnboarding` (GrupoId, Nome, Ordem, Link, TemDoisFatores)
- [x] 1.3 Criar `TarefaOnboardingResponsavel` (TarefaId + UsuarioId, chave composta) e as navegações nas duas pontas
- [x] 1.4 Criar `ChecklistOnboardingCliente` (EscritorioId, ClienteId, PercentualConclusao, AtualizadoEm) e `ItemChecklistOnboarding` (ChecklistId, TarefaId, Status, Observacao, ConcluidoEm, ConcluidoPorId)
- [x] 1.5 Registrar os cinco `DbSet` em `Infra/AppDbContext.cs`
- [x] 1.6 Adicionar os filtros globais de tenant das cinco entidades, no formato canônico `_tenantContext.VeTodosOsEscritorios || x.EscritorioId == _tenantContext.EscritorioId` (filhas filtram pelo pai, como `ApuracaoSegregacao`)
- [x] 1.7 Configurar chaves, FKs e cascatas: grupo→tarefas Cascade, tarefa→responsáveis Cascade, tarefa→itens Cascade, checklist→itens Cascade; índice único `(ClienteId)` em `ChecklistOnboardingCliente` e `(ChecklistId, TarefaId)` em `ItemChecklistOnboarding`
- [x] 1.8 Limitar tamanhos de coluna (Nome, Titulo, Descricao, Link, Observacao) coerentes com o resto de `AppDbContext.cs`
- [x] 1.9 Gerar a migration: `dotnet ef migrations add ChecklistOnboarding --project ContabOne.Api` e conferir que ela é puramente aditiva (cinco tabelas novas, nenhuma coluna alterada)

## 2. Endpoints do modelo de onboarding

- [x] 2.1 Criar `Features/Onboarding/OnboardingEndpoints.cs` com `MapOnboardingEndpoints()` e o helper de escopo `EscopoOuNull(TenantContext)`, no padrão de `PgdasEndpoints.cs`
- [x] 2.2 Registrar `app.MapGroup("/api/onboarding").MapOnboardingEndpoints().RequireAuthorization("EscritorioUsuario")` em `Program.cs`, junto dos demais grupos
- [x] 2.3 `GET /modelo` — grupos do escritório ordenados, com tarefas ordenadas e responsáveis (id + nome) de cada uma
- [x] 2.4 `POST /grupos`, `PUT /grupos/{id}`, `DELETE /grupos/{id}` — exigindo `EscritorioAdmin` (encadeado por endpoint, ver design.md D7); DELETE cascateia nas tarefas e nos itens de checklist
- [x] 2.5 `POST /tarefas`, `PUT /tarefas/{id}`, `DELETE /tarefas/{id}` — exigindo `EscritorioAdmin`; PUT substitui a lista de responsáveis por inteiro
- [x] 2.6 `PUT /grupos/ordem` — reordenação em lote de grupos e tarefas, exigindo `EscritorioAdmin`
- [x] 2.7 Validadores FluentValidation: campos obrigatórios, limites de tamanho, `Link` como URL quando preenchido, e cada `UsuarioId` de responsável com vínculo `UsuarioEscritorio` no escritório dono da tarefa
- [x] 2.8 Garantir que grupo/tarefa de outro escritório resulte em `NotFound` pelo filtro global — nunca em erro que revele a existência da linha
- [x] 2.9 Em `Features/Clientes/ClientesEndpoints.cs`, acrescentar `temChecklistOnboarding` (bool) ao DTO de listagem, resolvido com `Any()` correlacionado a `ChecklistOnboardingCliente` na mesma projeção — sem consulta por linha (D11)

## 3. Endpoints do checklist do cliente

- [x] 3.1 `POST /clientes/{clienteId}` — cria `ChecklistOnboardingCliente` com percentual zero e nenhum item; se o cliente já tem checklist, devolve o existente em vez de criar um segundo (D2)
- [x] 3.2 `GET /clientes/{clienteId}` — devolve `404` quando o cliente não tem checklist criado; quando tem, monta o checklist a partir do modelo vigente, casando cada tarefa com seu `ItemChecklistOnboarding` quando existir (tarefa sem item vale como `Aberto`)
- [x] 3.3 No mesmo GET, reconciliar o percentual: comparar o persistido com o calculado e gravar a diferença quando houver (D5)
- [x] 3.4 `PUT /clientes/{clienteId}/itens/{tarefaId}` — exige checklist já criado (404 se não existir); cria `ItemChecklistOnboarding` sob demanda, grava status + observação, preenche `ConcluidoEm`/`ConcluidoPorId` ao concluir e limpa ao reabrir
- [x] 3.5 Recalcular e persistir `PercentualConclusao` na mesma transação da alternância, sempre no servidor — o percentual nunca vem do corpo do pedido (D3)
- [x] 3.6 Tratar total de tarefas igual a zero como percentual zero, sem divisão por zero
- [x] 3.7 Devolver o percentual recalculado na resposta do PUT, para a tela não precisar de um segundo pedido
- [x] 3.8 Validar que `clienteId` pertence ao escritório da sessão via filtro global (nunca comparando parâmetro de rota com o tenant à mão)

## 4. Frontend — tipos e cliente de API

- [x] 4.1 Declarar em `src/api/types.ts` os DTOs de grupo, tarefa, responsável, checklist e item, com `status` como número espelhando o enum da API; acrescentar `temChecklistOnboarding` ao DTO de cliente da listagem
- [x] 4.2 Criar o módulo de API do onboarding sobre `apiClient`, com as chamadas do modelo, a criação explícita do checklist (`POST /clientes/{clienteId}`) e as demais do checklist
- [x] 4.3 Conferir o `npm --prefix ContabOne.Frontend run build` (único typecheck do repo) depois dos tipos novos

## 5. Frontend — página de onboarding do cliente

- [x] 5.1 Criar `src/views/onboarding/OnboardingClienteView.vue` e a rota `/clientes/:clienteId/onboarding` em `router/index.ts`, no bloco transversal, com `meta.papeis` de EscritorioUsuario para cima e sem `meta.pagina`
- [x] 5.2 Cabeçalho com nome/código do cliente (via novo `GET /api/clientes/{id}` — necessário para renderizar o cabeçalho tanto com quanto sem checklist criado) e o círculo de percentual em SVG (dois `<circle>`, `stroke-dashoffset` proporcional, `var(--accent)` no arco e `var(--border)` na trilha)
- [x] 5.3 Faixa de progresso antes do primeiro grupo: barra em `transform: scaleX()` mais a contagem de marcadas e faltantes
- [x] 5.4 Bloco por grupo, com título, descrição e o contador `concluídas/total` do grupo, usando `.table-card` e os tokens de `components.css` — nada de CSS copiado do projeto de referência
- [x] 5.5 Linha de tarefa com checkbox, título riscado (`line-through` + `var(--text-muted)`) quando concluída, chip dos responsáveis, acesso ao link quando houver e selo de 2FA quando marcado
- [x] 5.6 Campo de observação por tarefa, com debounce de ~550 ms, aplicando a resposta do servidor (que só traz o percentual, não o texto em digitação)
- [x] 5.7 Marcação otimista: alternar checkbox, círculo e barra na hora, reverter e avisar em caso de falha, reconciliando com o percentual devolvido pelo servidor
- [x] 5.8 Estado vazio quando o escritório ainda não montou o modelo — apontando para `/onboarding/modelos` para admin e explicando a quem não pode criá-lo
- [x] 5.9 Tratar o `404` de `GET /clientes/{clienteId}` (checklist ainda não criado — acesso direto por URL) oferecendo a ação de criar o checklist ali mesmo, em vez de tela de erro
- [x] 5.10 Conferir responsividade e o tema escuro (todas as cores por token, nenhuma fixa), e não usar `display:flex` em `<td>`

## 6. Frontend — CRUD do modelo

- [x] 6.1 Criar `src/views/onboarding/OnboardingModelosView.vue` e a rota `/onboarding/modelos`, restrita a `EscritorioAdmin` por `meta.papeis`
- [x] 6.2 Listagem de grupos com suas tarefas, na ordenação definida, e ações de criar/editar/excluir em `.col-actions`
- [x] 6.3 Modal de grupo (nome, título, descrição, ordenação) reusando `.modal-card` e `.modal-actions`
- [x] 6.4 Modal de tarefa (nome, ordenação, link, flag de 2FA) reusando as mesmas classes
- [x] 6.5 `<select multiple>` de responsáveis alimentado por `GET /api/usuarios`, exibindo o nome de cada usuário do escritório em foco
- [x] 6.6 Confirmação via `ConfirmarAcao.vue` antes de excluir grupo ou tarefa, informando quantas tarefas saem junto e que o percentual de todos os clientes muda
- [x] 6.7 Acrescentar o item de menu de `/onboarding/modelos` no bloco transversal do menu lateral (ao lado de Clientes, Agentes e Usuários), visível a `EscritorioAdmin`

## 7. Botão na listagem de clientes

- [x] 7.1 Acrescentar em `views/ClientesView.vue`, dentro de `<td class="col-actions">`, o botão de onboarding ao lado de editar e excluir, seguindo o padrão `.btn-icon` com ícone SVG inline
- [x] 7.2 Estado sem checklist (`!c.temChecklistOnboarding`): ao acionar, chamar `POST /api/onboarding/clientes/{clienteId}` e navegar para `/clientes/:clienteId/onboarding`; `title` "Adicionar checklist de onboarding"
- [x] 7.3 Estado com checklist (`c.temChecklistOnboarding`): ao acionar, apenas navegar para `/clientes/:clienteId/onboarding`, sem chamar o POST; `title` "Ver checklist de onboarding"
- [x] 7.4 Ícone/estilo distinto entre os dois estados (ex.: "+" para adicionar, checklist para abrir), para o usuário reconhecer o estado sem precisar ler o `title`

## 8. Testes

- [x] 8.1 Estender `IsolamentoTest.cs` com as cinco entidades novas, provando que sessão sem escritório resolvido não vê nada e que uma não alcança dados da outra — 2 casos novos (`ModeloDeOnboardingDeEscritorioNaoVazaParaOutro`, `ChecklistOnboardingDeClienteNaoVazaParaOutroEscritorio`). `ContabOne.Api.Tests` estava referenciado em `ContabOne.slnx` num caminho (`ContabOne.Api/tests/...`) que não existe mais — o projeto vive em `ContabOne.Api.Tests/` como irmão de `ContabOne.Api/` (mesmo padrão de `ContabOne.Frontend`); `.slnx` corrigido
- [x] 8.2 Estender `TraducaoLinqTest.cs` com as consultas do modelo e do checklist, provando a tradução por `ToQueryString()` sem banco — 5 casos novos, cobrindo os filtros aninhados (tarefa→grupo, responsável→tarefa→grupo, item→checklist) e a projeção com navegação opcional (`ConcluidoPor`)
- [x] 8.3 Testes de endpoint: percentual sobe ao concluir, desce ao desmarcar, é zero com modelo vazio, e reconcilia depois de excluir tarefa concluída — `OnboardingTest.cs`
- [x] 8.4 Teste de autorização: `EscritorioUsuario` recusado no CRUD do modelo e aceito na marcação do checklist — `OnboardingTest.cs`
- [x] 8.5 Teste de validação de responsável fora do escritório — `OnboardingTest.cs` (mais o caso espelho: responsável do próprio escritório é aceito)
- [x] 8.6 Vitest do cálculo de percentual e da alternância otimista na view do cliente (MSW cobrindo todas as chamadas — `onUnhandledRequest: 'error'`) — `OnboardingClienteView.spec.ts`, 6 casos; achou e corrigiu um bug real (falha ao marcar tarefa substituía a página inteira pelo card de erro, em vez de mostrar um banner mantendo o checklist visível)
- [x] 8.7 Playwright do caminho listagem de clientes → botão de onboarding → marcar tarefa → percentual atualizado — `e2e/onboarding.spec.ts`, rodado contra API+Postgres reais; achou e corrigiu uma suposição errada no teste (percentual esperado como 100% assumindo modelo com 1 tarefa só — o modelo é do escritório, compartilhado e cumulativo entre execuções, D1)
- [x] 8.8 Rodar `dotnet test`, `npm --prefix ContabOne.Frontend test` e `npm --prefix ContabOne.Frontend run build` (nunca `dotnet test` com `DATABASE_URL` no ambiente) — `dotnet test` (`Category!=Banco`: 40/40; suíte completa com Testcontainers: todos verdes, ver nota abaixo); `npm test` (171/171) e `npm run build` (typecheck limpo) passam; suíte Playwright completa passa exceto `pgdas.spec.ts`, que falha também isolado e sem relação com esta change (import de PDF trava esperando o botão "Identificar" — pré-existente). `DetMensagensTest.cs` e 3 métodos em `IsolamentoTest.cs`/`TraducaoLinqTest.cs` desativados temporariamente (`#if false` / exclusão no `.csproj`) porque testam `MensagemDet`, que só existe no branch `det-agent-paridade-nfse` (ainda não mesclado a `main`) — reverter quando esse branch mesclar

## 9. Fechamento

- [x] 9.1 Revisar se algum comportamento implementado diverge das specs desta change e ajustar o que for preciso antes de sincronizar — revisado requisito a requisito contra `specs/checklist-onboarding/spec.md` e `specs/gestao-clientes/spec.md`; nenhuma divergência encontrada
- [x] 9.2 Rodar `openspec validate checklist-onboarding-clientes --strict` — válido

## 10. Ajustes pós-revisão do usuário

- [x] 10.1 Modelo de onboarding compartilhado entre os escritórios do usuário (design.md D1 revisado): filtro de tenant de `GrupoTarefaOnboarding`/`TarefaOnboarding` passa a aceitar `EscritorioId == foco` OU vínculo (`UsuariosEscritorios`) do usuário atuante com o escritório do grupo — `ChecklistOnboardingCliente`/`ItemChecklistOnboarding` continuam com isolamento estrito (pertencem ao Cliente)
- [x] 10.2 Draggable nativo (HTML5 drag-and-drop, sem biblioteca) para reordenar tarefas dentro de um grupo em `/onboarding/modelos`, persistindo via `PUT /api/onboarding/grupos/ordem` já existente
- [x] 10.3 Removida a coluna "Responsáveis" da tabela de tarefas em `/onboarding/modelos`
- [x] 10.4 Removido o campo de responsáveis do cadastro de tarefa (modelo) — informação errada na primeira versão; o vínculo é por cliente, não pelo modelo (design.md D6 revisado)
- [x] 10.5 Responsável relocado para o item do checklist: nova entidade `ItemChecklistOnboardingResponsavel` (substitui `TarefaOnboardingResponsavel`, removida); `PUT /api/onboarding/clientes/{clienteId}/itens/{tarefaId}` passa a aceitar `responsavelIds`, validado contra o escritório do cliente; `<select multiple>` de responsáveis movido para `OnboardingClienteView.vue`, por tarefa
- [x] 10.6 Migration `OnboardingResponsavelPorClienteEModeloCompartilhado`: drop de `TarefaOnboardingResponsaveis`, create de `ItemChecklistOnboardingResponsaveis`
- [x] 10.7 Redesign visual de `OnboardingClienteView.vue` inspirado na estrutura do projeto de referência (círculo maior, faixa de progresso escura, badges numerados por grupo, status pill, cartão com sombra e blur decorativo) — construído só com tokens/classes do Contab One, nenhum CSS copiado
- [x] 10.8 Specs e design.md atualizados (D1, D6 revisados; requisito de responsável reescrito para "por cliente"; requisito de modelo reescrito para "compartilhado")
- [x] 10.9 Testes ajustados e verdes: `IsolamentoTest.cs` (+1 caso positivo de compartilhamento), `TraducaoLinqTest.cs` (filtros revisados), `OnboardingTest.cs` (responsável movido para o nível de item, +1 caso de não-vazamento entre clientes), Vitest (`OnboardingClienteView.spec.ts` ajustado ao novo layout), Playwright (`onboarding.spec.ts` ajustado à classe `is-complete`)

## 11. Modelos de onboarding (reestruturação)

- [x] 11.1 Entidades `ModeloOnboarding` (id, nome) e `ModeloOnboardingEscritorio` (vínculo modelo × escritório); `GrupoTarefaOnboarding` troca `EscritorioId` por `ModeloOnboardingId`; `Cliente` ganha `ModeloOnboardingId` opcional (design.md, D1 revisado 2×)
- [x] 11.2 Filtros de tenant reescritos: modelo/grupo/tarefa passam a ser visíveis via `ModeloOnboardingEscritorio` (igualdade simples pelo join), no lugar do `EXISTS` dinâmico contra `UsuariosEscritorios` da revisão anterior
- [x] 11.3 Migration `ModeloOnboarding` — duas tabelas novas, `Clientes.ModeloOnboardingId` (SetNull), rename de `GruposTarefaOnboarding.EscritorioId`; limpa as linhas de grupo pré-existentes (recurso pré-lançamento) para não deixar FK órfã do rename
- [x] 11.4 CRUD de modelos: `GET/POST /modelos`, `PUT/DELETE /modelos/{id}`, `GET /modelos/{id}/grupos` — criação vincula automaticamente todos os escritórios do admin atuante
- [x] 11.5 `POST /modelos/{id}/duplicar` — cópia profunda de grupos e tarefas, com vínculos re-derivados do admin que duplicou (design.md, D13)
- [x] 11.6 `GrupoRequest` passa a exigir `modeloOnboardingId`; checklist do cliente lê SÓ o modelo atual do cliente, e `PUT` de item recusa tarefa fora dele (design.md, D14)
- [x] 11.7 `GET /clientes/{id}` do checklist distingue `motivo: sem_modelo` de `motivo: sem_checklist` no 404, e a página do cliente mostra telas diferentes para cada caso
- [x] 11.8 `ClientesEndpoints`: `modeloOnboardingId` no DTO e no request (validado contra modelo visível), exposto na listagem para a coluna de ações decidir se mostra a ação de onboarding
- [x] 11.9 Frontend: `/onboarding/modelos` vira lista de modelos (criar, renomear, duplicar, excluir) e `/onboarding/modelos/:modeloId` recebe o CRUD de grupos/tarefas com drag-and-drop
- [x] 11.10 Frontend: `<select>` de modelo no cadastro/edição do cliente (opcional, "Sem onboarding"), e ícone de checklist só nas linhas de clientes com modelo
- [x] 11.11 Testes ajustados e ampliados: `OnboardingTest` (+5 casos — vínculo automático, renomear, duplicar, escopo por modelo, cliente sem modelo), `IsolamentoTest` (vínculo automático nos dois escritórios do admin), `TraducaoLinqTest` (filtros via `ModeloOnboardingEscritorios`), `ClientesView.spec.ts` (+1 caso — sem modelo, sem ícone), `e2e/onboarding.spec.ts` (fluxo completo com modelo)
- [x] 11.12 Specs e design.md atualizados (D1 revisado 2×, D13 e D14 novos; requisitos de modelo, replicação, vínculo automático e escolha no cadastro do cliente)
