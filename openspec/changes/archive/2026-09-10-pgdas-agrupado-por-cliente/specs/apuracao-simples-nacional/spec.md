## ADDED Requirements

### Requirement: A visão geral lista uma apuração por cliente

A tela de visão geral do PGDAS-D DEVE (MUST) exibir a lista de apurações
agrupada por cliente: uma linha por cliente, com o nome do cliente e a
última competência importada dele, ordenada da competência mais recente
para a mais antiga. O ícone "Ver dashboard" DEVE (MUST) continuar
disponível na coluna de ações dessa tabela, comportando-se como hoje.

#### Scenario: Cliente com várias competências

- **WHEN** a lista é carregada e um cliente tem apurações de mais de uma
  competência
- **THEN** ele aparece em exatamente uma linha, com a última competência
  importada dele

#### Scenario: Ver dashboard permanece acessível

- **WHEN** o usuário clica no ícone "Ver dashboard" de uma linha
- **THEN** a navegação para a dashboard do cliente ocorre como antes da
  mudança

### Requirement: A sidebar mostra a identidade do cliente e o histórico de competências

Cada linha da lista DEVE (MUST) ter um ícone que, ao ser acionado, abre uma
sidebar à direita exibindo a identificação do cliente — código, nome e CNPJ
mascarado — e, abaixo, uma tabela das competências do cliente com os
respectivos valores (faturamento, DAS, vencimento, status pago/aberto e
pendências). O CNPJ DEVE (MUST) aparecer mascarado, como em toda a
plataforma.

#### Scenario: Abrir a sidebar de um cliente

- **WHEN** o usuário aciona o ícone de detalhe de uma linha da lista
- **THEN** uma sidebar se abre à direita com o código, o nome e o CNPJ
  mascarado do cliente, seguidos da tabela das competências dele com os
  respectivos valores

#### Scenario: Fechamento da sidebar

- **WHEN** o usuário fecha a sidebar ou aciona o detalhe de outro cliente
- **THEN** a sidebar fecha (ou muda para o novo cliente) e a lista principal
  permanece com os mesmos dados

### Requirement: A listagem carrega a identidade do cliente

A resposta de `GET /api/pgdas/apuracoes` DEVE (MUST) incluir, em cada
apuração, o código do cliente e o CNPJ mascarado dele (`clienteCodigo`,
`clienteCnpjMascarado`), provenientes das colunas já gravadas de
`Cliente` — nunca o CNPJ inteiro.

#### Scenario: Listagem expõe identidade mascarada

- **WHEN** o endpoint de listagem responde a uma requisição autenticada
- **THEN** cada item da resposta carrega `clienteCodigo` e
  `clienteCnpjMascarado`, e nenhum campo carrega CNPJ não mascarado