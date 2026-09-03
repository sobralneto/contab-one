## Context

O projeto de referência (`checklistonboardingclientes`, TanStack Start + Netlify
Functions) resolve o problema com três blocos de tarefas **fixos em código** e um
único `jsonb checks` por empresa. Não tem contas, nem papéis: a autorização inteira
é um UUID de workspace no `localStorage`. Nada disso sobrevive ao trazer o checklist
para o Contab One, onde cliente, usuário, escritório e isolamento multi-tenant já
existem e são a espinha do produto.

O que se aproveita da referência é a **estrutura visual da página** — círculo de
percentual no topo, faixa de progresso antes do primeiro grupo, blocos por grupo,
linha de tarefa com checkbox e título riscado quando concluída — reconstruída com
os tokens e classes de `assets/styles/components.css`, não com o CSS de lá.

Três decisões já foram tomadas com o usuário antes deste documento e são premissa,
não alternativa em aberto:

1. **Modelo por escritório + status por cliente** (e não cópia de tarefas por
   cliente).
2. **Rotas transversais**, ao lado de `/clientes`, e não uma ferramenta nova do
   catálogo `/f/:produto`.
3. **`EscritorioAdmin` edita o modelo; `EscritorioUsuario` opera o checklist.**

## Goals / Non-Goals

**Goals:**

- Modelo de onboarding (grupos → tarefas) editável por escritório, sem deploy.
- Checklist por cliente, criado por ação explícita do usuário (nunca automático no
  cadastro), derivado do modelo do escritório a partir daí, com status, observação
  e percentual persistido.
- Responsáveis por tarefa vindos dos usuários do escritório em foco, por
  identificador — não por texto livre.
- Página do cliente com a estrutura da referência, no design system do Contab One.
- Isolamento multi-tenant com o mesmo rigor das entidades existentes: filtro global
  em `AppDbContext`, escopo sempre do `TenantContext`, nunca da rota.

**Non-Goals:**

- Exportação em PDF do checklist (existe na referência, não foi pedida).
- Modelo global da plataforma, herdado por todos os escritórios: cada escritório
  começa com o modelo vazio e monta o próprio.
- Qualquer participação de agente Python, endpoint sob `/api/agent` ou execução.
- Produto novo no catálogo, gate comercial por `EscritorioProdutos`, item de menu
  vindo de `GET /api/produtos`.
- Histórico/auditoria de quem marcou o quê ao longo do tempo — grava-se apenas o
  estado atual (quem concluiu e quando), não uma trilha.

## Decisions

### D1 — `ModeloOnboarding` como entidade própria; status por cliente (revisado 2×)

**Escolhido:** duas árvores separadas, com o modelo no topo da primeira.

```
ModeloOnboarding (nome)
 ├─ ModeloOnboardingEscritorio (modeloId, escritorioId)  ← quem enxerga o modelo
 └─ GrupoTarefaOnboarding (nome, titulo, descricao, ordem)
     └─ TarefaOnboarding (nome, ordem, link, temDoisFatores)

Cliente (modeloOnboardingId — opcional, escolhido no cadastro do cliente)
 └─ ChecklistOnboardingCliente (percentualConclusao, atualizadoEm)
     └─ ItemChecklistOnboarding (tarefaId, status, observacao, concluidoEm, concluidoPorId)
         └─ ItemChecklistOnboardingResponsavel (itemId, usuarioId) — ver D6
```

**Por quê (modelo, não tarefas por cliente):** o onboarding é o mesmo para
vários clientes — é justamente a padronização que se quer. Copiar as tarefas
por cliente (alternativa considerada) daria liberdade de divergir, ao custo de
duplicar entidades e de tornar "corrigir o link do portal" um trabalho de N
clientes. Quem precisa de uma variação duplica o MODELO (ver D13), não o
trabalho de cada cliente.

**Revisão 1 (descartada):** a primeira tentativa de compartilhar o modelo entre
escritórios manteve `GrupoTarefaOnboarding.EscritorioId` como âncora e ampliou o
query filter com um `EXISTS` dinâmico contra `UsuariosEscritorios` (visível a
quem tem vínculo com o escritório do grupo). Funcionava, mas fazia a resposta a
"de quem é este modelo?" depender de QUEM pergunta, e não havia um objeto
"modelo" para nomear, renomear ou duplicar.

**Revisão 2 (atual):** `ModeloOnboarding` vira entidade de verdade — com Id e
nome — e a visibilidade passa a ser um vínculo EXPLÍCITO
(`ModeloOnboardingEscritorio`), gravado na criação do modelo com TODOS os
escritórios do administrador que o criou. O grupo deixa de ter `EscritorioId` e
passa a ter `ModeloOnboardingId`.

Ganhos sobre a revisão 1:
- O filtro vira uma igualdade simples através do join
  (`m.Escritorios.Any(v => v.EscritorioId == tenant.EscritorioId)`) — sem
  `EXISTS` dinâmico contra vínculos de usuário, e a mesma resposta para
  qualquer sessão do mesmo escritório.
- Nomear/renomear/duplicar um modelo passa a existir (D13).
- Cada cliente escolhe QUAL modelo usa, em vez de todos herdarem a união de
  tudo que existia (D14).

**Preço aceito:** o vínculo é um retrato do momento da criação. Um escritório
que o administrador passe a gerenciar depois NÃO ganha acesso retroativo aos
modelos antigos — é o que "vínculo criado automaticamente" quer dizer, e a
alternativa (recalcular vínculos dinamicamente a cada consulta) traz de volta
exatamente o problema da revisão 1.

**Por que não um modelo literalmente global à plataforma** (alternativa
considerada, mesma família do catálogo `Produto`/`Dominio`): romperia
isolamento multi-tenant de verdade — um `EscritorioAdmin` de um cliente da
plataforma alteraria o onboarding de TODOS os outros clientes, não só dos
próprios escritórios.

`ChecklistOnboardingCliente`/`ItemChecklistOnboarding` NÃO participam desse
compartilhamento — pertencem ao Cliente, que vive em exatamente um escritório;
isolamento estrito ali, como no resto do sistema.

**Preço aceito, e é o principal (inalterado pela revisão):** mexer no modelo
mexe no denominador do percentual de todo mundo que o enxerga — agora
potencialmente vários escritórios ao mesmo tempo, não só um. Acrescentar
tarefa faz o percentual de todos os clientes cair; excluir tarefa concluída
faz subir. É consequência inerente da escolha, tratada em D5 e sinalizada na
tela antes de excluir grupo.

### D2 — `ChecklistOnboardingCliente` nasce por ação explícita; itens, sob demanda

Diferente da primeira versão deste design, o checklist **não** é derivado
implicitamente na primeira leitura. Um cliente novo não tem checklist até o
usuário criar um, pela ação "Adicionar checklist" na listagem de clientes
(`POST /api/onboarding/clientes/{clienteId}`), que grava a linha
`ChecklistOnboardingCliente` com percentual zero e nenhum item.

A partir daí, `ItemChecklistOnboarding` continua nascendo sob demanda — só quando
alguém marca a tarefa ou escreve uma observação. Tarefa sem linha é aberta.

**Por quê a criação explícita:** pedido direto do escopo — cliente cadastrado não
deve ganhar onboarding sozinho, é decisão de quem está trabalhando aquele cliente,
tomada uma vez, cliente a cliente. Também evita que todo cliente já cadastrado
antes desta feature apareça com um checklist "fantasma" no dia do deploy.

**Por quê os itens continuam preguiçosos:** evita gravar N linhas por cliente na
criação do checklist, e faz "tarefa nova entra no modelo" funcionar sem migração de
dados — ela simplesmente não tem linha em lugar nenhum, então está aberta em todo
checklist já criado.

**Consequência:** o cálculo do percentual conta linhas com status concluído contra
o total de tarefas do modelo, e não linhas contra linhas.

**Alternativa considerada:** materializar todos os itens na criação do checklist.
Torna a leitura mais simples mas cria lixo se o modelo crescer depois — os itens
já gravados não ajudam em nada que a ausência de linha não resolva.

### D3 — Percentual é derivado E persistido

A verdade é derivável (concluídas ÷ total). Persistir em
`ChecklistOnboardingCliente.PercentualConclusao` é redundância deliberada, pedida
no escopo, e paga por si: permite mostrar progresso de onboarding na listagem de
clientes ou no dashboard sem varrer itens de todos os clientes.

**Regra que evita divergência:** o percentual **nunca** é enviado pelo cliente HTTP.
O servidor recalcula a partir do estado e grava, na mesma transação da alternância.
Divergir só é possível se alguém alterar o banco por fora.

Total zero → percentual zero, explicitamente, sem divisão por zero.

### D4 — Escopo do tenant

Segue o padrão de `PgdasEndpoints.EscopoOuNull`: escritório **sempre** do
`TenantContext`, nunca de rota ou query. As cinco entidades novas ganham filtro
global em `AppDbContext`, no formato canônico:

```csharp
_tenantContext.VeTodosOsEscritorios || x.EscritorioId == _tenantContext.EscritorioId
```

`GrupoTarefaOnboarding` e `ChecklistOnboardingCliente` carregam `EscritorioId`
próprio para o filtro ser direto. `TarefaOnboarding`,
`TarefaOnboardingResponsavel` e `ItemChecklistOnboarding` filtram pelo pai —
mesmo arranjo já usado por `ApuracaoSegregacao`. `IsolamentoTest.cs` recebe as
cinco.

`PlatformAdmin` sem escritório em foco: o modelo é do escritório e a tela não tem
sentido sem foco. Os endpoints de escrita devolvem `Forbid` quando
`tenant.EscritorioId` é nulo, como o PGDAS-D faz.

### D5 — Exclusão em cascata, com aviso na tela

Excluir grupo apaga suas tarefas; excluir tarefa apaga os `ItemChecklistOnboarding`
dela em todos os clientes (`OnDelete(DeleteBehavior.Cascade)`) e os responsáveis.

Isso perde marcação de cliente — por isso a confirmação na UI diz quantas tarefas
saem junto e que o percentual de todos os clientes muda. Alternativa considerada
(soft delete com `Ativo`) foi descartada: complica toda consulta para preservar
dado que ninguém vai consultar, e a tarefa desativada continuaria aparecendo em
relatório histórico sem contexto.

Recalcular o percentual de todos os clientes na hora da exclusão seria uma escrita
em massa disparada por um clique de cadastro. Em vez disso, o percentual gravado é
reconciliado na próxima leitura do checklist daquele cliente: o GET compara o
percentual persistido com o calculado e grava a diferença quando houver.

### D6 — Responsável é POR CLIENTE, não pelo modelo (revisado)

**Revisão pós-implementação**: a primeira versão deste design vinculava o
responsável à `TarefaOnboarding` (modelo). Informação errada — o pedido real é
"para o cliente X, a tarefa Y é do João; para o cliente Z, a mesma tarefa é da
Ana". `TarefaOnboardingResponsavel` foi removida; o vínculo agora é
`ItemChecklistOnboardingResponsavel(ItemChecklistOnboardingId, UsuarioId)`,
chave composta — pendurado no item do checklist (tarefa × cliente), não na
tarefa do modelo.

A validação confirma que cada `UsuarioId` tem `UsuarioEscritorio` com o
escritório do **cliente dono do checklist** (`checklist.EscritorioId`) — a
mesma fonte de verdade que `AGENTS.md` aponta para "este usuário pode enxergar
este escritório?". Como o item nasce sob demanda (D2), a validação roda no PUT
do item (`AtualizarItemAsync`), não mais na criação/edição da tarefa.

Usuário desvinculado do escritório depois: o item não quebra. A leitura do
checklist faz `join` com os usuários ainda vinculados, então ele some da lista
de responsáveis sem apagar nada. A linha órfã é inofensiva e é limpa se o
usuário for excluído (`Cascade` pelo `UsuarioId`).

O `<select multiple>` fica na página do CLIENTE (`OnboardingClienteView.vue`),
não no cadastro do modelo — cada tarefa do checklist tem o seu próprio select,
salvo junto com status e observação no mesmo PUT. Consome `GET /api/usuarios`
— que já existe, já é escopado ao escritório e já devolve `nome`. Nenhum
endpoint novo de usuários.

**Consequência para D1**: como o modelo agora pode ser compartilhado entre
escritórios (ver D1 abaixo), fixar o responsável no modelo teria sido ainda
mais errado — o mesmo João poderia não ter vínculo com todos os escritórios
que compartilham aquele modelo. Responsável por cliente evita esse problema
de propósito, não por acidente.

### D7 — Superfície HTTP

`app.MapGroup("/api/onboarding")` em `Program.cs` com
`.RequireAuthorization("EscritorioUsuario")` — a política mais permissiva do grupo.
Os endpoints de cadastro do modelo encadeiam `.RequireAuthorization("EscritorioAdmin")`
no próprio `MapPost`/`MapPut`/`MapDelete`: ASP.NET Core combina as duas políticas do
mesmo endpoint com E lógico, e como `EscritorioAdmin` já implica `EscritorioUsuario`
(hierarquia de papéis), o efeito é exigir só `EscritorioAdmin` — sem checagem manual
de papel dentro do handler.

| Verbo | Rota | Papel |
|---|---|---|
| GET | `/api/onboarding/modelo` | EscritorioUsuario |
| POST/PUT/DELETE | `/api/onboarding/grupos[/{id}]` | EscritorioAdmin |
| POST/PUT/DELETE | `/api/onboarding/tarefas[/{id}]` | EscritorioAdmin |
| PUT | `/api/onboarding/grupos/ordem` | EscritorioAdmin |
| POST | `/api/onboarding/clientes/{clienteId}` | EscritorioUsuario |
| GET | `/api/onboarding/clientes/{clienteId}` | EscritorioUsuario |
| PUT | `/api/onboarding/clientes/{clienteId}/itens/{tarefaId}` | EscritorioUsuario |

`POST /api/onboarding/clientes/{clienteId}` cria o checklist do cliente (D2); é
idempotente na prática porque a listagem só oferece essa ação a cliente sem
checklist — mesmo assim, se acionado sobre cliente que já tem checklist, devolve o
checklist existente em vez de duplicar.

`GET /api/onboarding/clientes/{clienteId}` devolve `404` quando o cliente não tem
checklist criado — a página trata isso oferecendo a criação (spec, "Página aberta
antes de o checklist existir"), não como erro. Quando existe, devolve o checklist
montado — grupos, tarefas, responsáveis e o status/observação de cada uma — em uma
resposta só. O PUT do item carrega status e observação juntos e devolve o
percentual recalculado, para a tela não precisar de um segundo pedido só para o
número.

`clienteId` na rota **não é** escopo de tenant: a consulta continua passando pelo
filtro global, então cliente de outro escritório simplesmente não é encontrado.

### D8 — Enum novo

`StatusTarefaOnboarding { Aberto, Concluido }`, persistido como inteiro, como todo
enum do projeto exceto `LayoutDashboard`. Nenhum agente Python lê este campo, então
não há contrato C#↔Python novo — nada a espelhar em `api_client.py`.

**Alternativa considerada:** `bool Concluido`. O enum foi preferido porque o escopo
já fala em "status", e um terceiro estado ("não se aplica a este cliente") é o
próximo pedido previsível — acrescentar membro ao fim do enum é seguro, trocar
`bool` por enum depois é migração.

### D9 — Rotas e navegação do frontend

```
/clientes/:clienteId/onboarding   OnboardingClienteView.vue    EscritorioUsuario
/onboarding/modelos               OnboardingModelosView.vue    EscritorioAdmin
```

Sem `meta.pagina`: não são rotas de ferramenta, e `router/guards.ts` só valida
produto/página sob `/f/:produto`. Entram na seção "transversais" de
`router/index.ts`, ao lado de `/clientes` e `/agentes`, com `meta.papeis` fazendo o
controle de acesso.

`/onboarding/modelos` precisa de porta de entrada própria (não sai do catálogo):
entra no menu lateral no mesmo bloco transversal onde já vivem Clientes, Agentes e
Usuários, visível a `EscritorioAdmin`.

### D10 — Estado da página do cliente

Marcar tarefa é otimista: a UI alterna o checkbox, o círculo e a barra na hora e
dispara o PUT; se falhar, reverte e avisa. O percentual exibido vem do cálculo
local durante a interação e é reconciliado com o valor devolvido pelo servidor —
que é a autoridade.

Observação usa debounce (a referência usa 550 ms; o mesmo serve) para não gerar um
PUT por tecla. Diferente da referência, a resposta **é** aplicada, porque só carrega
o percentual, não o texto que o usuário está digitando.

O círculo é um SVG com dois `<circle>` e `stroke-dashoffset` proporcional, como na
referência, com `var(--accent)` no arco e `var(--border)` na trilha. A barra usa
`transform: scaleX()`. Nenhuma biblioteca nova.

Título de tarefa concluída recebe `text-decoration: line-through` com
`var(--text-muted)`.

### D12 — `GET /api/clientes/{id}` para o cabeçalho da página do cliente

A página de onboarding do cliente precisa do nome/código do cliente tanto
antes quanto depois de o checklist existir (estado 404 incluso), e
`ChecklistClienteDto` propositalmente não carrega esses campos — pertencem ao
cliente, não ao checklist. `ClientesEndpoints` ganhou um `GET /{id}` simples
(mesmo formato do `ClienteDto` da listagem, escopado pelo filtro global),
descoberto como faltante só durante a implementação da view. Padrão REST
básico, sem decisão nova de design por trás.

### D11 — A listagem de clientes sabe, sem N+1, quem já tem checklist

`GET /api/clientes` ganha um campo booleano no DTO de listagem (`temChecklistOnboarding`,
por exemplo) para a coluna de ações escolher entre "Adicionar" e "Abrir" sem um
pedido por linha. `ClientesEndpoints.ListarAsync` já pagina uma query sobre
`Clientes`; o campo é resolvido com `Any()` correlacionado a
`ChecklistOnboardingCliente` dentro da mesma projeção (`ToListAsync` com
`Select` incluindo o booleano), não com uma consulta por cliente.

**Alternativa considerada:** o frontend descobrir o estado tentando o `GET` do
checklist e tratando `404` como "sem checklist". Rejeitada: transformaria abrir a
listagem em N requisições (uma por cliente visível), contra o modelo de página
única que o resto da tela já segue.

### D13 — Duplicação é uma cópia profunda, e re-deriva os vínculos

`POST /api/onboarding/modelos/{id}/duplicar` cria um `ModeloOnboarding` novo
(nome `"<original> (cópia)"`) e copia grupos e tarefas como registros NOVOS,
preservando a ordenação. A cópia é independente do original em ambos os
sentidos — é o ponto da funcionalidade: variar sem reconstruir.

Os vínculos de escritório da cópia são **re-derivados** dos escritórios de quem
duplicou, não copiados do original. Assim a regra "modelo nasce vinculado aos
escritórios do administrador" vale igual para criar e para duplicar; copiar os
vínculos do original poderia dar a um administrador acesso a um escritório que
ele não gerencia.

### D14 — O cliente escolhe o modelo; o checklist lê o modelo ATUAL

`Cliente.ModeloOnboardingId` é opcional e escolhido no cadastro/edição do
cliente (`<select>` no formulário), não na criação do checklist. Consequências:

- A ação de checklist na listagem de clientes só aparece para cliente COM
  modelo — sem modelo não há o que montar.
- `GET /api/onboarding/clientes/{id}` distingue os dois vazios pelo campo
  `motivo` no corpo do 404: `sem_modelo` (falta escolher, a tela manda editar o
  cliente) e `sem_checklist` (tem modelo, falta criar — a tela oferece o botão).
  Dois estados diferentes precisam de duas telas diferentes; um 404 mudo faria
  a página oferecer "criar checklist" para quem não tem como criar.
- O checklist é montado a partir do modelo vigente do cliente A CADA LEITURA.
  Trocar o modelo do cliente troca o que aparece; marcações de tarefas do
  modelo anterior ficam órfãs (não contam, não somem do banco). Guardar um
  snapshot do modelo no checklist foi considerado e descartado: dobraria o
  número de lugares a manter em sincronia para um caso de borda raro.
- `PUT …/itens/{tarefaId}` recusa tarefa que não pertença ao modelo atual do
  cliente — impede marcar, por id, uma tarefa de um modelo antigo.

## Risks / Trade-offs

- **Alterar o modelo mexe no percentual de todos os clientes** → inerente a D1.
  Mitigado pela confirmação explícita antes de excluir grupo/tarefa (a spec exige) e
  pela reconciliação do percentual na leitura (D5). Não há como oferecer
  padronização e imunidade histórica ao mesmo tempo.

- **Escritório novo começa com o modelo vazio** → a página do cliente abre em 0% e
  sem grupos. Mitigado por estado vazio (`EstadoVazio.vue`) que aponta para
  `/onboarding/modelos`, e por `EscritorioUsuario` — que não pode criar o modelo —
  receber uma mensagem dizendo que o administrador precisa montá-lo.

- **Percentual persistido pode divergir do derivado** se alguém escrever no banco
  por fora ou se uma exclusão de tarefa não for seguida de leitura. Mitigado por D3
  (só o servidor grava) + D5 (reconciliação na leitura). O valor derivado é sempre
  a verdade em caso de conflito.

- **Marcação simultânea por dois usuários no mesmo cliente** → o último PUT vence,
  e o percentual é recalculado do estado do banco em ambos. Nenhum item se perde;
  no máximo uma tela mostra um número velho até a próxima leitura. Aceito: o volume
  torna a colisão rara e o dano é cosmético.

- **`LINQ` sobre propriedade computada quebra a tradução em runtime** — o defeito
  que chegou à produção duas vezes neste repo. Nenhuma propriedade computada em
  predicado; a contagem de concluídos é `Count(i => i.Status == StatusTarefaOnboarding.Concluido)`
  sobre coluna real, e `TraducaoLinqTest.cs` cobre as consultas novas.

- **`observacao` é texto livre digitado pelo usuário do escritório.** Não fere o
  contrato de privacidade (nada de conteúdo fiscal, nada de CNPJ completo derivado
  de documento), mas merece limite de tamanho no servidor, como o resto da API.

## Migration Plan

1. Entidades + `Enums.cs` + configuração e filtros em `AppDbContext.cs`.
2. `dotnet ef migrations add ChecklistOnboarding --project ContabOne.Api` — cinco
   tabelas novas, nenhuma coluna alterada em tabela existente, nenhum backfill.
   Migração puramente aditiva: roda sozinha no boot da API e no Testcontainers.
3. Endpoints e grupo em `Program.cs`.
4. Frontend: tipos, cliente de API, duas views, rotas, botão na coluna de ações.
5. Testes: `IsolamentoTest`, `TraducaoLinqTest`, Vitest do percentual, Playwright do
   caminho completo.

**Rollback:** como nada existente muda de forma, reverter é remover as rotas e as
telas; as tabelas podem ficar vazias sem afetar nada. Migration de reversão só é
necessária se as tabelas incomodarem.

## Open Questions

- Nenhuma bloqueante. As três ambiguidades estruturais foram resolvidas com o
  usuário antes deste documento (Context).
- Fica registrado para depois, fora deste escopo: mostrar o percentual de onboarding
  como coluna na listagem de clientes ou como card no dashboard — D3 já deixa o dado
  pronto para isso.
