## Purpose

Define como a plataforma decide de qual escritório é cada linha que um pedido pode ler ou escrever, e garante que a ausência de escopo resolvido nunca seja interpretada como permissão para ver tudo.

## ADDED Requirements

### Requirement: Escopo de tenant indefinido não enxerga nada

O sistema DEVE (MUST) tratar a ausência de escritório resolvido como "nenhuma linha visível", e NÃO DEVE (MUST NOT) tratá-la como ausência de filtro. Apenas o papel `PlatformAdmin` DEVE (MUST) enxergar dados de todos os escritórios, e essa permissão DEVE (MUST) vir de o papel ser reconhecido explicitamente — nunca de o escritório estar vazio.

Isso vale para toda entidade com dono de escritório: clientes, execuções, métricas de execução, agentes, alertas e configurações.

#### Scenario: Sessão de escritório sem escritório resolvido

- **WHEN** um pedido autenticado com papel de escritório chega sem escritório resolvido
- **THEN** nenhuma linha de nenhum escritório é retornada, e nada é gravado

#### Scenario: PlatformAdmin lista dados

- **WHEN** um `PlatformAdmin` consulta clientes, execuções ou alertas
- **THEN** os dados de todos os escritórios são retornados

#### Scenario: Usuário de escritório lista dados

- **WHEN** um usuário do escritório A consulta clientes, execuções ou alertas
- **THEN** apenas os dados do escritório A são retornados

### Requirement: Sessão de escritório sem escritório é rejeitada

O sistema DEVE (MUST) recusar com 401 qualquer pedido cuja credencial declare papel de escritório (`EscritorioAdmin` ou `EscritorioUsuario`) mas não permita resolver a qual escritório ela pertence. A rejeição DEVE (MUST) acontecer antes de o pedido alcançar qualquer handler.

Uma credencial nesse estado é inconsistente por definição — deixá-la seguir com contexto vazio foi o que produziu leitura entre escritórios.

#### Scenario: Token de papel de escritório sem identificação de escritório

- **WHEN** chega um pedido cujo token tem papel `EscritorioUsuario` ou `EscritorioAdmin` e nenhuma identificação de escritório utilizável
- **THEN** a API responde 401 sem executar o handler

#### Scenario: Token de PlatformAdmin sem escritório

- **WHEN** chega um pedido cujo token tem papel `PlatformAdmin` e nenhuma identificação de escritório
- **THEN** o pedido segue normalmente, porque `PlatformAdmin` não pertence a escritório por definição

### Requirement: Todo usuário de escritório tem escritório

O sistema DEVE (MUST) impedir, no nível do armazenamento, a existência de um usuário com papel de escritório e sem escritório associado. A restrição DEVE (MUST) valer para qualquer origem de escrita — endpoints da API, seeds, migrações de dados e alteração manual no banco.

#### Scenario: Gravação de usuário de escritório sem escritório

- **WHEN** se tenta gravar um usuário com papel `EscritorioAdmin` ou `EscritorioUsuario` sem escritório associado
- **THEN** a gravação é rejeitada pelo banco de dados

#### Scenario: Gravação de PlatformAdmin sem escritório

- **WHEN** se grava um usuário com papel `PlatformAdmin` sem escritório associado
- **THEN** a gravação é aceita

### Requirement: A tentativa de furar o escopo pelo pedido não funciona

O sistema DEVE (MUST) resolver o escritório de um pedido exclusivamente a partir da credencial apresentada, e NÃO DEVE (MUST NOT) aceitar escritório vindo de parâmetro de rota, query string ou corpo — exceto de um `PlatformAdmin`, que não tem escritório próprio e precisa indicar o alvo.

#### Scenario: Usuário informa escritório de outro na query string

- **WHEN** um usuário do escritório A consulta um recurso passando o identificador do escritório B como parâmetro
- **THEN** a resposta contém apenas dados do escritório A

#### Scenario: PlatformAdmin informa escritório alvo

- **WHEN** um `PlatformAdmin` consulta ou grava informando o escritório alvo
- **THEN** a operação é aplicada ao escritório informado
