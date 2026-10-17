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
remetente, tipo, assunto, **texto da mensagem** e link.

A API NÃO DEVE (MUST NOT) armazenar nem devolver a situação de leitura da
mensagem ("lida"/"não lida"). Um envio que ainda traga esse campo DEVE (MUST)
ser aceito normalmente, com o valor ignorado — agentes já instalados não
podem começar a falhar por causa de um campo que deixou de existir.

O texto é opcional: mensagem cujo texto o agente não conseguiu capturar é
persistida sem ele.

#### Scenario: Envio de mensagens de uma execução

- **WHEN** um agente DET autenticado envia mensagens de Caixa Postal
  referenciando uma `Execucao` aberta por ele mesmo
- **THEN** as mensagens são persistidas vinculadas ao `Cliente` e à
  `Execucao` informados, e a resposta confirma a quantidade recebida

#### Scenario: Reenvio da mesma execução

- **WHEN** o agente reenvia mensagens já persistidas para a mesma
  `Execucao` (mesmo identificador de mensagem no portal)
- **THEN** a API atualiza os registros existentes em vez de duplicá-los

#### Scenario: Mensagem com texto

- **WHEN** o agente envia uma mensagem com o texto preenchido
- **THEN** o texto é persistido e devolvido na consulta do painel

#### Scenario: Mensagem sem texto

- **WHEN** o agente envia uma mensagem sem o texto
- **THEN** a mensagem é persistida com os demais campos e o texto fica vazio

#### Scenario: Agente antigo ainda envia a situação

- **WHEN** o envio traz o campo de situação de leitura
- **THEN** a requisição é aceita, as mensagens são persistidas e a situação
  não aparece em nenhuma resposta da API

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

### Requirement: A API guarda a prioridade por assunto de mensagem DET

A API DEVE (MUST) guardar, por escritório, uma prioridade (Baixa, Média ou Alta) associada a um assunto de mensagem DET. O assunto DEVE (MUST) ser identificado após normalização — remoção de espaços nas pontas e comparação sem diferença de maiúsculas/minúsculas — de modo que variações triviais do mesmo assunto compartilhem a mesma prioridade. Mensagens sem assunto DEVEM (MUST) compartilhar uma única prioridade própria. A prioridade NÃO DEVE (MUST NOT) ser guardada na mensagem individual. O valor DEVE (MUST) atravessar a rede como inteiro, como os demais enums.

#### Scenario: Assunto ainda não classificado

- **WHEN** não há prioridade definida para o assunto de uma mensagem
- **THEN** a consulta devolve `prioridade` nula para essa mensagem

#### Scenario: Variação de caixa e espaços

- **WHEN** a prioridade Alta é definida para "Aviso de pendência" e existe uma mensagem com o assunto " aviso de pendência "
- **THEN** a consulta devolve prioridade Alta para essa mensagem

#### Scenario: Prioridade isolada por escritório

- **WHEN** o escritório A define Alta para um assunto e o escritório B tem mensagens com o mesmo assunto
- **THEN** as mensagens do escritório B continuam sem prioridade

### Requirement: A consulta devolve a prioridade do assunto em cada mensagem

A consulta de mensagens DET DEVE (MUST) incluir, em cada mensagem, a prioridade vigente do seu assunto (nula quando não classificado). Todas as mensagens de um mesmo assunto DEVEM (MUST) trazer a mesma prioridade, incluindo mensagens coletadas depois da classificação.

#### Scenario: Mensagens já existentes

- **WHEN** a prioridade de um assunto é definida e o painel consulta as mensagens
- **THEN** todas as mensagens desse assunto trazem essa prioridade

#### Scenario: Mensagem coletada depois

- **WHEN** o agente envia uma mensagem nova cujo assunto já foi classificado
- **THEN** a consulta devolve essa mensagem já com a prioridade do assunto

### Requirement: O painel define ou limpa a prioridade de um assunto

A API DEVE (MUST) oferecer uma operação autenticada como usuário do escritório para definir a prioridade de um assunto como Baixa, Média ou Alta, ou limpá-la (nula). A operação DEVE (MUST) rejeitar valor fora dos níveis definidos, DEVE (MUST) atuar somente sobre o escritório em foco e NÃO DEVE (MUST NOT) alterar nenhuma mensagem. A chave de API de agente NÃO DEVE (MUST NOT) alcançar essa operação. Definir a prioridade de um assunto que já tinha uma DEVE (MUST) substituí-la, sem criar duplicata.

#### Scenario: Usuário classifica um assunto

- **WHEN** um usuário do escritório define a prioridade Média para um assunto
- **THEN** a prioridade é gravada e passa a ser devolvida, para todos os usuários do escritório, em todas as mensagens desse assunto

#### Scenario: Reclassificar

- **WHEN** o usuário define Alta para um assunto que estava Média
- **THEN** o assunto passa a Alta e continua havendo um único registro de prioridade para ele

#### Scenario: Limpar a classificação

- **WHEN** o usuário define a prioridade do assunto como nula
- **THEN** as mensagens desse assunto voltam a vir sem prioridade

#### Scenario: Valor inválido

- **WHEN** a operação recebe um valor que não é nenhum dos níveis
- **THEN** a API responde com erro de validação e não altera nada

#### Scenario: Chave de agente

- **WHEN** a operação é chamada com a chave de API de um agente
- **THEN** a API nega o acesso
