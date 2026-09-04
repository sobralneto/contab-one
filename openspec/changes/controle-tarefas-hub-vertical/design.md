## Context

O produto já tem tudo o que uma tarefa precisa em volta: `Escritorio` como
fronteira de tenant, `Usuario`/`UsuarioEscritorio` como universo de responsáveis,
`Cliente` como objeto de trabalho, e `components.css` como sistema visual. O que
não existe é a entidade que registra trabalho humano não automatizado.

Duas restrições do repositório moldam o desenho:

1. **Isolamento multi-tenant é resolvido em um lugar só** (`Infra/AppDbContext.cs`,
   filtro global `_tenantContext.VeTodosOsEscritorios || x.EscritorioId == ...`).
   Entidade nova sem filtro vaza entre escritórios — `IsolamentoTest.cs` é o guarda.
2. **Predicado LINQ sobre propriedade computada quebra a tradução do EF em
   runtime** (defeito que já chegou à produção duas vezes, hoje coberto por
   `TraducaoLinqTest.cs`). Vale diretamente aqui: "tarefa atrasada" é a tentação
   óbvia de propriedade computada.

A referência visual aprovada (as duas telas de to-do enviadas) define a forma da
página: contador ao lado do título da visão, linha "＋ Adicionar tarefa" no topo
da lista, checkbox à esquerda, metadados em pílulas abaixo do título, e a visão
"Próximas" quebrada em blocos (Hoje / Amanhã / Esta semana).

## Goals / Non-Goals

**Goals:**

- Tarefa única e compartilhada entre N responsáveis, com conclusão que vale para
  todos eles.
- Visibilidade estreita: cada um vê o que é seu, sem que a lista de um colega
  vire dado de gestão.
- Recorrência que não exige job de fundo nem varredura diária.
- Hub em três colunas que ainda funciona em tela estreita.
- Reaproveitar o sistema visual existente — nenhum CSS por view onde já existe
  classe compartilhada em `components.css`.

**Non-Goals:**

- Subtarefas, tags, anexos, sticky wall (existem na referência, não foram pedidos).
- Notificação ou alerta de tarefa vencendo.
- Tarefa como ferramenta do catálogo (`Produto`) — não é ferramenta, é transversal.
- Corrigir a convenção de fuso do repositório como um todo (ver Decisão 6).

## Decisions

### 1. Visibilidade por participação, aplicada no handler — não no filtro global

O filtro global de tenant continua sendo o de sempre (`EscritorioId`). Por cima
dele, **todo handler de leitura de tarefa adiciona**:

```
t.Responsaveis.Any(r => r.UsuarioId == tenant.UsuarioId) || t.CriadoPorUsuarioId == tenant.UsuarioId
```

Por que não colocar isso no filtro global: o filtro global existe para o
**tenant**, e misturar nele uma regra de usuário faria com que qualquer consulta
futura sobre `Tarefa` — inclusive contagem administrativa ou migração — herdasse
silenciosamente uma regra que não é de isolamento. Fica explícito no handler, com
teste próprio.

O **criador entra na regra** porque, sem isso, quem cria uma tarefa e atribui só a
um colega perde a tarefa de vista no instante seguinte ao salvar.

`EscritorioAdmin` **não** tem visão ampliada, e `PlatformAdmin` sem foco também
não: a cláusula acima é aplicada mesmo quando `VeTodosOsEscritorios` é verdadeiro.
Essa é a única entidade do produto cujo escopo é mais estreito que o tenant — está
registrado aqui porque contraria a expectativa padrão de quem for mexer no código
depois.

*Alternativa descartada:* visibilidade por escritório inteiro com filtro "minhas
tarefas" na tela. Mais simples e alinhada ao resto do produto, mas transforma a
lista pessoal em painel de produtividade visível a todos.

### 2. Responsáveis como entidade de junção explícita

`TarefaResponsavel` (chave composta `TarefaId` + `UsuarioId`), no mesmo padrão de
`UsuarioEscritorio` e `ItemChecklistOnboardingResponsavel` — não skip navigation.
Junção explícita porque a regra de visibilidade consulta essa tabela diretamente e
porque a tabela tende a ganhar coluna (data de atribuição) sem custar outra
migração sobre ela.

**Ao menos um responsável é obrigatório**, validado no handler — não há como
expressar "coleção não vazia" no banco. `TarefaResponsavel` cascateia com a
tarefa; o vínculo com `Usuario` é `Restrict`, para que desligar um usuário nunca
apague tarefa alheia silenciosamente.

Todo responsável enviado é validado contra `UsuarioEscritorio` do escritório da
tarefa — mesma checagem de `OnboardingEndpoints.ValidarResponsaveisAsync`. Id de
usuário de outro escritório é 400, nunca ignorado em silêncio.

### 3. `GET /api/tarefas/responsaveis` em vez de reusar `/api/usuarios`

O seletor precisa da lista de usuários do escritório em foco, mas o grupo
`/api/usuarios` exige `EscritorioAdmin` no nível do grupo em `Program.cs` — e
política declarada no grupo **soma** com a do endpoint, então não dá para afrouxar
lá dentro. O endpoint novo vive no grupo `/api/tarefas` (`EscritorioUsuario`) e
devolve apenas `{ id, nome }` dos usuários **ativos** vinculados ao escritório em
foco, ordenados por nome.

Devolver só id e nome é deliberado: não é a listagem de gestão de usuários, é o
que um seletor precisa. E-mail, papel, último login e a carteira de escritórios do
colega continuam restritos a `EscritorioAdmin`.

`PlatformAdmin` **sem foco** não tem escritório para listar: o endpoint responde
400 pedindo que ele escolha um escritório, em vez de devolver lista vazia
(indistinguível de "escritório sem usuários") ou todos os usuários da plataforma.

### 4. Recorrência gera a próxima ocorrência na conclusão — sem job

Ao concluir uma tarefa com `Recorrencia != Nenhuma`, o mesmo handler, na mesma
transação: marca a atual como `Concluida` (gravando `ConcluidaEm` e
`ConcluidaPorUsuarioId`) e insere uma tarefa nova, aberta, copiando título,
observação, cliente, responsáveis e a própria recorrência, com
`Vencimento = ProximoVencimento(vencimento anterior, recorrência)`.

A cadeia é rastreável por `TarefaOrigemId` (auto-relacionamento opcional,
`Restrict`), que aponta para a ocorrência anterior.

O dia de referência do avanço é sempre o **vencimento anterior**, nunca "hoje" —
senão concluir com atraso empurraria a série inteira para frente:

| Recorrência | Avanço |
|---|---|
| Diária | +1 dia |
| Semanal | +7 dias |
| Mensal | +1 mês, saturando no último dia do mês |
| Anual | +1 ano, com 29/02 caindo em 28/02 fora de bissexto |

`DateOnly.AddMonths`/`AddYears` do .NET já saturam exatamente assim — a função é
uma linha, mas ganha teste próprio pelos dois casos de borda (31/01 → 28/02 e
29/02 → 28/02).

**Tarefa recorrente sem vencimento não gera ocorrência seguinte** — não há de onde
avançar. O formulário exige vencimento quando a recorrência é diferente de
`Nenhuma`, e a API valida o mesmo.

*Alternativa descartada:* materializar N ocorrências futuras no cadastro, ou um job
diário (`--job=alertas` já existe como precedente). Ambas criam linhas que ninguém
pediu e obrigam a decidir "até quando"; gerar na conclusão mantém exatamente uma
ocorrência aberta por série.

### 5. "Atrasada" é derivada na consulta, nunca propriedade computada

`Tarefa` guarda `Status` e `Vencimento`. "Atrasada" (`Status == Aberta &&
Vencimento < hoje`) é escrita **como predicado na query**, e a resposta traz o
campo já resolvido para a tela. Não existe `Tarefa.Atrasada { get; }` — é
exatamente o defeito que `TraducaoLinqTest.cs` guarda.

### 6. Data de vencimento é `DateOnly`; o "hoje" das visões vem do cliente

`Vencimento` é `DateOnly?`, como `Cliente.CertificadoValidade` e
`ParcelaPgdas.Vencimento`. Tarefa vence no dia, não no instante.

Para as visões, a listagem aceita `de`/`ate` (`DateOnly`), e **o frontend envia a
data local do navegador** — a coluna "tarefas do dia" e a visão "Hoje" usam o dia
do usuário, não o do servidor. Sem isso, entre 21h e meia-noite no horário de
Brasília o painel já mostraria o dia seguinte, porque o resto do repositório
resolve "hoje" com `DateOnly.FromDateTime(DateTime.UtcNow)`.

Quando os parâmetros são omitidos, a API cai nesse mesmo `DateTime.UtcNow`, para
não introduzir uma segunda convenção de fuso no servidor. Corrigir a convenção
global (`ClientesEndpoints`, `DashboardEndpoints`, `AlertaJob`) está fora do
escopo desta change.

### 7. Hub em três colunas com CSS grid e ordem de empilhamento preservada

`HubView.vue` tem duas áreas empilhadas:

1. **`.hub-ferramentas`** — faixa horizontal no topo, `flex` com `wrap`, com as
   seções de domínio lado a lado. Cada seção mantém `width: 300px`: deixá-la
   crescer livre esticaria um domínio de ferramenta única pela tela inteira,
   já que o card é desenhado para ~260px.
2. **`.hub-colunas`** — `grid-template-columns: repeat(3, minmax(0, 1fr))`, com
   `TarefasDoDia` na primeira, `CertificadosVencimento` na segunda e a terceira
   **deliberadamente vazia**, como espaço reservado.

A terceira trilha é declarada no grid mas não recebe elemento algum — não existe
`<div>` vazio no DOM. Declará-la ainda assim é o que impede tarefas e
certificados de esticarem até metade da tela cada; é a diferença entre "reservado"
e "sobrou espaço".

Abaixo de ~1180px o grid cai para duas colunas — a trilha reservada é a primeira
a sair, antes de espremer o que tem conteúdo — e abaixo de ~780px, para uma só.

`minmax(0, …)` em todas as trilhas: sem isso, um nome de cliente longo no card de
certificados força rolagem horizontal na página inteira.

A coluna 1 mantém as seções de domínio empilhadas verticalmente — hoje elas são
`flex-wrap` com largura fixa de 300px, o que dentro de uma coluna estreita
produziria uma coluna dentro da coluna.

Cada coluna falha sozinha: o hub já trata erro de certificados sem derrubar a tela,
e a coluna de tarefas segue a mesma regra.

### 8. Rota transversal, não ferramenta do catálogo

`/tarefas`, fora de `/f/:produto`, como `/clientes` e `/agentes`. Nenhum `Produto`
novo, nenhum `EscritorioProduto`, nenhum gate comercial: tarefa não é uma
ferramenta contratável, é infraestrutura do painel. Consequência aceita: o acesso
não vem do catálogo, então o item de menu é fixo, como já acontece com clientes e
agentes.

## Risks / Trade-offs

- **Um responsável desatribuído perde acesso ao histórico da tarefa.** Se A e B são
  responsáveis, B é removido e a tarefa já estava concluída, B deixa de enxergá-la
  (a menos que a tenha criado). → Aceito: é a consequência direta da regra de
  visibilidade pedida. Remover responsável é ação explícita de quem enxerga a
  tarefa, não efeito colateral.

- **Ninguém no escritório tem visão do todo.** Não há tela de "todas as tarefas do
  escritório", nem para `EscritorioAdmin`. → Aceito e documentado; se depois for
  preciso, entra como capability própria com decisão consciente sobre privacidade,
  não como flag ligada às pressas.

- **Série recorrente se interrompe se a ocorrência aberta for excluída.** Não há
  varredura que perceba a lacuna. → Mitigação: excluir uma tarefa recorrente aberta
  pede confirmação explícita, com o texto dizendo que a série termina ali.

- **Data local do cliente como fonte do "hoje".** Navegador com fuso errado vê a
  lista do dia errado. → Mitigação: o servidor valida o intervalo recebido
  (`de <= ate`, janela máxima) e nada além da montagem da visão depende dele; a
  gravação de `ConcluidaEm` continua em UTC no servidor.

- **Hub com três colunas em telas de 1280px fica apertado.** → Mitigação: os
  breakpoints acima, e o card de ferramenta já é desenhado para ~260px.

- **Tarefa vira depósito de dado sensível de cliente.** A observação é texto livre e
  alguém pode colar ali o que o contrato de privacidade mantém fora da API. →
  Mitigação: limite de tamanho no campo e nenhuma promessa de sigilo especial na
  tela. O contrato do produto é sobre conteúdo fiscal trafegado pelo agente; texto
  que o usuário escolhe digitar é dele. Sem tratamento novo.

## Migration Plan

Uma migration EF aditiva: duas tabelas novas (`Tarefas`, `TarefasResponsaveis`) e
nenhuma alteração em tabela existente. Sem backfill — o escritório começa com zero
tarefas, e as visões já têm estado vazio. Rollback é o `Down` da migration; nada
fora da change depende das tabelas novas.

O hub reorganizado é troca de layout sem migração de dado: rollback é reverter o
componente.

## Open Questions

- Excluir tarefa é exclusão física ou marcação? Assumido **físico** — não há
  auditoria de tarefa no escopo. Se auditoria virar requisito, vira soft delete com
  coluna nova.
- A visão "Concluídas" mostra tudo ou uma janela? Assumida **janela de 90 dias** com
  paginação, para que a série recorrente antiga não cresça a resposta sem limite.
