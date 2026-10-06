## MODIFIED Requirements

### Requirement: A sidebar mostra a identidade do cliente e o histórico de competências

Cada linha da lista DEVE (MUST) ter um ícone que, ao ser acionado, abre uma
sidebar à direita exibindo a identificação do cliente — código, nome e CNPJ — e, abaixo, uma tabela das competências do cliente com os
respectivos valores (faturamento, DAS, vencimento, status pago/aberto e
pendências). O CNPJ DEVE (MUST) aparecer completo quando o cliente o tem, e mascarado
quando não tem.

#### Scenario: Abrir a sidebar de um cliente

- **WHEN** o usuário aciona o ícone de detalhe de uma linha da lista
- **THEN** uma sidebar se abre à direita com o código, o nome e o CNPJ
  do cliente, seguidos da tabela das competências dele com os
  respectivos valores

#### Scenario: Fechamento da sidebar

- **WHEN** o usuário fecha a sidebar ou aciona o detalhe de outro cliente
- **THEN** a sidebar fecha (ou muda para o novo cliente) e a lista principal
  permanece com os mesmos dados

### Requirement: A listagem carrega a identidade do cliente

A resposta de `GET /api/pgdas/apuracoes` DEVE (MUST) incluir, em cada
apuração, o código do cliente, o CNPJ mascarado dele e, quando existir, o CNPJ
completo (`clienteCodigo`, `clienteCnpjMascarado`, `clienteCnpj`),
provenientes das colunas já gravadas de `Cliente`.

#### Scenario: Listagem expõe a identidade

- **WHEN** o endpoint de listagem responde a uma requisição autenticada
- **THEN** cada item da resposta carrega `clienteCodigo` e
  `clienteCnpjMascarado`, mais `clienteCnpj` quando o cliente tem CNPJ
  completo gravado
