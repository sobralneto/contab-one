## Why

A change `cnpj-completo-cliente` guardou o CNPJ completo cifrado em repouso
(`Cliente.CnpjCifrado`, AES-256-GCM). Em produção, quem olha a tabela vê só a
máscara e um blob ilegível — conferir ou dar suporte a um cliente exige
decifrar fora do banco. O dono do produto decidiu que o CNPJ completo deve
ficar legível no banco, revertendo a Decisão 1 do design daquela change.

## What Changes

- `Cliente` ganha `Cnpj` (`string?`, só os 14 dígitos), legível. Passa a ser a
  coluna gravada no cadastro/edição manual, na importação do PGDAS-D e na
  sincronização do agente.
- Os valores já gravados em `CnpjCifrado` são decifrados uma vez para `Cnpj`
  (backfill no startup, idempotente), sem perder nenhum cliente.
- `CnpjCifrado` deixa de ser lido e escrito. A coluna e `CnpjCipher` ficam
  como legado só para o backfill; a remoção fica para uma change seguinte,
  depois de confirmado o backfill em produção.
- A dashboard do PGDAS passa a formatar `Cnpj` direto, sem decifrar.
- Contrato de API inalterado: listagem, busca, detalhe e CSV continuam sem o
  CNPJ completo (`temCnpjCompleto` segue sendo `Cnpj != null`).
- **BREAKING (segurança):** um dump do Postgres passa a expor o CNPJ completo
  de clientes de terceiros.

## Capabilities

### New Capabilities

### Modified Capabilities

- `gestao-clientes`: o CNPJ completo é persistido em texto legível, não
  cifrado.

## Impact

- `ContabOne.Api`: `Domain/Entities.cs`, `ClientesEndpoints.cs`,
  `PgdasEndpoints.cs`, `AgentEndpoints.cs`, nova migration, backfill no
  startup, testes (`ClientesTest`, `PgdasTest`, `ContratoAgenteTest`).
- `ContabOne.Frontend`: nenhuma mudança.
- Deploy: migration automática no startup; o backfill exige `HMAC_CNPJ_KEY`
  (já obrigatório).
