# vinculo-usuario-escritorios Specification

## Purpose

Quem pode ver quais escritórios — como um usuário é vinculado a zero, um ou vários escritórios, quem administra esses vínculos e o que acontece quando o último vínculo é removido.

## Requirements

### Requirement: Um usuário pode ser vinculado a vários escritórios

O sistema DEVE (MUST) permitir que um mesmo usuário esteja vinculado a zero, um ou mais
escritórios, e NÃO DEVE (MUST NOT) exigir uma conta separada por escritório para atender
mais de um.

O vínculo é a única fonte da resposta à pergunta "este usuário pode enxergar este
escritório?". Nenhuma outra informação do usuário — papel, e-mail, domínio — DEVE (MUST)
conceder acesso a um escritório sem vínculo correspondente.

#### Scenario: Usuário atende dois escritórios

- **WHEN** um usuário é vinculado aos escritórios A e B
- **THEN** os dois escritórios ficam disponíveis para ele com a mesma credencial, sem
  necessidade de segunda conta

#### Scenario: Escritório sem vínculo não é alcançável

- **WHEN** um usuário vinculado apenas ao escritório A pede para operar no escritório C
- **THEN** o pedido é recusado, e nenhum dado do escritório C é lido ou gravado

### Requirement: Papel de escritório exige ao menos um vínculo

O sistema DEVE (MUST) impedir a existência de um usuário com papel `EscritorioAdmin` ou
`EscritorioUsuario` sem nenhum vínculo de escritório. A restrição DEVE (MUST) valer para
qualquer origem de escrita — endpoints da API, seeds, migrações de dados e alteração
manual no banco.

`PlatformAdmin` é a exceção: ele PODE (MAY) existir sem vínculo nenhum, porque não
pertence a escritório por definição.

#### Scenario: Criação de usuário de escritório sem escritório

- **WHEN** se tenta criar um usuário com papel `EscritorioAdmin` ou `EscritorioUsuario`
  sem informar nenhum escritório
- **THEN** a gravação é rejeitada

#### Scenario: Remoção do último vínculo de um usuário de escritório

- **WHEN** um administrador tenta remover o único vínculo restante de um usuário com papel
  de escritório
- **THEN** a operação é recusada, com a indicação de que o usuário precisa de ao menos um
  escritório ou de mudança de papel

#### Scenario: PlatformAdmin sem nenhum vínculo

- **WHEN** se grava um usuário com papel `PlatformAdmin` e nenhum escritório vinculado
- **THEN** a gravação é aceita

### Requirement: Quem administra os vínculos

O sistema DEVE (MUST) restringir a criação e a remoção de vínculos ao `PlatformAdmin` e ao
`EscritorioAdmin`, e o `EscritorioAdmin` DEVE (MUST) poder vincular usuários apenas aos
escritórios aos quais ele próprio está vinculado.

Um `EscritorioAdmin` NÃO DEVE (MUST NOT) conseguir remover o vínculo de um usuário com um
escritório ao qual ele mesmo não tem acesso — isso o deixaria alterando o alcance de um
usuário fora do seu escopo.

#### Scenario: EscritorioAdmin vincula usuário ao próprio escritório

- **WHEN** um `EscritorioAdmin` do escritório A vincula um usuário ao escritório A
- **THEN** o vínculo é criado

#### Scenario: EscritorioAdmin tenta vincular a escritório alheio

- **WHEN** um `EscritorioAdmin` vinculado apenas ao escritório A tenta vincular um usuário
  ao escritório B
- **THEN** a operação é recusada e nenhum vínculo é criado

#### Scenario: EscritorioAdmin edita usuário que também atende outro escritório

- **WHEN** um `EscritorioAdmin` do escritório A edita um usuário vinculado a A e a B
- **THEN** ele pode adicionar ou remover o vínculo com A, e o vínculo com B permanece
  intocado

#### Scenario: EscritorioUsuario tenta administrar vínculos

- **WHEN** um usuário com papel `EscritorioUsuario` tenta criar ou remover um vínculo
- **THEN** a operação é recusada

### Requirement: A gestão de usuários trabalha com conjunto de escritórios

O sistema DEVE (MUST) apresentar e receber, no cadastro e na edição de usuário, o
**conjunto** de escritórios do usuário, e NÃO DEVE (MUST NOT) oferecer um campo de
escritório único que sobrescreva silenciosamente os demais vínculos.

#### Scenario: Edição de usuário com dois escritórios

- **WHEN** um administrador abre a edição de um usuário vinculado a dois escritórios
- **THEN** a tela mostra os dois escritórios selecionados, e salvar sem alterá-los mantém
  os dois vínculos

#### Scenario: Administrador acrescenta um escritório ao usuário

- **WHEN** um administrador seleciona um escritório adicional na edição de um usuário e
  salva
- **THEN** o usuário passa a ter os vínculos anteriores mais o novo

### Requirement: Usuário só é apresentado a quem compartilha escritório com ele

O sistema DEVE (MUST) limitar a listagem de usuários vista por um `EscritorioAdmin` aos
usuários que tenham ao menos um vínculo em comum com ele, e DEVE (MUST) exibir para cada
usuário apenas os escritórios que o solicitante também enxerga.

Sem isso, listar usuários viraria um jeito indireto de descobrir a carteira de escritórios
de um colega e a existência de escritórios que não são do solicitante.

#### Scenario: EscritorioAdmin lista usuários

- **WHEN** um `EscritorioAdmin` do escritório A lista os usuários
- **THEN** aparecem apenas usuários vinculados ao escritório A, e cada um exibe apenas o
  vínculo com A, mesmo que atenda outros escritórios

#### Scenario: PlatformAdmin lista usuários

- **WHEN** um `PlatformAdmin` lista os usuários
- **THEN** todos os usuários aparecem, cada um com todos os seus vínculos

### Requirement: Consulta de colegas do escritório em foco para atribuição

O sistema DEVE (MUST) oferecer a qualquer usuário de escritório — inclusive
`EscritorioUsuario` — uma consulta dos usuários **ativos** vinculados ao escritório
em foco da sessão, para uso em campos de atribuição de responsável.

Essa consulta DEVE (MUST) devolver apenas identificador e nome de cada usuário. Ela
NÃO DEVE (MUST NOT) expor e-mail, papel, último acesso, situação de senha ou os
demais escritórios em que o usuário atua — isso segue restrito à gestão de usuários,
que continua exigindo `EscritorioAdmin`.

Quando a sessão não tem escritório em foco — caso possível apenas para
`PlatformAdmin` —, o sistema DEVE (MUST) recusar a consulta pedindo a escolha de um
escritório, e NÃO DEVE (MUST NOT) devolver os usuários de todos os escritórios nem
uma lista vazia.

#### Scenario: Usuário comum abre um seletor de responsável

- **WHEN** um `EscritorioUsuario` abre um campo de atribuição de responsável
- **THEN** ele recebe os usuários ativos do escritório em foco, cada um apenas com
  identificador e nome

#### Scenario: Usuário desativado

- **WHEN** um usuário do escritório está desativado
- **THEN** ele não consta do resultado da consulta

#### Scenario: Usuário de outro escritório

- **WHEN** um usuário vinculado aos escritórios A e B está com A em foco
- **THEN** o resultado traz apenas usuários vinculados a A

#### Scenario: PlatformAdmin sem escritório em foco

- **WHEN** um `PlatformAdmin` sem escritório em foco faz a consulta
- **THEN** o sistema recusa o pedido indicando que é preciso escolher um escritório

#### Scenario: Dados de gestão continuam restritos

- **WHEN** um `EscritorioUsuario` faz a consulta
- **THEN** nenhum e-mail, papel ou vínculo de escritório de terceiros é devolvido
