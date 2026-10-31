## ADDED Requirements

### Requirement: A visão geral permite selecionar clientes para exportação

A tabela da visão geral do PGDAS-D DEVE (MUST) oferecer, em cada linha, uma
caixa de seleção do cliente, e no cabeçalho uma caixa que seleciona ou limpa
todos os clientes listados, indicando quando a seleção é parcial.

Com ao menos um cliente selecionado, a tela DEVE (MUST) exibir quantos estão
selecionados, a ação "Exportar PDFs" e a ação de limpar a seleção. Sem seleção,
essas ações NÃO DEVEM (MUST NOT) aparecer.

#### Scenario: Selecionar alguns clientes

- **WHEN** o usuário marca dois clientes de uma lista de cinco
- **THEN** a tela informa dois clientes selecionados, oferece "Exportar PDFs",
  e a caixa do cabeçalho indica seleção parcial

#### Scenario: Selecionar todos os listados

- **WHEN** o usuário marca a caixa do cabeçalho
- **THEN** todos os clientes listados ficam selecionados

### Requirement: A seleção contém apenas clientes visíveis na lista

A seleção DEVE (MUST) conter apenas clientes visíveis na lista: ao mudar um
filtro, os clientes que saírem da lista DEVEM (MUST) sair da seleção. O sistema
NÃO DEVE (MUST NOT) exportar cliente que o usuário não esteja vendo.

#### Scenario: Filtro tira cliente da seleção

- **WHEN** há clientes selecionados e o usuário muda um filtro de forma que um
  deles deixa de aparecer na lista
- **THEN** esse cliente sai da seleção, e os que continuam na lista permanecem
  selecionados

#### Scenario: Lista truncada

- **WHEN** a lista está truncada pelo teto da listagem e o usuário marca a caixa
  do cabeçalho
- **THEN** a seleção cobre apenas os clientes listados, e o aviso de lista
  truncada continua visível

### Requirement: A exportação em lote gera um PDF da dashboard por cliente

Ao acionar "Exportar PDFs", o sistema DEVE (MUST) gerar um PDF para cada cliente
selecionado e entregar um único download: um arquivo ZIP com um PDF por cliente.

O PDF de cada cliente DEVE (MUST) ser o mesmo documento do "Baixar PDF" da
dashboard daquele cliente, com o leiaute do escritório, a mesma regra de exibição
do CNPJ e os gráficos desenhados por completo.

#### Scenario: Exportação de três clientes

- **WHEN** o usuário seleciona três clientes e aciona "Exportar PDFs"
- **THEN** um único ZIP é baixado, com três PDFs, cada um com os dados do próprio
  cliente

#### Scenario: Mesmo documento da dashboard

- **WHEN** o ZIP é gerado para um cliente e o usuário compara o PDF com o "Baixar
  PDF" da dashboard desse cliente
- **THEN** os dois trazem as mesmas seções, valores e leiaute, com os gráficos
  completos

### Requirement: O filtro de competência define o período do PDF exportado

Quando a visão geral tiver filtro de competência, o PDF de cada cliente DEVE
(MUST) se limitar a esse período. Sem filtro, DEVE (MUST) trazer as mesmas
competências da dashboard do cliente.

#### Scenario: Filtro de competência aplicado

- **WHEN** a visão geral está filtrada de 01/2026 a 03/2026 e o usuário exporta
  os clientes selecionados
- **THEN** o PDF de cada cliente traz apenas as competências desse período

#### Scenario: Sem filtro de competência

- **WHEN** a visão geral não tem filtro de competência e o usuário exporta os
  clientes selecionados
- **THEN** o PDF de cada cliente traz as mesmas competências da dashboard dele

### Requirement: Cada PDF do lote tem nome próprio

O nome de cada PDF DEVE (MUST) identificar o cliente pelo código e pelo nome, e
dois clientes do lote NÃO DEVEM (MUST NOT) resultar em arquivos com o mesmo nome.

#### Scenario: Clientes com nomes parecidos

- **WHEN** dois clientes selecionados têm o mesmo nome
- **THEN** o ZIP traz dois arquivos com nomes diferentes, e nenhum sobrescreve o
  outro

### Requirement: Cada exportação aceita até 100 clientes

Cada exportação DEVE (MUST) aceitar até 100 clientes. Acima disso, o sistema
DEVE (MUST) explicar o limite e NÃO DEVE (MUST NOT) iniciar a geração.

#### Scenario: Seleção acima do limite

- **WHEN** o usuário seleciona 101 clientes
- **THEN** a tela informa o limite de 100 clientes por exportação, e a geração
  não pode ser iniciada

### Requirement: A exportação em lote mostra o progresso

Durante a geração, a tela DEVE (MUST) mostrar quantos clientes já foram
processados do total, e DEVE (MUST) impedir mudar a seleção, mudar os filtros ou
iniciar outra exportação. A informação de progresso DEVE (MUST) ser anunciada a
tecnologias assistivas.

#### Scenario: Progresso visível

- **WHEN** a exportação de doze clientes está em andamento e três já terminaram
- **THEN** a tela indica três de doze, e a seleção não pode ser alterada

### Requirement: A falha de um cliente não interrompe o lote

A falha na geração de um cliente NÃO DEVE (MUST NOT) interromper os demais. Ao
final, o ZIP DEVE (MUST) trazer os PDFs gerados, e a tela DEVE (MUST) informar
quantos foram gerados e quais clientes ficaram de fora. A seleção DEVE (MUST)
passar a conter apenas os que falharam, para que o usuário possa gerar só esses
de novo. Se nenhum PDF for gerado, nenhum arquivo DEVE (MUST) ser baixado.

#### Scenario: Falha em um cliente

- **WHEN** a geração falha para um de três clientes
- **THEN** o ZIP é baixado com dois PDFs, a tela nomeia o cliente que ficou de
  fora, e a seleção passa a conter só esse cliente

#### Scenario: Todos falham

- **WHEN** a geração falha para todos os clientes selecionados
- **THEN** nenhum arquivo é baixado, e a tela informa a falha

### Requirement: A exportação em lote pode ser cancelada

O usuário DEVE (MUST) poder cancelar a exportação em andamento. Cancelada a
exportação, ou deixada a tela, a geração DEVE (MUST) parar e nenhum arquivo DEVE
(MUST) ser baixado.

#### Scenario: Cancelamento

- **WHEN** o usuário cancela a exportação depois de alguns clientes
- **THEN** a geração para, nenhum ZIP é baixado, e a seleção permanece como estava

#### Scenario: Usuário deixa a tela

- **WHEN** o usuário sai da visão geral durante a exportação
- **THEN** a geração para, e nenhum ZIP é baixado

### Requirement: A exportação em lote acontece inteira no navegador

Os PDFs e o ZIP DEVEM (MUST) ser gerados no navegador do usuário, a partir das
leituras que a dashboard já faz. Nenhum PDF, ZIP ou conteúdo gerado DEVE (MUST)
ser enviado ao servidor, e a exportação NÃO DEVE (MUST NOT) gravar nada no
servidor. Cada leitura DEVE (MUST) respeitar o escopo do escritório da sessão.

#### Scenario: Requisições durante a exportação

- **WHEN** o usuário exporta um lote com as ferramentas do navegador abertas
- **THEN** as únicas requisições do lote são leituras da dashboard de cada
  cliente, sem corpo com arquivo
