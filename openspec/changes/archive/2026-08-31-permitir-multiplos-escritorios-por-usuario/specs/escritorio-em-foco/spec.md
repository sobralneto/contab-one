## ADDED Requirements

### Requirement: A sessão tem sempre um escritório em foco declarado

O sistema DEVE (MUST) tratar o escopo de tenant de um pedido como o **escritório em foco
declarado na credencial daquela sessão**, e NÃO DEVE (MUST NOT) derivá-lo do cadastro do
usuário no momento do pedido.

O foco é escolhido quando o acesso é emitido — no login ou na troca de foco — e vale até o
acesso seguinte. Um usuário vinculado a três escritórios tem, em cada instante, exatamente
um em foco.

`PlatformAdmin` PODE (MAY) operar sem foco; nesse estado ele enxerga todos os escritórios,
como já acontece hoje.

#### Scenario: Usuário de um só escritório entra

- **WHEN** um usuário vinculado a um único escritório faz login
- **THEN** o acesso é emitido com aquele escritório em foco, sem nenhuma escolha pedida ao
  usuário

#### Scenario: Usuário de vários escritórios entra

- **WHEN** um usuário vinculado a mais de um escritório faz login
- **THEN** o acesso é emitido já com um escritório em foco, e o usuário chega à aplicação
  operando dentro dele

#### Scenario: PlatformAdmin entra

- **WHEN** um `PlatformAdmin` sem vínculo nenhum faz login
- **THEN** o acesso é emitido sem escritório em foco, e ele enxerga os dados de todos os
  escritórios

### Requirement: O foco é validado contra os vínculos a cada emissão

O sistema DEVE (MUST) verificar, toda vez que emite um acesso — login, renovação ou troca
de foco —, que o escritório pedido para foco está entre os que aquele usuário pode
enxergar, e DEVE (MUST) recusar a emissão quando não estiver.

A verificação DEVE (MUST) consultar o estado atual dos vínculos, não o que a credencial
anterior afirmava — do contrário, revogar um vínculo não teria efeito enquanto a sessão
seguisse se renovando.

#### Scenario: Renovação após perda do vínculo em foco

- **WHEN** um vínculo é removido e a sessão que estava com aquele escritório em foco tenta
  renovar o acesso
- **THEN** a renovação é recusada, e a sessão termina

#### Scenario: Troca para escritório sem vínculo

- **WHEN** um usuário pede foco em um escritório ao qual não está vinculado
- **THEN** o pedido é recusado e a credencial anterior segue valendo, com o foco anterior
  intacto

#### Scenario: Foco em escritório inativo

- **WHEN** um usuário pede foco em um escritório vinculado cujo status não permite
  operação
- **THEN** o pedido é recusado com a indicação do status, e o foco anterior é mantido

### Requirement: A troca de foco não exige novo login

O sistema DEVE (MUST) oferecer uma operação que troque o escritório em foco da sessão
corrente, reemitindo o acesso com o novo foco e mantendo a sessão viva. O usuário NÃO DEVE
(MUST NOT) precisar sair e entrar de novo para atender outro escritório.

#### Scenario: Usuário troca de escritório

- **WHEN** um usuário vinculado a A e B, operando em A, pede foco em B
- **THEN** um novo acesso é emitido com B em foco, a sessão continua a mesma, e a partir
  daí apenas dados de B são lidos e gravados

#### Scenario: Credencial anterior após a troca

- **WHEN** um acesso emitido antes da troca é apresentado depois dela
- **THEN** ele continua escopado ao escritório antigo até vencer, e nunca ao novo

### Requirement: A sessão sabe listar os escritórios que pode focar

O sistema DEVE (MUST) permitir que a sessão obtenha a lista dos escritórios que aquele
usuário pode colocar em foco, com nome e identificação de cada um, e a indicação de qual
está em foco no momento.

Para `PlatformAdmin` a lista DEVE (MUST) conter todos os escritórios, mais a opção de
operar sem foco.

#### Scenario: Usuário de dois escritórios pede a lista

- **WHEN** um usuário vinculado a A e B, operando em A, pede a lista
- **THEN** a resposta traz A e B, com A marcado como o foco atual

#### Scenario: Usuário de um escritório pede a lista

- **WHEN** um usuário vinculado a um único escritório pede a lista
- **THEN** a resposta traz apenas aquele escritório, marcado como o foco atual

#### Scenario: PlatformAdmin pede a lista

- **WHEN** um `PlatformAdmin` pede a lista
- **THEN** a resposta traz todos os escritórios da plataforma e a opção de nenhum foco

### Requirement: A barra superior mostra o escritório em foco

O sistema DEVE (MUST) exibir, na barra superior da área autenticada, o nome do escritório
em foco da sessão, de modo que o usuário nunca precise deduzir em qual escritório está
operando.

Quando a sessão tiver mais de uma opção de foco, o indicador DEVE (MUST) oferecer a troca.
Quando tiver apenas uma, ele DEVE (MUST) exibir só o nome, sem controle acionável — um
seletor de uma opção só é ruído.

Para `PlatformAdmin` sem foco, o indicador DEVE (MUST) deixar explícito que a visão é de
todos os escritórios, e NÃO DEVE (MUST NOT) ficar em branco.

#### Scenario: Usuário de vários escritórios

- **WHEN** um usuário vinculado a mais de um escritório está na aplicação
- **THEN** a barra superior mostra o nome do escritório em foco e oferece a troca para os
  demais

#### Scenario: Usuário de um só escritório

- **WHEN** um usuário vinculado a um único escritório está na aplicação
- **THEN** a barra superior mostra o nome daquele escritório sem oferecer troca

#### Scenario: PlatformAdmin sem foco

- **WHEN** um `PlatformAdmin` está operando sem escritório em foco
- **THEN** a barra superior indica a visão de todos os escritórios e oferece focar um deles

#### Scenario: Escritório em foco antes do nome chegar

- **WHEN** a sessão está confirmada e o nome do escritório em foco ainda não foi resolvido
- **THEN** o indicador exibe um estado de carregamento no lugar do nome, e não exibe nome
  de escritório algum de sessão anterior

### Requirement: A troca de foco recomeça a tela no escritório novo

O sistema DEVE (MUST) descartar, ao trocar o foco, o catálogo de ferramentas e os dados
carregados do escritório anterior, e DEVE (MUST) recarregá-los a partir do novo foco antes
de exibir qualquer número.

Nenhum dado do escritório anterior PODE (MAY) permanecer visível depois da troca. Uma tela
que mistura número de dois escritórios é pior do que uma tela vazia.

#### Scenario: Troca com uma listagem aberta

- **WHEN** o usuário está com uma listagem de clientes do escritório A na tela e troca o
  foco para B
- **THEN** a listagem passa a mostrar os clientes de B, sem exibir nenhuma linha de A em
  momento algum

#### Scenario: Troca para escritório com outras ferramentas contratadas

- **WHEN** o usuário troca o foco para um escritório com contratação de ferramentas
  diferente
- **THEN** o menu lateral e a página inicial passam a refletir o catálogo do novo
  escritório, sem item remanescente do anterior

#### Scenario: Troca estando dentro de ferramenta não contratada pelo destino

- **WHEN** o usuário está numa página de uma ferramenta e troca para um escritório que não
  contratou aquela ferramenta
- **THEN** a aplicação o leva à página inicial do novo escritório, e nenhuma requisição de
  dado daquela ferramenta é disparada

#### Scenario: Falha na troca

- **WHEN** a troca de foco falha
- **THEN** a sessão permanece no escritório anterior com os dados que já tinha, a falha é
  sinalizada, e o usuário não é levado à tela de login
