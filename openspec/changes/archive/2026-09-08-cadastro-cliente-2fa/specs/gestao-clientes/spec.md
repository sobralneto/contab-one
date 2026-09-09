## ADDED Requirements

### Requirement: O cadastro do cliente registra se tem 2FA habilitado no GOV.br

O sistema DEVE (MUST) manter, para cada cliente, uma flag booleana indicando se
o cliente tem o segundo fator de autenticação (2FA) habilitado para acesso ao
site do GOV.br. O cadastro e a edição de cliente DEVEM (MUST) oferecer um
controle para marcar ou desmarcar essa flag. Cliente novo, sem escolha
explícita, NASCE (MUST) com a flag desmarcada.

#### Scenario: Cadastro marcando 2FA habilitado

- **WHEN** o usuário marca a opção de 2FA ao cadastrar um cliente e salva
- **THEN** o cliente é criado com a flag de 2FA habilitada

#### Scenario: Cadastro sem marcar 2FA

- **WHEN** o usuário cadastra um cliente sem marcar a opção de 2FA
- **THEN** o cliente é criado com a flag de 2FA desabilitada

#### Scenario: Alterar a flag na edição

- **WHEN** o usuário edita um cliente e altera a marcação de 2FA
- **THEN** a mudança é salva e passa a valer em toda referência ao cliente,
  inclusive na listagem e no onboarding

### Requirement: A listagem de clientes exibe se o cliente tem 2FA habilitado

A tela de clientes DEVE (MUST) exibir, em coluna própria chamada "2FA", se cada
cliente tem o segundo fator de autenticação habilitado no GOV.br, com o texto
"Sim" quando a flag estiver marcada e "Não" quando não estiver. A coluna vale
para **todos os papéis** que enxergam a listagem: a flag é atributo da
empresa, não do papel de quem olha.

#### Scenario: Cliente com 2FA habilitado

- **WHEN** o usuário vê na listagem um cliente com a flag de 2FA marcada
- **THEN** a coluna "2FA" mostra "Sim"

#### Scenario: Cliente sem 2FA habilitado

- **WHEN** o usuário vê na listagem um cliente com a flag de 2FA desmarcada
- **THEN** a coluna "2FA" mostra "Não"

#### Scenario: Coluna visível para o administrador

- **WHEN** um administrador de plataforma abre a tela de clientes
- **THEN** a coluna "2FA" aparece para ele como para os demais papéis

### Requirement: A listagem de clientes filtra por 2FA habilitado

A tela de clientes DEVE (MUST) oferecer um controle para restringir a listagem
aos clientes com 2FA habilitado, ou aos clientes sem 2FA habilitado. Sem
escolha, a listagem NÃO DEVE (MUST NOT) ser restringida por essa flag.

O filtro DEVE (MUST) estar disponível para **todos os papéis** que enxergam a
listagem, e DEVE (MUST) combinar com os demais controles da tela — busca,
escritório, certificado, regime tributário e onboarding —, restringindo o
resultado a quem atende a todos ao mesmo tempo. A paginação e o total exibido
DEVEM (MUST) refletir o conjunto filtrado, e a escolha DEVE (MUST) levar de
volta à primeira página.

#### Scenario: Filtrar por quem tem 2FA

- **WHEN** o usuário escolhe o filtro "Sim" para 2FA
- **THEN** a listagem exibe apenas os clientes com a flag de 2FA marcada, e o
  total exibido acompanha

#### Scenario: Filtrar por quem não tem 2FA

- **WHEN** o usuário escolhe o filtro "Não" para 2FA
- **THEN** a listagem exibe apenas os clientes com a flag de 2FA desmarcada

#### Scenario: Filtro desligado

- **WHEN** o usuário não escolhe filtro de 2FA
- **THEN** a listagem exibe todos os clientes do escopo, com e sem 2FA
  habilitado

#### Scenario: Filtro combinado com a busca

- **WHEN** o usuário digita um termo de busca e escolhe um filtro de 2FA
- **THEN** a listagem exibe apenas os clientes que atendem ao termo E ao
  filtro de 2FA

#### Scenario: Filtro disponível para o administrador

- **WHEN** um administrador de plataforma abre a tela de clientes
- **THEN** o filtro de 2FA está disponível para ele como para os demais
  papéis, e combina com o filtro de escritório

#### Scenario: Troca de filtro volta à primeira página

- **WHEN** o usuário está numa página adiante e escolhe um filtro de 2FA
- **THEN** a listagem volta para a primeira página do conjunto filtrado
