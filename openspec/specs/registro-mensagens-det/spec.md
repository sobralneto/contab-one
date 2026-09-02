## Purpose

Cobre a persistência das mensagens da Caixa Postal DET na API — recebimento
por execução, upsert por chave e o isolamento multi-tenant que as protege —
e a consulta usada pelo painel para listá-las por escritório e cliente.

## Requirements

### Requirement: A API armazena as mensagens da Caixa Postal DET por execução

A API DEVE (MUST) aceitar, de um agente autenticado do produto DET, o envio
de mensagens coletadas na Caixa Postal de cada `Cliente` durante uma
`Execucao`, persistindo ao menos: `ClienteId`, `ExecucaoId`, identificador da
mensagem no portal, número, data de envio, data de leitura, prazo,
remetente, tipo, assunto, situação e link — as mesmas colunas que hoje só
existiam no CSV local de `Det.Agent`.

#### Scenario: Envio de mensagens de uma execução

- **WHEN** um agente DET autenticado envia mensagens de Caixa Postal
  referenciando uma `Execucao` aberta por ele mesmo
- **THEN** as mensagens são persistidas vinculadas ao `Cliente` e à
  `Execucao` informados, e a resposta confirma a quantidade recebida

#### Scenario: Reenvio da mesma execução

- **WHEN** o agente reenvia mensagens já persistidas para a mesma
  `Execucao` (mesmo identificador de mensagem no portal)
- **THEN** a API atualiza os registros existentes em vez de duplicá-los

### Requirement: Mensagens só são aceitas para clientes do próprio escritório

A API DEVE (MUST) descartar, sem falhar a requisição, qualquer mensagem cujo
`ClienteId` não pertença ao escritório do agente autenticado — mesma regra
de isolamento que `EnviarMetricasAsync` já aplica para `ExecucaoMetrica`.

#### Scenario: Mensagem referenciando cliente de outro escritório

- **WHEN** o payload enviado contém uma mensagem com `ClienteId` que não
  pertence ao escritório do agente autenticado
- **THEN** essa mensagem é descartada silenciosamente e as demais do mesmo
  envio são processadas normalmente

### Requirement: O painel consulta mensagens DET filtrando por cliente

A API DEVE (MUST) expor uma forma de listar as mensagens DET do escritório
em foco de um usuário autenticado do painel, com filtro opcional por
`ClienteId`, respeitando o mesmo isolamento multi-tenant (`Infra/TenantContext`)
usado por todo o resto da API.

#### Scenario: Usuário do painel lista mensagens sem filtro

- **WHEN** um usuário do escritório consulta as mensagens DET sem informar
  cliente
- **THEN** a resposta traz as mensagens de todos os clientes do escritório
  em foco, e nenhuma de outro escritório

#### Scenario: Usuário do painel filtra por cliente

- **WHEN** um usuário do escritório consulta as mensagens DET informando um
  `ClienteId`
- **THEN** a resposta traz somente as mensagens desse cliente
