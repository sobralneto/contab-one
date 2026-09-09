## MODIFIED Requirements

### Requirement: Modelo de onboarding é uma entidade própria, com nome editável

O sistema DEVE (MUST) manter modelos de onboarding como entidade própria, cada um
com identificador e nome, e DEVE (MUST) permitir renomear um modelo sem afetar os
grupos, tarefas ou clientes ligados a ele. Cada modelo tem os próprios grupos de
tarefas, e cada grupo as próprias tarefas — um grupo pertence a exatamente um
modelo.

Um grupo tem nome, título, descrição e ordenação. Uma tarefa pertence a exatamente
um grupo e tem nome, ordenação e link da página do portal ou sistema.

#### Scenario: Listagem de modelos

- **WHEN** o usuário abre o cadastro de modelos de onboarding
- **THEN** são listados os modelos disponíveis para o escritório em foco, cada um
  com o nome e quantos grupos e tarefas tem

#### Scenario: Renomear modelo

- **WHEN** o administrador altera o nome de um modelo
- **THEN** o nome novo passa a valer em toda referência ao modelo, e os grupos,
  tarefas e clientes ligados a ele continuam intactos

### Requirement: O PDF apresenta o checklist inteiro, independente do estado da tela

O PDF DEVE (MUST) conter todos os grupos e todas as tarefas do checklist do
cliente, inclusive os grupos que estão recolhidos na tela no momento da
exportação. O que está aberto ou fechado é conveniência de leitura na tela e NÃO
DEVE (MUST NOT) alterar o documento exportado — quem imprime o checklist quer o
checklist, não o recorte que estava visível.

Cada tarefa DEVE (MUST) aparecer no PDF com o nome, o status (aberta ou
concluída), o link quando houver, os responsáveis atribuídos e a observação
escrita para aquele cliente. Tarefa concluída DEVE (MUST) trazer também o
momento da conclusão e quem concluiu, quando esses dados existirem. Cada grupo
DEVE (MUST) trazer o próprio título e quantas das suas tarefas estão
concluídas.

O documento exportado é um documento de leitura: os controles interativos da
página — a caixa de marcação, a seleção de responsáveis, o campo de observação,
o botão de recolher grupo, a navegação e qualquer aviso de erro — NÃO DEVEM
(MUST NOT) aparecer no PDF. O conteúdo que esses controles carregam aparece como
texto.

Uma observação que o usuário acabou de digitar e que ainda não terminou de ser
gravada DEVE (MUST) aparecer no PDF como está na tela: o documento reflete o
checklist que o usuário está vendo.

#### Scenario: Grupo recolhido entra no PDF

- **WHEN** o usuário recolhe um grupo e em seguida exporta o checklist
- **THEN** o PDF contém aquele grupo e todas as tarefas dele

#### Scenario: Tarefa com link, responsáveis e observação

- **WHEN** uma tarefa tem link cadastrado, tem responsáveis atribuídos e uma
  observação escrita
- **THEN** o PDF apresenta os três dados junto do nome da tarefa

#### Scenario: Tarefa concluída

- **WHEN** uma tarefa está concluída e há registro de quando e por quem
- **THEN** o PDF apresenta a tarefa como concluída, com o momento da conclusão e
  o nome de quem concluiu

#### Scenario: Tarefa sem link, sem responsável e sem observação

- **WHEN** uma tarefa não tem link, não tem responsável atribuído e não tem
  observação
- **THEN** o PDF apresenta a tarefa apenas com o nome e o status, sem campos
  vazios pendurados e sem erro

#### Scenario: Controles interativos ficam de fora

- **WHEN** o checklist é exportado
- **THEN** o PDF não contém caixa de marcação clicável, seleção de responsáveis,
  campo de observação editável, botão de recolher grupo nem link de navegação

#### Scenario: Observação recém-digitada

- **WHEN** o usuário digita uma observação e exporta antes de a gravação
  terminar
- **THEN** o PDF traz a observação como digitada

#### Scenario: Modelo sem tarefas

- **WHEN** o checklist exportado vem de um modelo sem nenhum grupo ou tarefa
- **THEN** o PDF é gerado assim mesmo, com o cabeçalho e a indicação de que não
  há tarefas, sem erro

## REMOVED Requirements

### Requirement: Tarefa exibe link e indicação de segundo fator

**Reason**: A indicação de "exige segundo fator" era uma flag por tarefa de
onboarding, fruto de um entendimento errado do pedido original. O dado de 2FA
é atributo do cliente (se o cliente tem 2FA habilitado no GOV.br), não de uma
tarefa específica do checklist, e passa a viver no cadastro do cliente.

**Migration**: A informação de 2FA agora vem do cadastro do cliente (ver
capability `gestao-clientes`) e é apresentada como aviso fixo na tela de
onboarding do cliente, acima do primeiro grupo de tarefas — não mais por
tarefa. Escritórios que hoje marcam tarefas como "exige 2FA" perdem essa
marcação; nenhuma migração automática de dado é feita entre a flag antiga (por
tarefa) e a nova (por cliente), que exige marcação própria no cadastro.

A página DEVE (MUST) apresentar, em cada tarefa que tenha link cadastrado, o acesso
à página correspondente, e DEVE (MUST) sinalizar visualmente a tarefa cujo site
exige segundo fator de autenticação.

#### Scenario: Tarefa com link e 2FA

- **WHEN** uma tarefa tem link cadastrado e está marcada como site com 2FA
- **THEN** a tarefa apresenta o acesso ao link e a indicação de segundo fator

#### Scenario: Tarefa sem link

- **WHEN** uma tarefa não tem link cadastrado
- **THEN** a tarefa é apresentada sem acesso a link, e nada quebra

## ADDED Requirements

### Requirement: Tarefa exibe link cadastrado

A página DEVE (MUST) apresentar, em cada tarefa que tenha link cadastrado, o
acesso à página correspondente.

#### Scenario: Tarefa com link

- **WHEN** uma tarefa tem link cadastrado
- **THEN** a tarefa apresenta o acesso ao link

#### Scenario: Tarefa sem link

- **WHEN** uma tarefa não tem link cadastrado
- **THEN** a tarefa é apresentada sem acesso a link, e nada quebra

### Requirement: A tela de onboarding do cliente avisa quando o cliente tem 2FA habilitado

A página de onboarding de um cliente DEVE (MUST) exibir, logo acima do
primeiro grupo de tarefas, um aviso com o texto "Cliente possui 2FA habilitado
para acesso ao site do GOV.br" quando o cadastro do cliente tiver a flag de
2FA marcada. Quando a flag não estiver marcada, o aviso NÃO DEVE (MUST NOT)
aparecer.

O aviso é fixo e não editável a partir da própria tela de onboarding — ele
reflete a flag do cadastro do cliente; para mudar o aviso, o usuário precisa
editar o cadastro do cliente.

#### Scenario: Cliente com 2FA habilitado

- **WHEN** o usuário abre a página de onboarding de um cliente cujo cadastro
  tem a flag de 2FA marcada
- **THEN** o aviso "Cliente possui 2FA habilitado para acesso ao site do
  GOV.br" aparece acima do primeiro grupo de tarefas

#### Scenario: Cliente sem 2FA habilitado

- **WHEN** o usuário abre a página de onboarding de um cliente cujo cadastro
  não tem a flag de 2FA marcada
- **THEN** nenhum aviso de 2FA aparece na página

#### Scenario: Cliente sem checklist criado

- **WHEN** o usuário abre a página de onboarding de um cliente com 2FA
  habilitado, mas ainda sem checklist criado
- **THEN** o aviso de 2FA aparece do mesmo jeito, independente de o checklist
  já existir
