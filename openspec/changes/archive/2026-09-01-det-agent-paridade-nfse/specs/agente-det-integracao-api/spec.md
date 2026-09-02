## ADDED Requirements

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
  configuração, sem autenticar no gov.br nem acessar `empresas.xlsx`

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

### Requirement: `Det.Agent` vincula mensagens ao cliente por CNPJ

Antes de enviar o relatório de uma execução, `Det.Agent` DEVE (MUST) fazer
upsert de cada empresa da planilha como `Cliente` do escritório (mesmo
endpoint `POST /api/agent/clientes` usado por `Nfse.Agent`), usando o CNPJ
como identidade — cifrado como hash HMAC e mascarado, nunca em claro — e
usar o `Cliente.Id` devolvido para vincular as mensagens dessa empresa na
execução.

#### Scenario: Empresa nova na planilha

- **WHEN** uma empresa da planilha `empresas.xlsx` ainda não existe como
  `Cliente` do escritório
- **THEN** o upsert cria o cliente e o `Id` retornado é usado para associar
  as mensagens dessa empresa nesta execução

#### Scenario: Empresa já conhecida

- **WHEN** uma empresa da planilha já existe como `Cliente` do escritório
  (mesmo `Codigo`)
- **THEN** o upsert atualiza o cliente existente e reaproveita o mesmo
  `Cliente.Id`

### Requirement: O relatório da execução substitui a geração de CSV local

Ao final de uma execução com `[api]` configurado, `Det.Agent` DEVE (MUST)
enviar as mensagens coletadas (título, mensagem, datas, situação, link, por
empresa) para a API, abrindo e finalizando uma `Execucao` como
`Nfse.Agent` já faz, e NÃO DEVE (MUST NOT) gravar
`resultado/YYYY-MM-DD_resultado-det.csv` como parte desse fluxo.

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
