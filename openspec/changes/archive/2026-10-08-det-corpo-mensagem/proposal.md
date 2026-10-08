## Why

O `Det.Agent` abre cada mensagem não lida da Caixa Postal para capturar o
texto, mas o texto fica só no JSON local da máquina do escritório: a API
recebe assunto, remetente e datas, e o painel não tem como mostrar o que a
mensagem diz. Como abrir a mensagem a marca como lida no portal, hoje o robô
consome a mensagem sem que o contador consiga lê-la no painel. A primeira
execução completa (46 clientes, 24 mensagens) mostrou exatamente isso.

A situação "lida/não lida", por outro lado, é gravada e exibida sem servir a
ninguém: ela registra o estado no instante da coleta, que o próprio robô
altera ao abrir a mensagem.

## What Changes

- O agente passa a enviar o **texto da mensagem** (`corpo`) junto com os
  demais campos, e a API passa a armazená-lo.
- O painel passa a exibir o texto: a página de mensagens ganha a ação de
  abrir uma mensagem e ler o conteúdo completo.
- **BREAKING** A **situação** da mensagem deixa de existir: o agente não a
  envia, a API não a armazena nem a devolve (a coluna é removida) e a página
  perde a coluna "Situação". Um agente antigo que ainda envie o campo
  continua sendo aceito; o valor é ignorado.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities
- `registro-mensagens-det`: o conjunto de campos persistidos por mensagem
  ganha o texto e perde a situação.
- `visualizacao-mensagens-det`: a página passa a permitir ler o texto de uma
  mensagem; a situação deixa de ser exibida.
- `agente-det-integracao-api`: o relatório enviado inclui o texto da mensagem
  e não inclui mais a situação.

## Impact

- **API** (`ContabOne.Api/`): `MensagemDet` ganha `Corpo` e perde `Situacao`
  (migration que adiciona uma coluna e remove outra — o valor de situação já
  gravado é descartado, de propósito); `MensagemDetRequest`,
  `EnviarMensagensDetAsync` e `DetEndpoints.ListarAsync`; testes em
  `DetMensagensTest.cs`.
- **Agente** (`Det.Agent/`): `api_client._traduzir_mensagens` (envia `corpo`,
  para de enviar `situacao`); fake API e testes offline. A coleta em si não
  muda — o corpo já é capturado.
- **Frontend** (`ContabOne.Frontend/`): `MensagemDetDto`,
  `DetMensagensView.vue` (sai a coluna Situação, entra a leitura do texto) e
  seus testes.
- **Privacidade:** o conteúdo textual de mensagens da Caixa Postal passa a
  ser armazenado na API. É a mesma exceção deliberada que `MensagemDet` já
  representa (mensagem DET não é documento fiscal, e mostrá-la no painel é o
  ponto da ferramenta), agora estendida do cabeçalho para o texto. O `.pfx`
  continua sem sair da máquina.
