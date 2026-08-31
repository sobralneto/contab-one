## MODIFIED Requirements

### Requirement: Escopo de tenant indefinido não enxerga nada

O sistema DEVE (MUST) tratar a ausência de escritório resolvido como "nenhuma linha
visível", e NÃO DEVE (MUST NOT) tratá-la como ausência de filtro. Apenas o papel
`PlatformAdmin` DEVE (MUST) enxergar dados de todos os escritórios, e essa permissão DEVE
(MUST) vir de o papel ser reconhecido explicitamente — nunca de o escritório estar vazio.

O escritório resolvido de um pedido é o **escritório em foco** declarado na credencial.
Um `PlatformAdmin` **com** escritório em foco DEVE (MUST) ser escopado àquele escritório
como qualquer outro usuário; a visão de todos vale apenas quando ele opera sem foco.

Isso vale para toda entidade com dono de escritório: clientes, execuções, métricas de
execução, agentes, alertas e configurações.

#### Scenario: Sessão de escritório sem escritório resolvido

- **WHEN** um pedido autenticado com papel de escritório chega sem escritório resolvido
- **THEN** nenhuma linha de nenhum escritório é retornada, e nada é gravado

#### Scenario: PlatformAdmin lista dados sem foco

- **WHEN** um `PlatformAdmin` sem escritório em foco consulta clientes, execuções ou
  alertas
- **THEN** os dados de todos os escritórios são retornados

#### Scenario: PlatformAdmin lista dados com foco

- **WHEN** um `PlatformAdmin` com o escritório A em foco consulta clientes, execuções ou
  alertas
- **THEN** apenas os dados do escritório A são retornados

#### Scenario: Usuário de escritório lista dados

- **WHEN** um usuário com o escritório A em foco consulta clientes, execuções ou alertas
- **THEN** apenas os dados do escritório A são retornados, mesmo que ele esteja vinculado
  também ao escritório B

### Requirement: Sessão de escritório sem escritório é rejeitada

O sistema DEVE (MUST) recusar com 401 qualquer pedido cuja credencial declare papel de
escritório (`EscritorioAdmin` ou `EscritorioUsuario`) mas não permita resolver qual
escritório está em foco. A rejeição DEVE (MUST) acontecer antes de o pedido alcançar
qualquer handler.

Uma credencial nesse estado é inconsistente por definição — deixá-la seguir com contexto
vazio foi o que produziu leitura entre escritórios.

#### Scenario: Token de papel de escritório sem escritório em foco

- **WHEN** chega um pedido cujo token tem papel `EscritorioUsuario` ou `EscritorioAdmin` e
  nenhum escritório em foco utilizável
- **THEN** a API responde 401 sem executar o handler

#### Scenario: Token de PlatformAdmin sem foco

- **WHEN** chega um pedido cujo token tem papel `PlatformAdmin` e nenhum escritório em foco
- **THEN** o pedido segue normalmente, porque `PlatformAdmin` não pertence a escritório por
  definição

### Requirement: Todo usuário de escritório tem escritório

O sistema DEVE (MUST) impedir, no nível do armazenamento, a existência de um usuário com
papel de escritório e **nenhum escritório vinculado**. A restrição DEVE (MUST) valer para
qualquer origem de escrita — endpoints da API, seeds, migrações de dados e alteração manual
no banco.

O vínculo passou a ser uma relação de muitos-para-muitos: a garantia deixou de ser "a coluna
de escritório não é nula" e passou a ser "existe ao menos uma linha de vínculo". Ver
[[vinculo-usuario-escritorios]].

#### Scenario: Gravação de usuário de escritório sem nenhum vínculo

- **WHEN** se tenta deixar um usuário com papel `EscritorioAdmin` ou `EscritorioUsuario`
  sem nenhum escritório vinculado
- **THEN** a operação é rejeitada

#### Scenario: Gravação de PlatformAdmin sem escritório

- **WHEN** se grava um usuário com papel `PlatformAdmin` sem escritório vinculado
- **THEN** a gravação é aceita

### Requirement: A tentativa de furar o escopo pelo pedido não funciona

O sistema DEVE (MUST) resolver o escritório de um pedido exclusivamente a partir do foco
declarado na credencial apresentada, e NÃO DEVE (MUST NOT) aceitar escritório vindo de
parâmetro de rota, query string ou corpo — exceto de um `PlatformAdmin` operando sem foco,
que precisa indicar o alvo.

Trocar de escritório é uma operação explícita que reemite a credencial; ver
[[escritorio-em-foco]]. Um parâmetro no pedido NÃO É (MUST NOT be) um caminho alternativo
para isso, nem mesmo para um escritório ao qual o usuário está legitimamente vinculado.

#### Scenario: Usuário informa escritório de outro na query string

- **WHEN** um usuário com o escritório A em foco consulta um recurso passando o
  identificador do escritório B como parâmetro
- **THEN** a resposta contém apenas dados do escritório A

#### Scenario: Usuário informa na query string um escritório ao qual está vinculado

- **WHEN** um usuário vinculado a A e B, com A em foco, consulta um recurso passando o
  identificador de B como parâmetro
- **THEN** a resposta contém apenas dados de A, porque o parâmetro não troca o foco

#### Scenario: PlatformAdmin sem foco informa escritório alvo

- **WHEN** um `PlatformAdmin` sem escritório em foco consulta ou grava informando o
  escritório alvo
- **THEN** a operação é aplicada ao escritório informado
