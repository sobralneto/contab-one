## Why

O escritório coordena obrigações que não são de nenhuma ferramenta — ligar para o
cliente, protocolar uma guia, cobrar um documento, revisar uma competência — e
hoje isso vive em WhatsApp, papel e memória. O produto já sabe quem são os
usuários do escritório, quem são os clientes e como isolar um escritório do
outro; falta o lugar onde alguém escreve "o que eu tenho que fazer hoje" e o
colega vê que já foi feito.

Ao mesmo tempo, o hub cresceu na vertical: card de certificados no topo, seções
de domínio embaixo, e a página vira rolagem. Trazer as tarefas para lá sem
reorganizar o hub só pioraria isso — por isso as duas coisas andam juntas nesta
change.

## What Changes

- **Tarefa como entidade do escritório**, com **título e ao menos um responsável
  obrigatórios**; vencimento, recorrência, observação e cliente são opcionais. A
  tarefa é **única e compartilhada**: um ou mais responsáveis enxergam a mesma
  linha, e a conclusão feita por um aparece concluída para os demais.
- **Visibilidade por participação, não por escritório inteiro.** Um usuário vê
  apenas as tarefas em que é responsável ou que ele mesmo criou — inclusive
  `EscritorioAdmin`, que **não** ganha visão ampla das tarefas alheias. É a única
  entidade do produto com esse escopo mais estreito que o tenant, e é
  deliberado: a lista de tarefas é pessoal.
- **Seleção de responsável limitada ao escritório em foco**, listando apenas
  usuários ativos (`EscritorioUsuario` e `EscritorioAdmin`) vinculados a ele, com
  **o próprio usuário logado como valor padrão** do campo.
- **Recorrência que gera a próxima ocorrência.** Diária, semanal, mensal ou
  anual: concluir uma tarefa recorrente fecha aquela ocorrência e cria a
  seguinte, com o vencimento avançado pela regra, mesmos responsáveis, mesmo
  cliente. O histórico de ocorrências fica preservado. Sem job de fundo — a
  geração acontece no momento da conclusão.
- **Página `/tarefas`** com as visões **Hoje**, **Próximas**, **Atrasadas**,
  **Sem prazo** e **Concluídas**, criação inline ("Adicionar tarefa"), contador por
  visão e filtros por responsável e por cliente — a estrutura da referência visual
  aprovada, desenhada com os tokens e classes de `components.css`.
- **Nota rápida**: um campo de texto livre que grava uma tarefa sem pedir campo
  algum — a primeira linha vira o título, o resto vira observação, o responsável é
  quem escreveu e não há prazo. Disponível na página e na página inicial. É o que
  torna a visão "Sem prazo" necessária: sem ela, tarefa sem data ficaria
  inalcançável.
- **Hub reorganizado**: faixa horizontal no topo com os cards de ferramenta
  agrupados por domínio e, abaixo dela, três colunas — tarefas do dia do usuário
  logado (concluir, criar e anotar direto dali), certificados a vencer/vencidos, e
  uma terceira reservada, sem conteúdo. Em telas estreitas as áreas empilham na
  mesma ordem.
- **Rota transversal**, fora da família `/f/:produto`: tarefa não é ferramenta,
  não entra no catálogo, não tem gate comercial nem agente — mesmo tratamento de
  `/clientes` e `/agentes`.
- Nenhum conteúdo fiscal novo trafega: título e observação são texto escrito pelo
  próprio usuário, nada derivado de documento do cliente.

## Capabilities

### New Capabilities

- `controle-tarefas`: a tarefa do escritório — campos obrigatórios e opcionais,
  responsáveis múltiplos, regra de visibilidade por participação, conclusão
  compartilhada, recorrência que gera a próxima ocorrência, e as visões da página
  de tarefas.

### Modified Capabilities

- `navegacao-por-dominio`: a página inicial passa a ter os grupos de domínio em
  faixa horizontal no topo e, abaixo, três colunas — tarefas do dia, certificados e
  uma reservada.
- `vinculo-usuario-escritorios`: passa a existir uma consulta dos usuários do
  escritório em foco disponível a `EscritorioUsuario` (hoje qualquer listagem de
  usuários exige `EscritorioAdmin`), restrita a id e nome dos usuários ativos.

## Impact

**API (`ContabOne.Api/`)**
- `Domain/Entities.cs`: `Tarefa` e `TarefaResponsavel` (N:N com `Usuario`).
- `Domain/Enums.cs`: `RecorrenciaTarefa` (Nenhuma, Diaria, Semanal, Mensal,
  Anual) e `StatusTarefa` (Aberta, Concluida) — enums novos; nada reordenado nos
  existentes.
- `Infra/AppDbContext.cs`: `DbSet`s, filtro global de tenant nas duas entidades
  novas, índices por `EscritorioId`/`Vencimento` e a chave composta de
  `TarefaResponsavel`.
- `Features/Tarefas/TarefasEndpoints.cs` + grupo `/api/tarefas` em `Program.cs`
  sob a política `EscritorioUsuario`, incluindo `GET /api/tarefas/responsaveis`
  (usuários do escritório em foco para o seletor).
- Migration EF nova.

**Frontend (`ContabOne.Frontend/`)**
- `views/TarefasView.vue` e componentes em `components/tarefas/`
  (`LinhaTarefa.vue`, `FormularioTarefa.vue`, `NotaRapida.vue`).
- `components/dashboard/TarefasDoDia.vue` para a primeira coluna do hub e
  `components/tarefas/NotaRapida.vue` para a captura em texto livre.
- `views/HubView.vue`: reestruturação para três colunas.
- `router/index.ts`: rota transversal `/tarefas`.
- `api/endpoints/tarefas.ts` e tipos em `api/types.ts`.

**Testes**
- `IsolamentoTest.cs` e `TraducaoLinqTest.cs` cobrindo `Tarefa` e
  `TarefaResponsavel`.
- Testes de API para a regra de visibilidade (responsável ou criador; admin sem
  visão ampla) e para a geração da próxima ocorrência.
- Vitest para o cálculo do próximo vencimento, o agrupamento por visão
  (hoje/próximas/atrasadas), o valor padrão do seletor de responsável e a quebra
  título/observação da nota rápida.
- Playwright para criar tarefa → aparecer no hub → concluir.

**Fora de escopo**
- Subtarefas, etiquetas/tags, anexos e a "sticky wall" da referência visual.
- Notificação por e-mail ou alerta de tarefa vencendo (o motor de `Alerta` existe,
  mas ligar tarefa nele não foi pedido).
- Qualquer participação de agente Python — tarefas são só painel.
