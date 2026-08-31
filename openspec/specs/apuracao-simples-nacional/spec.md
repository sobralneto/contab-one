# apuracao-simples-nacional Specification

## Purpose

TBD

## Requirements

### Requirement: O documento do PGDAS-D não é enviado ao servidor

O sistema DEVE (MUST) extrair as competências do extrato ou da declaração do
PGDAS-D inteiramente no navegador do usuário. O arquivo PDF NÃO DEVE (MUST
NOT) ser transmitido à API, nem inteiro, nem em pedaços, nem como texto
bruto — a API recebe apenas os valores de apuração já conferidos.

É a mesma promessa que sustenta o agente: conteúdo fiscal de empresa de
terceiro não trafega para a plataforma.

#### Scenario: Usuário carrega um extrato

- **WHEN** o usuário seleciona ou arrasta um PDF do PGDAS-D na tela de
  importação
- **THEN** as competências são extraídas localmente e nenhuma requisição
  carrega o conteúdo do arquivo

#### Scenario: Documento ilegível

- **WHEN** o arquivo não é um documento do PGDAS-D reconhecível, ou nenhuma
  competência pôde ser extraída dele
- **THEN** o arquivo é marcado como não processado com o motivo, os demais
  arquivos do lote continuam sendo processados, e nada é enviado à API

### Requirement: A conferência precede a gravação

O sistema DEVE (MUST) exibir as competências extraídas em uma tela editável
antes de qualquer gravação, e DEVE (MUST) sinalizar cada competência em que a
soma dos oito tributos (IRPJ, CSLL, COFINS, PIS, INSS/CPP, ICMS, IPI, ISS)
divirja do DAS informado em mais de R$ 0,05.

A conferência é o único ponto de validação humana entre o documento e o
banco, e é o que torna aceitável um extrator acoplado a um leiaute que muda
sem aviso.

#### Scenario: Soma dos tributos diverge do DAS

- **WHEN** a soma dos oito tributos de uma competência difere do DAS
  informado em mais de R$ 0,05
- **THEN** a competência é sinalizada como divergente na tela de
  conferência, permanecendo editável

#### Scenario: Valor corrigido à mão

- **WHEN** o usuário altera um valor na conferência e a competência é gravada
- **THEN** a apuração fica registrada como editada manualmente

#### Scenario: Gravação sem passar pela conferência

- **WHEN** o usuário conclui a carga dos arquivos
- **THEN** nada é gravado até que ele confirme a conferência

### Requirement: Competência sem movimento é apuração válida

O sistema DEVE (MUST) tratar competência declarada sem receita e sem DAS a
recolher como uma apuração legítima, distinta de uma extração que falhou.
Competência sem movimento NÃO DEVE (MUST NOT) receber status de pagamento,
porque não há DAS a pagar.

#### Scenario: Mês sem receita

- **WHEN** o documento traz a linha da receita do período zerada e nenhum DAS
- **THEN** a competência aparece na conferência marcada como sem movimento,
  é gravada, e não recebe status de pagamento

#### Scenario: Extração incompleta

- **WHEN** o bloco não traz sequer a linha da receita do período de apuração
- **THEN** ele não vira competência, e o arquivo é reportado como não
  processado

### Requirement: Uma apuração por cliente e competência

O sistema DEVE (MUST) manter no máximo uma apuração por combinação de
escritório, cliente e competência. Gravação que colida com competência já
existente DEVE (MUST) ser recusada informando quais competências colidiram, e
só prosseguir mediante confirmação explícita de substituição.

Sobrescrever em silêncio apagaria correção feita à mão numa importação
anterior.

#### Scenario: Competência já gravada

- **WHEN** o usuário grava um lote que contém competência já existente para
  aquele cliente
- **THEN** a gravação é recusada, as competências em conflito são
  identificadas, e é indicado quais delas foram editadas manualmente

#### Scenario: Substituição confirmada

- **WHEN** o usuário confirma a substituição das competências em conflito
- **THEN** as apurações existentes são substituídas pelos valores do novo
  lote, junto com a segregação de receita correspondente

### Requirement: A dashboard é reconstruída a partir do banco

O sistema DEVE (MUST) permitir abrir a dashboard de apuração de um cliente
para um intervalo de competências usando apenas dados já gravados, sem exigir
que nenhum documento seja carregado de novo.

#### Scenario: Dashboard reaberta meses depois

- **WHEN** o usuário abre a dashboard de um cliente que teve competências
  gravadas em importações anteriores
- **THEN** o painel é montado com os valores gravados, sem pedir arquivo
  algum

#### Scenario: Cliente sem apuração no intervalo

- **WHEN** o intervalo pedido não tem nenhuma competência gravada
- **THEN** a tela informa a ausência de dados em vez de exibir um painel
  vazio ou com zeros

### Requirement: A série mensal do documento alimenta a evolução de 12 meses

O sistema DEVE (MUST) persistir a série de receita bruta mensal que o próprio
documento traz, por cliente e competência, de modo que o gráfico de evolução
cubra também meses cujo documento nunca foi carregado. Quando o mesmo mês
aparecer em documentos diferentes, prevalece o do documento mais recente.

#### Scenario: Mês sem documento carregado

- **WHEN** a dashboard de um cliente é montada e um dos doze meses da série
  não tem apuração gravada, mas aparece na série de um documento carregado
- **THEN** o gráfico de evolução exibe o faturamento daquele mês

#### Scenario: Mesmo mês em dois documentos

- **WHEN** dois documentos de competências diferentes trazem o mesmo mês na
  série mensal com valores distintos
- **THEN** prevalece o valor do documento da competência mais recente

### Requirement: A identidade visual da dashboard vem do escritório

O sistema DEVE (MUST) montar a dashboard com a identidade visual configurada
para o escritório da sessão, e DEVE (MUST) ter uma identidade neutra da
plataforma para escritório sem identidade própria configurada.

O leiaute da dashboard NÃO DEVE (MUST NOT) ser afetado pelo tema da
plataforma — inclusive o modo escuro —, porque é documento entregue ao
cliente final e precisa sair igual na tela e no PDF.

#### Scenario: Escritório com identidade própria

- **WHEN** o escritório tem identidade visual configurada para a ferramenta
- **THEN** a dashboard usa as cores e o logotipo dessa identidade

#### Scenario: Escritório sem identidade configurada

- **WHEN** o escritório não tem identidade configurada
- **THEN** a dashboard é montada com a identidade neutra da plataforma, sem
  erro e sem logotipo de outro escritório

#### Scenario: Plataforma em modo escuro

- **WHEN** o usuário está com a plataforma em modo escuro e abre a dashboard
- **THEN** a dashboard é exibida com as próprias cores, idêntica ao que será
  exportado

### Requirement: O CNPJ do documento nunca é persistido inteiro

O sistema DEVE (MUST) usar o CNPJ lido do documento apenas em memória, para
derivar o hash de identificação e a versão mascarada, e DEVE (MUST) exibir o
CNPJ mascarado em toda apresentação — inclusive na dashboard gerada e na
exportação.

#### Scenario: Documento com CNPJ

- **WHEN** uma competência é gravada a partir de um documento
- **THEN** nenhum registro guarda o CNPJ completo, e a dashboard exibe a
  versão mascarada

### Requirement: Apuração pertence ao escritório da sessão

O sistema DEVE (MUST) escopar apuração, segregação e série mensal ao
escritório da sessão, e NÃO DEVE (MUST NOT) aceitar escopo indicado no
pedido para usuário de escritório.

#### Scenario: Leitura de apuração de outro escritório

- **WHEN** um usuário de escritório pede apurações indicando outro escritório
- **THEN** ele recebe apenas as apurações do próprio escritório

#### Scenario: Gravação para cliente de outro escritório

- **WHEN** a gravação aponta para um cliente que não pertence ao escritório
  da sessão
- **THEN** a gravação é recusada e nenhuma apuração é criada
