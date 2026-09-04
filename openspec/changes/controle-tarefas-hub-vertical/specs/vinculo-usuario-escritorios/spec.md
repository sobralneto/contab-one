## ADDED Requirements

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
