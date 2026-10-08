## MODIFIED Requirements

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
