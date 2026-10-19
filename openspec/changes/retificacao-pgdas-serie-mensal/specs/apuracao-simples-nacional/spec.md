## MODIFIED Requirements

### Requirement: A série mensal do documento alimenta a evolução de 12 meses

O sistema DEVE (MUST) persistir a série de receita bruta mensal que o próprio
documento traz, por cliente e competência, de modo que o gráfico de evolução
cubra também meses cujo documento nunca foi carregado.

O valor de um mês na série DEVE (MUST) seguir esta precedência:

- **Mês declarado pelo documento** (uma competência gravada como apuração no
  mesmo pedido): a receita declarada DEVE (MUST) sobrescrever o valor da
  série daquele mês, mesmo que ele tenha sido gravado antes pelo histórico de
  um documento de competência mais recente. É o caso da retificadora de uma
  competência antiga.
- **Mês que chega só pelo histórico de outro documento:** NÃO DEVE (MUST NOT)
  sobrescrever mês que tenha apuração gravada para o cliente. Para mês sem
  apuração gravada, quando o mesmo mês aparecer em documentos diferentes,
  prevalece o do documento de competência mais recente.

Assim, para todo mês com apuração gravada, a série mensal DEVE (MUST) ter a
mesma receita que o faturamento da apuração. A dashboard não pode mostrar um
valor nos cards e outro no gráfico de evolução para o mesmo mês.

#### Scenario: Mês sem documento carregado

- **WHEN** a dashboard de um cliente é montada e um dos doze meses da série
  não tem apuração gravada, mas aparece na série de um documento carregado
- **THEN** o gráfico de evolução exibe o faturamento daquele mês

#### Scenario: Mesmo mês em dois documentos

- **WHEN** dois documentos de competências diferentes trazem, só no histórico,
  o mesmo mês com valores distintos, e esse mês não tem apuração gravada
- **THEN** prevalece o valor do documento da competência mais recente

#### Scenario: Retificadora de competência antiga

- **WHEN** a série de março/2026 foi gravada pelo histórico do documento de
  08/2026, e depois o usuário importa a retificadora de 03/2026 e confirma a
  substituição da competência
- **THEN** a série de março/2026 passa a ter a receita declarada na
  retificadora, igual ao faturamento da apuração substituída

#### Scenario: Histórico de documento mais novo não desfaz a apuração

- **WHEN** março/2026 tem apuração gravada, e depois é importado um documento
  de 09/2026 cujo histórico traz março/2026 com outro valor
- **THEN** a série de março/2026 mantém o faturamento da apuração gravada

#### Scenario: Dados gravados antes da mudança

- **WHEN** a mudança é implantada, e um cliente tem um mês em que a série
  mensal e o faturamento da apuração divergem
- **THEN** a série daquele mês passa a ter o faturamento da apuração, sem que
  nenhum documento precise ser reimportado
