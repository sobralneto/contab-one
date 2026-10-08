## MODIFIED Requirements

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

## ADDED Requirements

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

## REMOVED Requirements

### Requirement: `Det.Agent` vincula mensagens ao cliente por CNPJ

**Reason**: o agente deixa de cadastrar clientes. A lista vem da API já com o
`Cliente.Id`, então o upsert por CNPJ — que também dava a um robô de leitura o
poder de criar e alterar clientes — não é mais necessário nem permitido.

**Migration**: cadastre (ou complete o CNPJ de) cada cliente pelo painel, em
Clientes; o agente passa a consultar automaticamente todo cliente ativo com
CNPJ completo. A planilha `empresas/empresas.xlsx` pode ser apagada.
