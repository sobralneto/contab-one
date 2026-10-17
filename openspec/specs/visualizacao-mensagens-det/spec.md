## Purpose

Cobre a página do painel onde o escritório visualiza as mensagens da Caixa
Postal DET coletadas pelo agente, publicada de forma catálogo-driven como
qualquer outra ferramenta.

## Requirements

### Requirement: O produto DET declara uma página de mensagens no catálogo

O produto DET DEVE (MUST) declarar a nova página de mensagens em
`Produto.Paginas`, seguindo o mesmo mecanismo catálogo-driven que já governa
o menu e as rotas `/f/:produto/:pagina` de toda ferramenta — sem item de
menu hard-coded no frontend.

#### Scenario: Escritório contratou o produto DET

- **WHEN** um escritório com o produto DET habilitado carrega o catálogo
  (`GET /api/produtos`)
- **THEN** a página de mensagens DET aparece no menu desse produto

#### Scenario: Escritório sem o produto DET

- **WHEN** um escritório não tem o produto DET habilitado
- **THEN** a página de mensagens DET não aparece no menu nem é alcançável
  pela rota

### Requirement: A página lista mensagens DET filtráveis por cliente

A página de mensagens DET DEVE (MUST) listar as mensagens recebidas do
escritório em foco e DEVE (MUST) oferecer um filtro por cliente, usando o
endpoint de consulta de `registro-mensagens-det`.

#### Scenario: Usuário abre a página sem filtro

- **WHEN** o usuário abre a página de mensagens DET sem selecionar um
  cliente
- **THEN** a lista mostra as mensagens de todos os clientes do escritório
  em foco

#### Scenario: Usuário filtra por cliente

- **WHEN** o usuário seleciona um cliente no filtro
- **THEN** a lista é restrita às mensagens desse cliente

### Requirement: A página permite ler o texto de uma mensagem

A página de mensagens DET DEVE (MUST) permitir abrir uma mensagem da lista e
ler o seu texto completo, junto com cliente, assunto, remetente, data de
envio e prazo. Quando a mensagem não tem texto armazenado, a página DEVE
(MUST) dizer isso explicitamente, em vez de mostrar uma área vazia.

A página NÃO DEVE (MUST NOT) exibir a situação de leitura da mensagem.

#### Scenario: Usuário abre uma mensagem com texto

- **WHEN** o usuário aciona a leitura de uma mensagem que tem texto
- **THEN** o texto completo é exibido, preservando as quebras de linha

#### Scenario: Usuário abre uma mensagem sem texto

- **WHEN** o usuário aciona a leitura de uma mensagem sem texto armazenado
- **THEN** a página informa que o texto não foi capturado

#### Scenario: Lista sem a situação

- **WHEN** o usuário abre a página de mensagens
- **THEN** a lista não tem coluna de situação

### Requirement: A página oferece dois modos de visão das mensagens

A página de mensagens DET DEVE (MUST) oferecer um controle com exatamente dois botões — "Agrupado" e "Lista" — para alternar o modo de visão. O modo "Agrupado" DEVE (MUST) ser o padrão ao abrir a página. O controle DEVE (MUST) indicar qual modo está ativo de forma acessível (`aria-pressed`).

#### Scenario: Página aberta pela primeira vez

- **WHEN** o usuário abre a página de mensagens DET
- **THEN** a visão ativa é "Agrupado" e o botão "Agrupado" aparece como selecionado

#### Scenario: Usuário troca para a lista

- **WHEN** o usuário aciona o botão "Lista"
- **THEN** as mensagens passam a ser exibidas na tabela plana, uma linha por mensagem, e o botão "Lista" aparece como selecionado

#### Scenario: Usuário volta para o agrupado

- **WHEN** o usuário está na "Lista" e aciona "Agrupado"
- **THEN** as mensagens voltam a ser exibidas agrupadas por assunto

### Requirement: A visão agrupada reúne as mensagens por assunto

Na visão "Agrupado", a página DEVE (MUST) mostrar uma linha por assunto distinto, contendo o assunto, a quantidade de mensagens, a quantidade de clientes distintos e a data de envio mais recente do grupo. A comparação de assuntos DEVE (MUST) ignorar espaços nas pontas e diferença de maiúsculas/minúsculas. Mensagens sem assunto DEVEM (MUST) ser reunidas em um grupo "Sem assunto". Cada grupo DEVE (MUST) poder ser expandido para listar suas mensagens (cliente, envio, prazo) com a ação de ler a mensagem.

#### Scenario: Mesmo assunto em vários clientes

- **WHEN** três mensagens de três clientes diferentes têm o assunto "Aviso de pendência"
- **THEN** a visão agrupada mostra uma única linha "Aviso de pendência" com 3 mensagens e 3 clientes

#### Scenario: Assuntos que diferem só em caixa ou espaços

- **WHEN** duas mensagens têm os assuntos "Aviso de pendência" e " aviso de pendência "
- **THEN** elas pertencem ao mesmo grupo

#### Scenario: Mensagem sem assunto

- **WHEN** uma mensagem não tem assunto
- **THEN** ela aparece no grupo "Sem assunto"

#### Scenario: Expandir um grupo

- **WHEN** o usuário expande um grupo
- **THEN** são listadas as mensagens do grupo e cada uma pode ser aberta para leitura do texto

### Requirement: Filtro por cliente vale nos dois modos

O filtro por cliente DEVE (MUST) ser aplicado nos dois modos de visão, e a troca de modo NÃO DEVE (MUST NOT) limpar o filtro selecionado.

#### Scenario: Filtro com visão agrupada

- **WHEN** o usuário seleciona um cliente na visão "Agrupado"
- **THEN** os grupos e suas contagens refletem apenas as mensagens desse cliente

#### Scenario: Troca de modo mantém o filtro

- **WHEN** há um cliente filtrado e o usuário troca de "Agrupado" para "Lista"
- **THEN** a lista continua restrita a esse cliente

### Requirement: A página exibe a prioridade do assunto com cores de sinalização

A página de mensagens DET DEVE (MUST) exibir um selo com o nome do nível — "Alta", "Média" ou "Baixa" — nas cores de sinalização vermelho, amarelo e verde, respectivamente, obtidas de tokens do design system (nenhuma cor literal). O nível DEVE (MUST) sempre aparecer por texto além da cor. Assunto sem classificação DEVE (MUST) ser mostrado como "Sem prioridade", em estilo neutro. O selo DEVE (MUST) aparecer na linha do grupo da visão agrupada, em cada mensagem da lista plana e no modal de leitura, sempre com a prioridade do assunto da mensagem.

#### Scenario: Assunto de prioridade alta

- **WHEN** o assunto de um grupo tem prioridade Alta
- **THEN** a linha do grupo mostra o selo "Alta" em vermelho

#### Scenario: Assunto sem classificação

- **WHEN** o assunto não tem prioridade
- **THEN** a página mostra "Sem prioridade" em estilo neutro

#### Scenario: Lista plana e modal

- **WHEN** o usuário vê uma mensagem na lista plana ou abre a leitura dela
- **THEN** o selo exibido é o da prioridade do assunto dessa mensagem e não oferece edição

### Requirement: A classificação é feita por assunto, na linha do grupo

A página DEVE (MUST) oferecer o controle para definir a prioridade (Alta, Média, Baixa) ou limpá-la **somente na linha do grupo por assunto** da visão agrupada. A página NÃO DEVE (MUST NOT) oferecer classificação por mensagem individual. O controle DEVE (MUST) ser operável por teclado, indicar o nível atual de forma acessível e refletir imediatamente a mudança em todas as mensagens do assunto, inclusive na lista plana. Se a gravação falhar, a página DEVE (MUST) restaurar o nível anterior. Acionar o controle NÃO DEVE (MUST NOT) expandir ou recolher o grupo.

#### Scenario: Classificar um assunto

- **WHEN** o usuário escolhe "Alta" no controle da linha de um grupo
- **THEN** a prioridade do assunto é gravada e o selo do grupo passa a "Alta" em vermelho

#### Scenario: Reflexo na lista plana

- **WHEN** o usuário classifica um assunto e depois troca para a visão "Lista"
- **THEN** todas as mensagens desse assunto mostram o selo da nova prioridade

#### Scenario: Limpar a classificação

- **WHEN** o usuário escolhe limpar a prioridade de um assunto classificado
- **THEN** o grupo volta a "Sem prioridade"

#### Scenario: Falha ao gravar

- **WHEN** a gravação da prioridade falha
- **THEN** o selo volta ao nível anterior

#### Scenario: Controle não expande o grupo

- **WHEN** o usuário aciona o controle de prioridade de um grupo
- **THEN** o estado de expansão do grupo não muda

#### Scenario: Sem classificação por mensagem

- **WHEN** o usuário vê as mensagens expandidas de um grupo, a lista plana ou o modal de leitura
- **THEN** não há controle para alterar a prioridade da mensagem individual
