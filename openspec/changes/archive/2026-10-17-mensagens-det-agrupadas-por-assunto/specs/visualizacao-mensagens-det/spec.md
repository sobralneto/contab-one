## ADDED Requirements

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
