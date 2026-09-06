## MODIFIED Requirements

### Requirement: Filtro por vencimento de certificado na visão escritório

Na tela de clientes, o sistema DEVE (MUST) oferecer um controle único para
filtrar por situação do certificado digital, disponível para **todos os papéis
que enxergam a listagem** — não apenas para a visão escritório. Vencimento de
certificado é assunto do cliente, não do papel de quem olha; e o painel oferece
essas contagens a todo mundo, então restringir o filtro a um papel deixaria
parte dos usuários sem como chegar ao que o painel mostrou.

O controle DEVE (MUST) oferecer exatamente as **mesmas três faixas que o painel
conta**, com os mesmos limites e os mesmos rótulos:

- **vencidos**, cujo certificado tem validade anterior a hoje;
- **vencendo em até 3 dias**;
- **vencendo de 4 a 30 dias**.

Um vocabulário só nas duas telas: quem lê uma contagem no painel e abre a
listagem reencontra o mesmo rótulo no seletor, em vez de ter de traduzir a faixa
para um período em dias. Os períodos avulsos que o controle oferecia antes (1,
2, 7 e 15 dias) saem — eram uma segunda maneira de dizer a mesma coisa, sem
correspondência com nada que o painel mostre.

As opções DEVEM (MUST) ser mutuamente exclusivas: escolher uma substitui a
anterior. Sem escolha alguma, a listagem NÃO DEVE (MUST NOT) ser restringida por
certificado.

O filtro DEVE (MUST) combinar com os demais controles da tela — busca,
escritório e onboarding —, restringindo o resultado a quem atende a todos ao
mesmo tempo, e a paginação e o total exibido DEVEM (MUST) refletir o conjunto
filtrado.

As três faixas DEVEM (MUST) ser as **mesmas** que o painel conta em seus
indicadores, de modo que abrir a listagem a partir de uma contagem produza
exatamente aquele conjunto.

#### Scenario: Filtro de vencendo em até 3 dias

- **WHEN** o usuário seleciona "vencendo em até 3 dias"
- **THEN** a tabela exibe apenas clientes cujo certificado vence de hoje até o
  terceiro dia, inclusive

#### Scenario: As faixas são as do painel

- **WHEN** o usuário abre o seletor de certificado
- **THEN** as opções oferecidas são exatamente as três faixas que o painel conta,
  e nenhum período avulso

#### Scenario: Filtro de vencidos

- **WHEN** o usuário seleciona "vencidos" no filtro de certificado
- **THEN** a tabela exibe apenas clientes cujo certificado já venceu, e nenhum
  cujo certificado ainda esteja válido

#### Scenario: Filtro da faixa de 4 a 30 dias

- **WHEN** o usuário seleciona a faixa de 4 a 30 dias
- **THEN** a tabela exibe apenas clientes cujo certificado vence nesse intervalo,
  excluindo os que vencem nos próximos 3 dias e os que vencem depois de 30

#### Scenario: Filtro disponível para o administrador

- **WHEN** um administrador de plataforma abre a tela de clientes
- **THEN** o filtro de certificado está disponível para ele como para os demais
  papéis, e é aplicado ao resultado

#### Scenario: Cliente sem certificado

- **WHEN** qualquer faixa de certificado está selecionada
- **THEN** clientes sem validade de certificado registrada não aparecem

#### Scenario: Usuário limpa filtro de vencimento

- **WHEN** o usuário remove o filtro de vencimento de certificado
- **THEN** a tabela volta a exibir todos os clientes do escopo

### Requirement: A listagem de clientes filtra por quem está em onboarding

A tela de clientes DEVE (MUST) oferecer um filtro que restrinja a listagem aos
clientes em fase de onboarding, conforme a definição única de
[[checklist-onboarding]]. O filtro DEVE (MUST) estar disponível para todos os
papéis que enxergam a listagem, e não apenas para administradores.

O filtro DEVE (MUST) combinar com os demais controles da tela — busca por texto,
escritório e situação do certificado — restringindo o resultado a quem atende a
todos ao mesmo tempo, e a paginação e o total exibido DEVEM (MUST) refletir o
conjunto filtrado, não o conjunto inteiro.

Estando desligado, o filtro NÃO DEVE (MUST NOT) alterar a listagem: a tela abre
mostrando todos os clientes, como hoje.

A tela DEVE (MUST) aceitar que a escolha de filtro venha do endereço, para que
um indicador do painel possa abrir a listagem já filtrada pelo conjunto que ele
contou.

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

#### Scenario: Filtro vindo do endereço

- **WHEN** a tela de clientes é aberta por um endereço que já indica uma faixa de
  certificado ou o onboarding
- **THEN** a listagem abre com aquele filtro aplicado e o controle correspondente
  refletindo a escolha

#### Scenario: Nenhum cliente em onboarding

- **WHEN** o usuário liga o filtro de onboarding e nenhum cliente do escopo está
  nessa situação
- **THEN** a tela apresenta o estado vazio, sem erro
