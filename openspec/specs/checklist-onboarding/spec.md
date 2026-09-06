# checklist-onboarding Specification

## Purpose

Define o onboarding de clientes do escritório: modelos reutilizáveis de grupos e
tarefas, compartilhados entre os escritórios de um administrador, e o
acompanhamento por cliente — status, responsáveis, observação e percentual de
conclusão de cada tarefa.

## Requirements

### Requirement: Modelo de onboarding é uma entidade própria, com nome editável

O sistema DEVE (MUST) manter modelos de onboarding como entidade própria, cada um
com identificador e nome, e DEVE (MUST) permitir renomear um modelo sem afetar os
grupos, tarefas ou clientes ligados a ele. Cada modelo tem os próprios grupos de
tarefas, e cada grupo as próprias tarefas — um grupo pertence a exatamente um
modelo.

Um grupo tem nome, título, descrição e ordenação. Uma tarefa pertence a exatamente
um grupo e tem nome, ordenação, link da página do portal ou sistema, e indicação
de que esse site exige segundo fator de autenticação.

#### Scenario: Listagem de modelos

- **WHEN** o usuário abre o cadastro de modelos de onboarding
- **THEN** são listados os modelos disponíveis para o escritório em foco, cada um
  com o nome e quantos grupos e tarefas tem

#### Scenario: Renomear modelo

- **WHEN** o administrador altera o nome de um modelo
- **THEN** o nome novo passa a valer em toda referência ao modelo, e os grupos,
  tarefas e clientes ligados a ele continuam intactos

### Requirement: Modelo nasce vinculado a todos os escritórios do administrador

Ao criar (ou duplicar) um modelo, o sistema DEVE (MUST) vincular automaticamente
esse modelo a TODOS os escritórios em que o usuário administrador atuante tem
vínculo, sem exigir nenhuma ação adicional. Editar o modelo passa a valer para
todos os escritórios vinculados — não é preciso replicar a edição em cada um.

O sistema DEVE (MUST) tornar um modelo visível apenas a sessões focadas em algum
escritório vinculado a ele, e NÃO DEVE (MUST NOT) exibi-lo a uma sessão focada em
escritório sem vínculo com aquele modelo, mesmo autenticada.

O vínculo é um retrato do momento da criação: um escritório que o administrador
passe a gerenciar DEPOIS não ganha acesso retroativo a modelos antigos.

#### Scenario: Administrador de dois escritórios cria um modelo

- **WHEN** um administrador vinculado aos escritórios A e B cria um modelo
- **THEN** o modelo nasce vinculado a A e a B, e um outro usuário que administra
  apenas B também passa a enxergá-lo

#### Scenario: Modelo de escritório sem vínculo é invisível

- **WHEN** uma sessão cujo usuário não tem vínculo algum com o escritório B tenta
  ler ou alterar um modelo, grupo ou tarefa vinculados apenas a B, informando o
  identificador
- **THEN** o sistema responde como se o registro não existisse, e nada é alterado

### Requirement: Modelo pode ser replicado por inteiro

O sistema DEVE (MUST) permitir duplicar um modelo, criando um modelo novo com
cópia de todos os grupos e de todas as tarefas do original, preservando a
ordenação. A cópia DEVE (MUST) ser independente: alterar a cópia não afeta o
original, e vice-versa. A cópia também nasce vinculada aos escritórios do
administrador que a criou.

#### Scenario: Duplicar modelo com grupos e tarefas

- **WHEN** o administrador aciona a duplicação de um modelo que tem grupos e tarefas
- **THEN** um modelo novo é criado com os mesmos grupos e tarefas, e as tarefas da
  cópia são registros distintos dos do original

#### Scenario: Editar a cópia não afeta o original

- **WHEN** uma tarefa da cópia é alterada ou excluída
- **THEN** a tarefa correspondente do modelo original permanece como estava

### Requirement: Cadastro de grupos e tarefas é ato de administração

O sistema DEVE (MUST) exigir o papel `EscritorioAdmin` para criar, alterar,
reordenar e excluir grupos de tarefas e tarefas do modelo. Marcar, desmarcar e
anotar tarefas no checklist de um cliente DEVE (MUST) bastar o papel
`EscritorioUsuario`.

#### Scenario: Usuário comum tenta editar o modelo

- **WHEN** um `EscritorioUsuario` tenta criar, alterar ou excluir um grupo ou uma
  tarefa do modelo
- **THEN** o pedido é recusado por falta de permissão, e o modelo permanece intacto

#### Scenario: Usuário comum opera o checklist

- **WHEN** um `EscritorioUsuario` marca uma tarefa como concluída no checklist de
  um cliente
- **THEN** a marcação é aceita e persistida

### Requirement: Responsável é por cliente, não pelo modelo

O sistema DEVE (MUST) permitir atribuir zero, um ou vários responsáveis a cada
tarefa DENTRO do checklist de UM cliente — nunca à tarefa do modelo. A mesma
tarefa DEVE (MUST) poder ter responsáveis diferentes no checklist de clientes
diferentes, e alterar o responsável em um checklist NÃO DEVE (MUST NOT) afetar o
responsável da mesma tarefa em outro checklist.

O sistema DEVE (MUST) aceitar como responsável apenas usuário vinculado ao
escritório do cliente dono do checklist. A tela do checklist do cliente DEVE
(MUST) oferecer esses usuários em uma seleção múltipla, por tarefa, identificando
cada um pelo nome.

Vincular por identificador de usuário, e não por texto livre, é o que permite
mostrar o nome atual quando alguém é renomeado e o que impede atribuir tarefa a
quem não trabalha no escritório daquele cliente.

#### Scenario: Seleção de responsáveis no checklist do cliente

- **WHEN** o usuário abre o checklist de onboarding de um cliente
- **THEN** cada tarefa oferece uma seleção de responsáveis com os usuários
  vinculados ao escritório daquele cliente, apresentados pelo nome, permitindo
  escolher mais de um

#### Scenario: Mesma tarefa, responsáveis diferentes por cliente

- **WHEN** a tarefa X tem João como responsável no checklist do cliente A, e Ana
  como responsável no checklist do cliente B
- **THEN** os dois responsáveis coexistem sem conflito, cada um só no checklist do
  respectivo cliente

#### Scenario: Responsável de fora do escritório do cliente

- **WHEN** um responsável é atribuído a uma tarefa do checklist que não é usuário
  do escritório do cliente dono desse checklist
- **THEN** o pedido é recusado por validação, e o responsável não é gravado

#### Scenario: Usuário responsável é desvinculado do escritório

- **WHEN** um usuário que era responsável por tarefas em checklists de clientes
  deixa de ser vinculado ao escritório
- **THEN** os checklists continuam existindo, sem aquele responsável, e nenhuma
  marcação de tarefa é perdida

### Requirement: Checklist do cliente nasce por ação explícita do usuário

Um cliente NÃO DEVE (MUST NOT) ganhar checklist de onboarding automaticamente ao
ser cadastrado. O sistema DEVE (MUST) oferecer, na listagem de clientes, uma ação
para adicionar o checklist a um cliente que ainda não tem, e só a partir dessa ação
o checklist passa a existir para aquele cliente, vazio (todas as tarefas do modelo
abertas, percentual zero).

O sistema DEVE (MUST) exigir que o cliente já tenha um modelo de onboarding
escolhido antes de criar o checklist dele, e DEVE (MUST) recusar a criação quando
não houver modelo — não há o que montar.

O sistema DEVE (MUST) manter, para cada cliente, no máximo um checklist de
onboarding.

#### Scenario: Cliente com modelo mas sem checklist

- **WHEN** um cliente já tem modelo escolhido e ainda não tem checklist
- **THEN** a listagem de clientes oferece a ação de adicionar o checklist, e não a
  de abri-lo

#### Scenario: Usuário adiciona o checklist

- **WHEN** o usuário aciona a adição de checklist em um cliente que ainda não tem
- **THEN** um checklist é criado para aquele cliente, com todas as tarefas do
  modelo dele abertas e percentual zero, e a listagem passa a oferecer a ação de
  abri-lo

#### Scenario: Adicionar checklist já existente

- **WHEN** o usuário aciona a adição de checklist em um cliente que já tem um
- **THEN** o sistema não cria um segundo checklist para o mesmo cliente

#### Scenario: Cliente sem modelo escolhido

- **WHEN** é solicitada a criação do checklist de um cliente que não tem modelo
  escolhido
- **THEN** o pedido é recusado, e nenhum checklist é criado

### Requirement: Checklist é apresentado a partir do modelo ATUAL do cliente

O sistema DEVE (MUST) apresentar o checklist de um cliente a partir do modelo
escolhido para ELE: todo grupo e toda tarefa daquele modelo — e somente daquele —
aparecem no checklist. Tarefas de outros modelos NÃO DEVEM (MUST NOT) aparecer.

O modelo considerado é sempre o vigente no momento da leitura: trocar o modelo do
cliente muda o que o checklist mostra.

O checklist guarda, por tarefa, o status (aberto ou concluído), a observação
escrita pelo usuário e o momento da conclusão. Tarefa que ninguém tocou DEVE
(MUST) valer como aberta, sem exigir registro prévio.

#### Scenario: Só as tarefas do modelo do cliente aparecem

- **WHEN** existem dois modelos com tarefas distintas e o cliente usa apenas um deles
- **THEN** o checklist mostra somente as tarefas do modelo do cliente

#### Scenario: Tarefa nova entra no modelo depois

- **WHEN** o administrador acrescenta uma tarefa a um modelo
- **THEN** essa tarefa passa a aparecer, aberta, no checklist de todos os clientes
  que usam aquele modelo, e as marcações já existentes são preservadas

#### Scenario: Checklist de cliente de outro escritório

- **WHEN** uma sessão do escritório A pede o checklist de um cliente do escritório B
- **THEN** o sistema responde como se o cliente não existisse

#### Scenario: Página aberta antes de o checklist existir

- **WHEN** a página de onboarding de um cliente com modelo, mas sem checklist, é
  aberta diretamente (por link salvo ou URL digitada)
- **THEN** a página oferece a ação de criar o checklist, em vez de apresentar
  progresso ou tarefas

#### Scenario: Página aberta para cliente sem modelo

- **WHEN** a página de onboarding de um cliente sem modelo escolhido é aberta
- **THEN** a página informa que falta escolher um modelo na edição do cliente, em
  vez de oferecer a criação do checklist

### Requirement: Marcar e desmarcar tarefa atualiza o percentual persistido

O sistema DEVE (MUST) permitir alternar o status de cada tarefa do checklist entre
aberto e concluído, e DEVE (MUST) recalcular e persistir, no checklist do cliente,
o percentual de conclusão a cada alternância — para cima ao concluir, para baixo ao
desmarcar.

O percentual é a razão entre tarefas concluídas e o total de tarefas do modelo no
momento do cálculo. Checklist sem nenhuma tarefa no modelo DEVE (MUST) resultar em
percentual zero, e NÃO DEVE (MUST NOT) produzir erro.

#### Scenario: Conclusão de tarefa

- **WHEN** o usuário marca uma tarefa aberta como concluída
- **THEN** o status da tarefa passa a concluído, o percentual gravado no checklist
  do cliente aumenta, e o valor exibido acompanha

#### Scenario: Desmarcação de tarefa

- **WHEN** o usuário desmarca uma tarefa concluída
- **THEN** o status volta a aberto, o percentual gravado diminui, e o valor exibido
  acompanha

#### Scenario: Modelo sem tarefas

- **WHEN** o checklist de um cliente é aberto em um escritório cujo modelo não tem
  nenhuma tarefa
- **THEN** o percentual é zero e a página é apresentada sem erro

#### Scenario: Tarefa removida do modelo

- **WHEN** o administrador exclui do modelo uma tarefa que estava concluída em
  checklists de clientes
- **THEN** essa tarefa deixa de contar em qualquer checklist, e o percentual de cada
  cliente afetado passa a refletir o total restante

### Requirement: A página apresenta progresso antes das tarefas

A página de onboarding de um cliente DEVE (MUST) apresentar, no topo, um indicador
circular com o percentual de conclusão, e, antes do primeiro grupo, uma barra de
progresso informando quantas tarefas estão marcadas e quantas faltam para concluir.
Os dois DEVEM (MUST) refletir imediatamente cada marcação e desmarcação, sem exigir
recarga da página.

#### Scenario: Marcação reflete nos dois indicadores

- **WHEN** o usuário marca uma tarefa como concluída
- **THEN** o círculo de percentual e a barra de progresso são atualizados na hora,
  e a contagem de marcadas e faltantes acompanha

#### Scenario: Título de tarefa concluída

- **WHEN** uma tarefa está com status concluído
- **THEN** o título dela é apresentado riscado, distinguindo-a das abertas

### Requirement: Tarefa exibe link e indicação de segundo fator

A página DEVE (MUST) apresentar, em cada tarefa que tenha link cadastrado, o acesso
à página correspondente, e DEVE (MUST) sinalizar visualmente a tarefa cujo site
exige segundo fator de autenticação.

#### Scenario: Tarefa com link e 2FA

- **WHEN** uma tarefa tem link cadastrado e está marcada como site com 2FA
- **THEN** a tarefa apresenta o acesso ao link e a indicação de segundo fator

#### Scenario: Tarefa sem link

- **WHEN** uma tarefa não tem link cadastrado
- **THEN** a tarefa é apresentada sem acesso a link, e nada quebra

### Requirement: Observação por tarefa é do cliente, não do modelo

O sistema DEVE (MUST) guardar a observação de uma tarefa no checklist do cliente,
e NÃO DEVE (MUST NOT) propagá-la para o checklist de outro cliente nem para o
modelo do escritório.

#### Scenario: Observação em um cliente

- **WHEN** o usuário escreve uma observação em uma tarefa do checklist do cliente A
- **THEN** a observação aparece apenas no checklist do cliente A, e a mesma tarefa
  no checklist do cliente B continua sem observação

### Requirement: Exclusão de grupo alerta sobre o efeito nos clientes

O sistema DEVE (MUST) informar, antes de excluir um grupo do modelo, quantas
tarefas serão removidas junto e que isso altera o percentual de todos os clientes,
e DEVE (MUST) exigir confirmação explícita.

#### Scenario: Confirmação antes de excluir grupo

- **WHEN** o administrador aciona a exclusão de um grupo que contém tarefas
- **THEN** o sistema pede confirmação informando o efeito sobre os checklists, e só
  exclui depois da confirmação

#### Scenario: Exclusão de grupo remove as tarefas dele

- **WHEN** a exclusão de um grupo é confirmada
- **THEN** o grupo e suas tarefas deixam de existir, junto com os registros de
  status e observação daquelas tarefas em todos os checklists

### Requirement: "Cliente em fase de onboarding" é uma definição única

O sistema DEVE (MUST) considerar em fase de onboarding o cliente que tem modelo
de onboarding escolhido e cujo onboarding ainda não chegou a 100% — o que inclui
tanto o cliente cujo checklist ainda não foi criado quanto o cliente com
checklist abaixo de 100%. Cliente sem modelo escolhido NÃO DEVE (MUST NOT) ser
considerado em onboarding, porque não há o que implantar.

A definição DEVE (MUST) ser uma só, aplicada por igual em todo lugar que a use —
filtro de listagem, contagem de indicador ou qualquer consumidor futuro. Duas
definições que divirjam produzem um número de indicador que não bate com o
tamanho da lista que o usuário abre em seguida, e o usuário não tem como saber
qual das duas está certa.

O conjunto DEVE (MUST) respeitar o isolamento por escritório como qualquer outra
leitura de cliente: uma sessão só enxerga em onboarding os clientes do próprio
escritório.

#### Scenario: Cliente com modelo e sem checklist

- **WHEN** um cliente tem modelo de onboarding escolhido e ainda não teve o
  checklist criado
- **THEN** ele é considerado em fase de onboarding

#### Scenario: Cliente com checklist em andamento

- **WHEN** um cliente tem checklist com percentual de conclusão abaixo de 100
- **THEN** ele é considerado em fase de onboarding

#### Scenario: Cliente com onboarding concluído

- **WHEN** o percentual de conclusão do checklist de um cliente chega a 100
- **THEN** ele deixa de ser considerado em fase de onboarding

#### Scenario: Cliente sem modelo escolhido

- **WHEN** um cliente não tem modelo de onboarding escolhido
- **THEN** ele não é considerado em fase de onboarding, independentemente de
  qualquer outro dado

#### Scenario: Conclusão de tarefa muda a classificação na hora

- **WHEN** a última tarefa aberta do checklist de um cliente é marcada como
  concluída
- **THEN** o cliente deixa de aparecer entre os que estão em onboarding, sem
  depender de nenhum processamento posterior

#### Scenario: Cliente em onboarding de outro escritório

- **WHEN** uma sessão do escritório A consulta clientes em onboarding e o
  escritório B tem clientes nessa situação
- **THEN** os clientes de B não aparecem nem são contados

### Requirement: O hub lista os clientes em onboarding com o progresso de cada um

O hub DEVE (MUST) apresentar os clientes em fase de onboarding do escopo da
sessão, cada um com o nome e o percentual de conclusão do próprio checklist,
representado também de forma visual (barra de progresso) além do número.

O lugar é o hub, e NÃO a visão geral de uma ferramenta: onboarding é do cliente,
não de ferramenta alguma. Na visão geral de uma ferramenta, o escritório que não
usa aquela ferramenta nunca veria a informação.

Cliente com modelo escolhido e sem checklist criado DEVE (MUST) aparecer com 0%
— está em onboarding e não começou. A ordem DEVE (MUST) ser por progresso
decrescente, e não alfabética: quem está mais perto do fim é onde um empurrão
encerra a implantação.

A lista DEVE (MUST) ser limitada a poucos clientes para não dominar a tela
inicial, e, quando houver mais do que o exibido, DEVE (MUST) informar quantos
existem ao todo e oferecer caminho para a lista completa já filtrada por
onboarding. Não havendo truncamento, a informação de quantidade NÃO DEVE (MUST
NOT) ser exibida.

Cada cliente listado DEVE (MUST) dar acesso ao próprio checklist.

Não havendo nenhum cliente em onboarding, o hub DEVE (MUST) dizer isso
explicitamente — é uma boa notícia, não um erro nem um espaço vazio. Falhando a
carga, o cartão DEVE (MUST) sinalizar a falha sem derrubar o restante do hub,
como as demais colunas.

#### Scenario: Escritório com implantações em curso

- **WHEN** o usuário abre o hub e o escritório tem clientes em fase de onboarding
- **THEN** cada um aparece com o nome, o percentual e a barra de progresso
  correspondente

#### Scenario: Cliente que ainda não começou

- **WHEN** um cliente tem modelo escolhido e nenhum checklist criado
- **THEN** ele aparece na lista com 0%

#### Scenario: Ordem por progresso

- **WHEN** a lista tem clientes com percentuais diferentes
- **THEN** eles são apresentados do maior percentual para o menor,
  independentemente do nome

#### Scenario: Mais clientes do que o hub exibe

- **WHEN** há mais clientes em onboarding do que o hub apresenta
- **THEN** o hub informa quantos estão sendo exibidos de quantos existem, e
  oferece caminho para a listagem completa já filtrada

#### Scenario: Lista que cabe inteira

- **WHEN** todos os clientes em onboarding cabem na lista do hub
- **THEN** nenhuma informação de truncamento é exibida

#### Scenario: Acesso ao checklist a partir do hub

- **WHEN** o usuário aciona um cliente da lista
- **THEN** a aplicação abre o checklist de onboarding daquele cliente

#### Scenario: Escritório que não usa NFS-e

- **WHEN** o escritório em foco não tem a ferramenta de NFS-e contratada
- **THEN** a lista de onboarding continua visível no hub

#### Scenario: Nenhum cliente em onboarding

- **WHEN** nenhum cliente do escopo está em fase de onboarding
- **THEN** o hub informa que não há cliente em implantação, em vez de exibir um
  espaço vazio

#### Scenario: Falha ao carregar

- **WHEN** a carga da lista falha
- **THEN** o cartão sinaliza a falha e o restante do hub continua de pé

#### Scenario: Coerência com a listagem

- **WHEN** o usuário abre a listagem de clientes a partir do hub
- **THEN** a listagem já vem filtrada por onboarding, e o conjunto exibido é o
  mesmo que originou a lista do hub
