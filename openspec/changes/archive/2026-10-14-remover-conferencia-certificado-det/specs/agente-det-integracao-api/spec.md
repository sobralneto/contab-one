## ADDED Requirements

### Requirement: O escritório é identificado só pela chave de API

`Det.Agent` DEVE (MUST) tratar como escritório da execução o dono da chave de
`[api] chave`, e NÃO DEVE (MUST NOT) interromper a execução por causa do CNPJ
do certificado da pasta `certificado/`, nem conferir esse CNPJ contra o
cadastro do escritório no painel.

#### Scenario: Escritório cadastrado sem hash de CNPJ

- **WHEN** a carteira é lida com uma chave válida de um escritório cujo
  cadastro no painel não tem hash de CNPJ
- **THEN** a execução segue para o login no gov.br e consulta os clientes da
  carteira dessa chave

#### Scenario: API antiga ainda manda o hash do escritório

- **WHEN** a resposta da carteira ainda traz um hash de CNPJ do escritório
  que não corresponde ao certificado da pasta
- **THEN** o agente ignora esse campo e consulta os clientes da carteira

## REMOVED Requirements

### Requirement: O certificado da pasta tem de ser do escritório da chave

**Reason**: Escritório cadastrado pelo painel não tem o HMAC do CNPJ, e a
conferência bloqueava a execução mesmo com o certificado certo. O dono do
produto decidiu identificar o escritório só pela chave de API.

**Migration**: Nenhuma ação do escritório. O agente 1.0.0 já distribuído,
falando com a API nova, não recebe o hash, avisa e segue. O agente novo não lê
mais o CNPJ do certificado.
