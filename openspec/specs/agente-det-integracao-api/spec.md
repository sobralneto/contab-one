## Purpose

Cobre a integração do `Det.Agent` com `ContabOne.Api`, trazendo o robô da Caixa
Postal DET à paridade com `Nfse.Agent`: exigência de credencial de API,
autenticação como agente do produto DET, lista de empresas vinda da carteira
de clientes do painel (só leitura: o agente nunca escreve cadastro), conferência
de que o certificado é do escritório da chave, substituição do CSV local pelo
relatório enviado à API, e a mesma fila de pendências com reenvio usada por
qualquer outro agente.

## Requirements

### Requirement: `Det.Agent` recusa rodar sem credencial de API

`Det.Agent` DEVE (MUST) exigir `[api] url` e `[api] chave` preenchidos em
`config.toml` para executar a coleta. Sem os dois campos, a ferramenta
encerra antes de abrir o navegador ou tocar em qualquer certificado, com uma
mensagem explicando o que falta — o mesmo comportamento de
`Nfse.Agent` (`configuracao-local-agente`).

#### Scenario: `config.toml` sem seção `[api]`

- **WHEN** `Det.Agent` é executado e `config.toml` não tem `url` e `chave`
  preenchidos em `[api]`
- **THEN** a execução é interrompida com código de saída de erro de
  configuração, sem autenticar no gov.br nem consultar a API

#### Scenario: `config.toml` com `[api]` completo

- **WHEN** `Det.Agent` é executado e `config.toml` tem `url` e `chave`
  preenchidos
- **THEN** a execução prossegue e usa essas credenciais para autenticar
  contra `ContabOne.Api`

### Requirement: `Det.Agent` autentica como agente do produto DET

`Det.Agent` DEVE (MUST) apresentar a chave de `[api] chave` no cabeçalho
`X-Api-Key` em toda chamada à API, seguindo o mesmo formato
`det_<prefixo8>_<segredo32>` já reservado para o produto DET em
`ApiKeyHasher`, e DEVE (MUST) tratar uma resposta 401 como bloqueio
imediato — nunca como "API indisponível" — assim como `Nfse.Agent` já faz.

#### Scenario: Chave revogada ou escritório inativo

- **WHEN** a API responde 401 a qualquer chamada de `Det.Agent`
- **THEN** a execução é interrompida imediatamente, sem cair em nenhuma
  carência offline

### Requirement: `Det.Agent` consulta a carteira de clientes vinda da API

`Det.Agent` DEVE (MUST) obter a lista de empresas a consultar exclusivamente
da API (`carteira-clientes-agente-det`), depois do handshake e antes de abrir
o navegador, e NÃO DEVE (MUST NOT) ler planilha ou qualquer outra lista local
de empresas. Cada empresa consultada é identificada pelo `Cliente.Id`
recebido, e é o CNPJ completo recebido que o agente digita na troca de perfil
do DET. Quando a API informa clientes sem CNPJ completo, o agente DEVE (MUST)
registrar a quantidade no log como aviso e seguir com os demais.

#### Scenario: Execução normal

- **WHEN** `Det.Agent` roda e a API devolve três clientes
- **THEN** o agente consulta a Caixa Postal dos três, na troca de perfil com o
  CNPJ de cada um, sem precisar de nenhum `empresas.xlsx`

#### Scenario: Carteira vazia

- **WHEN** a API devolve a carteira sem nenhum cliente
- **THEN** o agente não abre o navegador, finaliza a execução sem mensagens
  e explica no log que não há cliente com CNPJ completo a consultar

#### Scenario: API indisponível ao buscar a carteira

- **WHEN** a chamada que busca a carteira falha por rede ou 5xx
- **THEN** a execução é encerrada com erro, sem abrir o navegador — não há
  lista local para cair de volta

#### Scenario: Filtro por empresa na linha de comando

- **WHEN** o operador passa `--empresa` com um CNPJ que está na carteira
- **THEN** só esse cliente é consultado

### Requirement: `Det.Agent` nunca escreve dados de escritório ou de cliente

`Det.Agent` NÃO DEVE (MUST NOT) chamar nenhum endpoint que crie ou altere
`Escritorio` ou `Cliente` — em particular, NÃO DEVE (MUST NOT) chamar
`POST /api/agent/clientes`. As únicas escritas permitidas são as da própria
execução: abrir e finalizar a `Execucao` e enviar as mensagens da Caixa
Postal.

#### Scenario: Execução completa com mensagens

- **WHEN** `Det.Agent` termina uma execução e envia as mensagens coletadas
- **THEN** as chamadas feitas à API se limitam a handshake, leitura da
  carteira, abrir execução, enviar mensagens e finalizar execução — nenhuma
  chamada a `POST /api/agent/clientes`

#### Scenario: Reenvio de pendência

- **WHEN** a execução seguinte reenvia um relatório que ficou na fila de
  pendências
- **THEN** o reenvio também não chama `POST /api/agent/clientes`, e usa os
  `Cliente.Id` guardados na própria pendência

### Requirement: O certificado da pasta tem de ser do escritório da chave

Antes de abrir o navegador, `Det.Agent` DEVE (MUST) ler o CNPJ do certificado
único de `certificado/`, calcular o hash HMAC dele com a chave recebida no
handshake e compará-lo com o hash do escritório informado pela API. Hashes
diferentes DEVEM (MUST) encerrar a execução com erro de configuração. Quando
o escritório não tem CNPJ cadastrado, o agente DEVE (MUST) registrar um aviso
e seguir.

#### Scenario: Certificado de outra empresa

- **WHEN** o certificado da pasta é de um CNPJ diferente do escritório da
  chave
- **THEN** a execução encerra com código de erro de configuração, sem abrir o
  navegador, e o log diz que o certificado não pertence ao escritório

#### Scenario: Certificado do escritório

- **WHEN** o hash do CNPJ do certificado é igual ao do escritório
- **THEN** a execução segue para o login no gov.br

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

### Requirement: Falha no envio do relatório não perde as mensagens coletadas

`Det.Agent` DEVE (MUST) preservar localmente o relatório coletado quando o
envio para a API falhar (rede indisponível, erro 5xx) e DEVE (MUST) reenviá-lo
na execução seguinte, seguindo a mesma fila de pendências e o mesmo descarte
após trinta dias que `registro-execucoes-agente` já define para qualquer
agente.

#### Scenario: API indisponível ao final da coleta

- **WHEN** o envio do relatório falha por indisponibilidade da API
- **THEN** o relatório coletado é preservado localmente e a execução
  seguinte tenta reenviá-lo antes de iniciar sua própria coleta
