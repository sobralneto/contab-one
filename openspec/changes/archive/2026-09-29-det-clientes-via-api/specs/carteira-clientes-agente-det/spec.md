## ADDED Requirements

### Requirement: A API entrega ao agente DET a carteira de clientes ativos do escritório

A API DEVE (MUST) oferecer, no grupo `/api/agent` e autenticado por
`X-Api-Key`, um endpoint de leitura que devolve os clientes **ativos**
(`Cliente.Ativo = true`) do escritório identificado pela chave, cada um com
`id` (`Cliente.Id`), `nome` e `cnpj` completo (14 dígitos, decifrado de
`Cliente.CnpjCifrado`). O escritório DEVE (MUST) ser resolvido pelo
`TenantContext` da chave — nunca por parâmetro de rota ou de query.

#### Scenario: Escritório com clientes ativos e inativos

- **WHEN** um agente DET do escritório A chama o endpoint e A tem três
  clientes ativos com CNPJ completo e um cliente inativo
- **THEN** a resposta lista exatamente os três clientes ativos, com `id`,
  `nome` e `cnpj` de 14 dígitos, e não inclui o inativo

#### Scenario: Outro escritório não aparece

- **WHEN** um agente DET do escritório A chama o endpoint e o escritório B
  também tem clientes ativos
- **THEN** nenhum cliente de B aparece na resposta

### Requirement: Clientes sem CNPJ completo são contados, não listados

A lista MUST NOT incluir cliente ativo sem CNPJ completo cadastrado
(`CnpjCifrado` nulo), e a resposta DEVE (MUST) informar
quantos clientes ativos ficaram de fora por esse motivo, para que o agente
possa avisar o operador.

#### Scenario: Carteira com clientes sem CNPJ completo

- **WHEN** o escritório tem cinco clientes ativos, dois deles sem CNPJ
  completo
- **THEN** a resposta lista os três com CNPJ completo e informa `2` como a
  quantidade de clientes sem CNPJ completo

### Requirement: A resposta traz o hash do CNPJ do escritório

A resposta DEVE (MUST) incluir o `CnpjHash` do escritório da chave (o mesmo
HMAC de `CnpjHasher`), para que o agente confira se o certificado da pasta
pertence a esse escritório. Escritório sem CNPJ cadastrado devolve o campo
vazio.

#### Scenario: Escritório com CNPJ cadastrado

- **WHEN** o escritório da chave tem `CnpjHash` preenchido
- **THEN** a resposta traz esse mesmo valor no campo do hash do escritório

### Requirement: O endpoint é exclusivo de agentes do produto DET

O endpoint DEVE (MUST) responder 403 quando a chave autenticada pertence a um
agente cujo produto não é `det` (comparando o `Produto.Codigo` do próprio
agente), e 401 quando não há chave válida ou o escritório não está `Ativo`,
como os demais endpoints de agente.

#### Scenario: Agente NFS-e com chave válida

- **WHEN** um agente do produto `nfse` com chave válida chama o endpoint
- **THEN** a resposta é 403 e nenhum cliente é devolvido

#### Scenario: Escritório suspenso

- **WHEN** a chave pertence a um escritório com status diferente de `Ativo`
- **THEN** a resposta é 401

### Requirement: Consultar a carteira não escreve nada

Chamar o endpoint NÃO DEVE (MUST NOT) criar, alterar ou apagar nenhum
registro de `Escritorio` ou de `Cliente`.

#### Scenario: Chamada repetida

- **WHEN** o endpoint é chamado duas vezes seguidas pelo mesmo agente
- **THEN** `AtualizadoEm` de cada `Cliente` e do `Escritorio` permanece
  igual ao de antes das chamadas, e nenhum cliente novo existe
