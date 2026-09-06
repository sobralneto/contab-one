## ADDED Requirements

### Requirement: O código do cliente é editável depois do cadastro

O sistema DEVE (MUST) permitir alterar o código de um cliente já cadastrado, pela
mesma tela e pelo mesmo pedido que alteram os demais campos, e DEVE (MUST)
persistir o código novo.

O código é a chave que o escritório usa para casar o cliente com as próprias
pastas. Sem edição, um dígito errado no cadastro só se corrige excluindo e
recriando o cliente — o que descarta junto o checklist de onboarding e o
histórico de execuções daquele cliente.

A alteração DEVE (MUST) obedecer à mesma unicidade por escritório que vale no
cadastro: dois clientes do mesmo escritório não podem ficar com o mesmo código.
O sistema DEVE (MUST) recusar a alteração que colida com o código de OUTRO
cliente do escritório, indicando o conflito, e NÃO DEVE (MUST NOT) tratar como
conflito o pedido que mantém o código que o próprio cliente já tem. Código vazio
DEVE (MUST) ser recusado por validação, como no cadastro.

Alterar o código NÃO DEVE (MUST NOT) afetar nenhum outro dado do cliente — o
checklist de onboarding, as execuções e as métricas continuam apontando para o
mesmo cliente.

O código é também a chave pela qual o agente reconhece o cliente na
sincronização, e o agente a deriva do nome do arquivo do certificado na máquina
do escritório. Por isso, ao editar um cliente cuja origem é o agente, o sistema
DEVE (MUST) avisar, na própria tela, que mudar o código sem renomear o
certificado correspondente faz a próxima sincronização cadastrar o cliente
de novo sob o código antigo. O aviso NÃO DEVE (MUST NOT) impedir a alteração:
renomear os dois lados é exatamente o caso de uso que justifica a edição.

#### Scenario: Alteração para um código livre

- **WHEN** o usuário edita um cliente e informa um código ainda não usado no
  escritório
- **THEN** o código novo é gravado e passa a aparecer na listagem

#### Scenario: Alteração para um código já usado

- **WHEN** o usuário edita um cliente e informa um código que já pertence a outro
  cliente do mesmo escritório
- **THEN** a gravação é recusada indicando o conflito, e o cliente permanece com o
  código que tinha

#### Scenario: Gravação mantendo o próprio código

- **WHEN** o usuário salva a edição de um cliente sem mexer no código
- **THEN** a gravação é aceita normalmente, sem acusar conflito com ele mesmo

#### Scenario: Código igual ao de cliente de outro escritório

- **WHEN** o usuário edita um cliente e informa um código que já é usado por um
  cliente de OUTRO escritório
- **THEN** a gravação é aceita, porque a unicidade é por escritório

#### Scenario: Código vazio

- **WHEN** o usuário tenta salvar a edição com o código em branco
- **THEN** a gravação é recusada por validação, e o cliente permanece como estava

#### Scenario: Aviso ao editar cliente de origem agente

- **WHEN** o usuário abre a edição de um cliente cuja origem é o agente
- **THEN** o campo de código é editável e acompanhado do aviso de que o
  certificado na máquina do escritório precisa ser renomeado junto

#### Scenario: Vínculos preservados

- **WHEN** o código de um cliente que já tem checklist de onboarding é alterado
- **THEN** o checklist continua sendo o mesmo daquele cliente, agora exibido sob o
  código novo

### Requirement: A listagem de clientes filtra por quem está em onboarding

A tela de clientes DEVE (MUST) oferecer um filtro que restrinja a listagem aos
clientes em fase de onboarding, conforme a definição única de
[[checklist-onboarding]]. O filtro DEVE (MUST) estar disponível para todos os
papéis que enxergam a listagem, e não apenas para administradores.

O filtro DEVE (MUST) combinar com os demais controles da tela — busca por texto,
escritório e vencimento de certificado — restringindo o resultado a quem atende a
todos ao mesmo tempo, e a paginação e o total exibido DEVEM (MUST) refletir o
conjunto filtrado, não o conjunto inteiro.

Estando desligado, o filtro NÃO DEVE (MUST NOT) alterar a listagem: a tela abre
mostrando todos os clientes, como hoje.

#### Scenario: Filtrar por clientes em onboarding

- **WHEN** o usuário liga o filtro de onboarding na tela de clientes
- **THEN** a listagem passa a exibir apenas os clientes em fase de onboarding, e o
  total exibido acompanha

#### Scenario: Filtro desligado

- **WHEN** o usuário não liga o filtro de onboarding
- **THEN** a listagem exibe todos os clientes do escopo, em onboarding ou não

#### Scenario: Filtro combinado com a busca

- **WHEN** o usuário digita um termo de busca e liga o filtro de onboarding
- **THEN** a listagem exibe apenas os clientes que atendem ao termo E estão em
  onboarding

#### Scenario: Filtro na visão de administrador

- **WHEN** um administrador liga o filtro de onboarding e também escolhe um
  escritório no filtro de escritório
- **THEN** a listagem exibe apenas os clientes em onboarding daquele escritório

#### Scenario: Nenhum cliente em onboarding

- **WHEN** o usuário liga o filtro de onboarding e nenhum cliente do escopo está
  nessa situação
- **THEN** a tela apresenta o estado vazio, sem erro
