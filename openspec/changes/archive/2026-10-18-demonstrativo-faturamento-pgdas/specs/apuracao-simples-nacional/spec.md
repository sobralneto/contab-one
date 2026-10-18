## MODIFIED Requirements

### Requirement: A sidebar mostra a identidade do cliente e o histórico de competências

Cada linha da lista DEVE (MUST) ter um ícone que, ao ser acionado, abre uma
sidebar à direita. A sidebar DEVE (MUST) exibir o "Demonstrativo Mensal de
Faturamento" do cliente, definido na capability `demonstrativo-faturamento`:
identificação do cliente (razão social, CNPJ, data de abertura e regime
tributário), faturamento mês a mês de dois anos-calendário com o total de
cada ano, nota sobre a declaração, local e data, e bloco de assinaturas. O
CNPJ DEVE (MUST) aparecer completo quando o cliente o tem, e mascarado quando
não tem.

A sidebar NÃO DEVE (MUST NOT) exibir mais a tabela operacional de competências
(DAS, vencimento, situação pago/aberto e pendências). Esses dados continuam na
lista principal e na dashboard do cliente.

A sidebar DEVE (MUST) carregar todas as competências do cliente, sem os
filtros de competência da lista principal. O demonstrativo cobre anos
inteiros, independentemente do intervalo filtrado na lista.

#### Scenario: Abrir a sidebar de um cliente

- **WHEN** o usuário aciona o ícone de detalhe de uma linha da lista
- **THEN** uma sidebar se abre à direita com o demonstrativo de faturamento do
  cliente e, no topo, as ações "Exportar PDF" e "Imprimir"

#### Scenario: Filtro da lista não recorta o demonstrativo

- **WHEN** a lista principal está filtrada de 2026-06 a 2026-08 e o usuário
  abre o detalhe de um cliente com apurações desde 2025-01
- **THEN** o demonstrativo mostra todos os meses gravados de 2025 e 2026

#### Scenario: Fechamento da sidebar

- **WHEN** o usuário fecha a sidebar ou aciona o detalhe de outro cliente
- **THEN** a sidebar fecha (ou muda para o novo cliente) e a lista principal
  permanece com os mesmos dados

### Requirement: A listagem carrega a identidade do cliente

A resposta de `GET /api/pgdas/apuracoes` DEVE (MUST) incluir, em cada
apuração:

- o código do cliente, o CNPJ mascarado dele e, quando existir, o CNPJ
  completo (`clienteCodigo`, `clienteCnpjMascarado`, `clienteCnpj`),
  provenientes das colunas já gravadas de `Cliente`;
- a data de abertura do cliente (`clienteDataAbertura`, `AAAA-MM-DD`), ou
  `null` quando não é conhecida;
- o Nº da Declaração da apuração (`numeroDeclaracao`), ou `null` quando não
  foi gravado.

#### Scenario: Listagem expõe a identidade

- **WHEN** o endpoint de listagem responde a uma requisição autenticada
- **THEN** cada item da resposta carrega `clienteCodigo` e
  `clienteCnpjMascarado`, mais `clienteCnpj` quando o cliente tem CNPJ
  completo gravado

#### Scenario: Listagem expõe data de abertura e nº da declaração

- **WHEN** o cliente tem data de abertura gravada e a apuração tem Nº da
  Declaração gravado
- **THEN** o item da resposta carrega `clienteDataAbertura` e
  `numeroDeclaracao` preenchidos

#### Scenario: Dados anteriores à mudança

- **WHEN** a apuração foi gravada antes desta mudança
- **THEN** o item da resposta traz `numeroDeclaracao` nulo (e
  `clienteDataAbertura` nulo se o cliente nunca recebeu essa data), sem erro

## ADDED Requirements

### Requirement: A extração captura a data de abertura e o Nº da Declaração

O extrator do PGDAS-D, no navegador, DEVE (MUST) ler de cada documento,
extrato ou declaração, quando presentes:

- a **data de abertura no CNPJ** da empresa (`dd/mm/aaaa`);
- o **Nº da Declaração** da competência (sequência de dígitos).

A ausência de um desses campos NÃO DEVE (MUST NOT) marcar o documento como
não processado nem bloquear a gravação. Os dois são opcionais.

#### Scenario: Documento com os dois campos

- **WHEN** o documento traz "Data de abertura no CNPJ: 28/12/2022" e
  "Nº da Declaração: 48992503202608001"
- **THEN** a competência extraída carrega a data de abertura `2022-12-28` e o
  número `48992503202608001`

#### Scenario: Documento sem os campos

- **WHEN** o documento não traz nem a data de abertura nem o Nº da Declaração
- **THEN** a competência é extraída normalmente, com os dois campos vazios

### Requirement: A gravação persiste a data de abertura e o Nº da Declaração

`POST /api/pgdas/apuracoes` DEVE (MUST) aceitar, opcionalmente:

- a data de abertura do cliente (`dataAberturaCliente`). Quando informada, é
  gravada em `Cliente.DataAbertura`, substituindo o valor anterior;
- o Nº da Declaração de cada apuração (`numeroDeclaracao`). É gravado em
  `ApuracaoSimples.NumeroDeclaracao` na criação e na substituição da
  competência.

Quando a data não é informada, a data já gravada no cliente DEVE (MUST) ser
mantida. O Nº da Declaração, se informado, DEVE (MUST) conter só dígitos, com
no máximo 30 caracteres. Fora disso, o pedido é recusado com erro de
validação.

#### Scenario: Gravação com os dois campos

- **WHEN** o lote é gravado com `dataAberturaCliente = 2022-12-28` e uma
  apuração com `numeroDeclaracao = 48992503202608001`
- **THEN** o cliente passa a ter data de abertura 28/12/2022 e a apuração
  passa a ter aquele número

#### Scenario: Gravação sem data de abertura

- **WHEN** o lote é gravado sem `dataAberturaCliente` para um cliente que já
  tem data de abertura
- **THEN** a data de abertura do cliente permanece a mesma

#### Scenario: Número da declaração inválido

- **WHEN** uma apuração chega com `numeroDeclaracao` contendo letras
- **THEN** a API responde com erro de validação e nada é gravado
