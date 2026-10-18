## ADDED Requirements

### Requirement: A busca por texto da listagem de clientes ignora maiúsculas, minúsculas e acentos

A busca por texto da listagem de clientes DEVE (MUST) casar o termo
(`GET /api/clientes`, parâmetro `busca`) como "contém" — equivalente a um
`LIKE '%termo%'` — contra o nome, o código e o CNPJ mascarado do cliente, SEM
distinção entre maiúsculas e minúsculas e SEM distinção de acentos. O termo
DEVE (MUST) ser comparado depois de removidos os espaços das pontas.

Os caracteres `%` e `_` presentes no termo NÃO DEVEM (MUST NOT) funcionar como
curingas: são procurados literalmente.

A exportação CSV (`GET /api/clientes/exportar`) DEVE (MUST) aplicar exatamente
o mesmo critério de busca, de modo que a lista exibida e o arquivo exportado
com os mesmos filtros contenham os mesmos clientes.

A busca pelos dígitos do CNPJ completo continua valendo como definida em "O
CNPJ completo é o que a plataforma exibe e busca", e a busca continua
combinando com os demais filtros da tela (situação, escritório, certificado,
regime, onboarding, 2FA).

#### Scenario: Termo em minúsculas acha nome gravado em maiúsculas

- **WHEN** existe o cliente "SILVA COMERCIO LTDA" e o usuário busca "silva"
- **THEN** a listagem traz esse cliente

#### Scenario: Termo com caixa mista

- **WHEN** existe o cliente "SILVA COMERCIO LTDA" e o usuário busca "Comércio"
- **THEN** a listagem traz esse cliente

#### Scenario: Termo sem acento acha nome acentuado

- **WHEN** existe o cliente "JOÃO DA SILVA ME" e o usuário busca "joao"
- **THEN** a listagem traz esse cliente

#### Scenario: Termo no meio do nome

- **WHEN** existe o cliente "PADARIA BOM PAO LTDA" e o usuário busca "bom pao"
- **THEN** a listagem traz esse cliente

#### Scenario: Espaços nas pontas do termo são ignorados

- **WHEN** existe o cliente "SILVA COMERCIO LTDA" e o usuário busca "  silva  "
- **THEN** a listagem traz esse cliente

#### Scenario: Curinga digitado é literal

- **WHEN** existem os clientes "ALFA LTDA" e "BETA LTDA" e o usuário busca "%"
- **THEN** a listagem não traz nenhum dos dois

#### Scenario: Busca por código ignora caixa

- **WHEN** existe um cliente com código "ab12" e o usuário busca "AB12"
- **THEN** a listagem traz esse cliente

#### Scenario: Exportação usa o mesmo critério

- **WHEN** o usuário busca "silva" e exporta o CSV com os mesmos filtros
- **THEN** o arquivo contém exatamente os clientes exibidos na listagem,
  incluindo "SILVA COMERCIO LTDA"

#### Scenario: Busca continua isolada por escritório

- **WHEN** um usuário do escritório A busca "silva" e existe "SILVA COMERCIO
  LTDA" apenas no escritório B
- **THEN** a listagem não traz esse cliente
