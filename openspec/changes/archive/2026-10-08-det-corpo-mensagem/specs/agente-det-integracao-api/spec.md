## MODIFIED Requirements

### Requirement: O relatório da execução substitui a geração de CSV local

Ao final de uma execução com `[api]` configurado, `Det.Agent` DEVE (MUST)
enviar as mensagens coletadas (título, texto da mensagem, datas, remetente,
tipo e link, por empresa) para a API, abrindo e finalizando uma `Execucao`
como `Nfse.Agent` já faz, e NÃO DEVE (MUST NOT) gravar
`resultado/YYYY-MM-DD_resultado-det.csv` como parte desse fluxo.

`Det.Agent` NÃO DEVE (MUST NOT) enviar a situação de leitura da mensagem.

#### Scenario: Execução normal com API configurada

- **WHEN** `Det.Agent` termina de varrer todas as empresas com `[api]`
  configurada e válida
- **THEN** as mensagens de cada empresa são enviadas para a API vinculadas
  ao `Cliente.Id` correto, a execução é finalizada com o status
  correspondente, e nenhum CSV é gravado em `resultado/`

#### Scenario: Regeneração manual de CSV a partir do JSON local

- **WHEN** um operador roda `tools/exportar_csv.py` apontando para um JSON
  já salvo em `dados/`
- **THEN** o CSV é gerado normalmente — essa ferramenta avulsa não muda,
  só deixa de rodar automaticamente ao fim da coleta

#### Scenario: Mensagem com o texto capturado

- **WHEN** o agente capturou o texto de uma mensagem
- **THEN** o envio dessa mensagem inclui o texto e não inclui a situação

#### Scenario: Mensagem cujo texto não foi capturado

- **WHEN** o agente não conseguiu capturar o texto de uma mensagem
- **THEN** a mensagem é enviada mesmo assim, com o texto vazio
