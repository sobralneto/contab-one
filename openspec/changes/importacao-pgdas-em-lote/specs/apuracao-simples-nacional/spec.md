## ADDED Requirements

### Requirement: O lote de importação pode conter várias empresas

O sistema DEVE (MUST) aceitar, numa mesma importação, documentos do PGDAS-D de
empresas diferentes, e DEVE (MUST) atribuir cada competência extraída à empresa
do CNPJ lido no próprio documento. A mescla de documentos do mesmo período
(extrato e declaração do mesmo mês) DEVE (MUST) ocorrer apenas entre documentos
da **mesma** empresa: competências de mesmo período e empresas diferentes NÃO
DEVEM (MUST NOT) ser mescladas, sobrescritas nem gravadas no mesmo cliente.

Quando um documento não trouxer CNPJ reconhecível, suas competências DEVEM
(MUST) formar um grupo próprio, marcado como empresa não identificada, e NÃO
DEVEM (MUST NOT) ser atribuídas por suposição a outra empresa do lote.

Remover um arquivo do lote DEVE (MUST) remover também as competências que
vieram exclusivamente dele.

A data de abertura no CNPJ e o Nº da Declaração lidos de um documento DEVEM
(MUST) ficar com a empresa daquele documento, e NÃO DEVEM (MUST NOT) ser
atribuídos a outra empresa do lote.

#### Scenario: Lote com extratos de duas empresas

- **WHEN** o usuário carrega, no mesmo lote, extratos de duas empresas com
  CNPJs diferentes
- **THEN** as competências de cada uma ficam agrupadas sob a sua empresa, e o
  lote informa quantas empresas e quantas competências foram lidas

#### Scenario: Mesmo mês em empresas diferentes

- **WHEN** o lote traz a competência 03/2026 de duas empresas diferentes
- **THEN** cada empresa mantém a sua competência 03/2026, com os próprios
  valores, sem que uma substitua a outra

#### Scenario: Extrato e declaração do mesmo mês da mesma empresa

- **WHEN** o lote traz extrato e declaração da mesma competência de uma mesma
  empresa
- **THEN** eles resultam em uma única linha de competência naquela empresa,
  como numa importação de empresa única

#### Scenario: Data de abertura não passa de uma empresa para outra

- **WHEN** o lote traz documentos de duas empresas e só os de uma delas trazem
  a data de abertura no CNPJ
- **THEN** a data de abertura fica associada apenas a essa empresa, e a outra
  segue sem data de abertura lida

#### Scenario: Documento sem CNPJ reconhecível

- **WHEN** um documento é lido com competências válidas mas sem CNPJ
  reconhecível
- **THEN** suas competências aparecem num grupo de empresa não identificada,
  separado das demais empresas do lote

#### Scenario: Arquivo removido do lote

- **WHEN** o usuário remove do lote um arquivo já processado
- **THEN** as competências que só esse arquivo trouxe deixam de aparecer na
  empresa correspondente, e uma empresa que fique sem competências sai do lote

### Requirement: A conferência exibe um card por empresa

A etapa de conferência DEVE (MUST) exibir um card para cada empresa do lote.
Cada card DEVE (MUST) mostrar, no topo, a identificação da empresa — razão
social editável, CNPJ mascarado, município/UF e anexo/atividade editáveis, a
data de abertura no CNPJ quando lida dos documentos (só leitura, porque a
gravação a grava no cadastro do cliente), e a situação do cliente no
escritório (já cadastrado ou ainda não cadastrado) — e, abaixo dela, a tabela
editável com as competências importadas daquela empresa.

A sinalização de divergência entre a soma dos tributos e o DAS, a alternância
Pago/Aberto, a marcação de sem movimento e a remoção de linha DEVEM (MUST)
continuar valendo dentro da tabela de cada card, afetando apenas a empresa
daquele card. O usuário DEVE (MUST) poder retirar uma empresa inteira do lote
sem afetar as demais.

O CNPJ DEVE (MUST) continuar aparecendo mascarado nesta etapa.

#### Scenario: Conferência de um lote com três empresas

- **WHEN** o usuário avança para a conferência com documentos de três empresas
- **THEN** a tela exibe três cards, cada um com a identificação da empresa
  acima e a tabela das competências dela abaixo

#### Scenario: Lote de uma única empresa

- **WHEN** o lote contém documentos de uma única empresa
- **THEN** a conferência exibe um único card, com a identificação da empresa
  acima e a tabela das competências abaixo, no mesmo card

#### Scenario: Divergência sinalizada dentro do card da empresa

- **WHEN** uma competência de uma das empresas tem soma de tributos diferente
  do DAS em mais de R$ 0,05
- **THEN** a linha é sinalizada como divergente na tabela do card daquela
  empresa, e os cards das demais empresas não são afetados

#### Scenario: Situação do cliente já visível na conferência

- **WHEN** a conferência é aberta
- **THEN** cada card informa, a partir do CNPJ do documento, se a empresa já é
  cliente cadastrado do escritório, sem esperar a etapa seguinte

#### Scenario: CNPJ informado para empresa não identificada

- **WHEN** o usuário informa o CNPJ no card de empresa não identificada e esse
  CNPJ é de outra empresa já presente no lote
- **THEN** as competências do card passam para o card dessa empresa, com a mesma
  regra de mescla por período da mesma empresa, e o card não identificado deixa
  de existir

#### Scenario: Empresa retirada do lote

- **WHEN** o usuário retira uma empresa do lote na conferência
- **THEN** o card dela some, nada dela é gravado, e as demais empresas
  continuam na conferência com os valores editados até ali

### Requirement: Identificação e gravação são resolvidas por empresa

O sistema DEVE (MUST) identificar o cliente, permitir o cadastro de cliente
novo, tratar o conflito com competência já gravada e gravar as apurações
**separadamente para cada empresa** do lote, cada empresa no seu próprio
cliente. A gravação de uma empresa NÃO DEVE (MUST NOT) depender do sucesso da
gravação das demais, e uma empresa já gravada com sucesso NÃO DEVE (MUST NOT)
ser regravada ao se tentar de novo as que falharam.

O pedido de gravação de cada empresa DEVE (MUST) levar a data de abertura do
cliente e o Nº da Declaração de cada competência lidos dos documentos **daquela
empresa**, e apenas deles. Empresa cujos documentos não trouxeram data de
abertura DEVE (MUST) ser gravada sem ela, mantendo a data já existente no
cadastro do cliente.

A regra de recusa e confirmação explícita de substituição ("Uma apuração por
cliente e competência") DEVE (MUST) valer por empresa: o conflito de uma
empresa é exibido e confirmado no card dela, sem bloquear nem substituir nada
nas outras.

O sistema DEVE (MUST) oferecer a gravação de todas as empresas prontas de uma
vez, e DEVE (MUST) deixar de fora dessa ação as empresas que ainda não têm
cliente identificado ou que estão com conflito pendente de confirmação.

#### Scenario: Gravação de lote com todas as empresas cadastradas

- **WHEN** todas as empresas do lote já são clientes do escritório e o usuário
  grava o lote
- **THEN** as competências de cada empresa são gravadas no cliente
  correspondente, e o resultado de cada empresa é exibido

#### Scenario: Data de abertura gravada só no cliente certo

- **WHEN** um lote com as empresas A e B é gravado, e só os documentos de A
  trouxeram data de abertura
- **THEN** a data de abertura é gravada no cliente de A, e o cliente de B
  mantém a data de abertura que já tinha (ou continua sem nenhuma)

#### Scenario: Empresa nova no meio do lote

- **WHEN** uma das empresas do lote ainda não é cliente do escritório
- **THEN** o card dela oferece o cadastro com razão social e código sugerido,
  e as empresas já cadastradas podem ser gravadas sem esperar esse cadastro

#### Scenario: Conflito em uma das empresas

- **WHEN** o lote é gravado e uma das empresas tem competência já gravada
- **THEN** apenas essa empresa é recusada, com as competências em conflito e a
  indicação de edição manual exibidas no card dela, enquanto as demais
  empresas são gravadas normalmente

#### Scenario: Substituição confirmada em uma empresa

- **WHEN** o usuário confirma a substituição no card da empresa em conflito
- **THEN** só as apurações dessa empresa são substituídas, e nenhuma outra
  empresa do lote é regravada

#### Scenario: Falha de gravação em uma empresa

- **WHEN** a gravação de uma das empresas falha por erro de rede ou do servidor
- **THEN** essa empresa é marcada com o erro e pode ser gravada de novo, sem
  reenviar as empresas que já foram gravadas

#### Scenario: Conclusão de lote com uma empresa

- **WHEN** o lote tinha uma única empresa e ela foi gravada
- **THEN** o usuário é levado à dashboard desse cliente, como numa importação
  de empresa única

#### Scenario: Conclusão de lote com várias empresas

- **WHEN** todas as empresas de um lote com várias empresas foram gravadas
- **THEN** a tela exibe o resumo do lote, com cada empresa, quantas
  competências foram gravadas e o acesso à dashboard de cada cliente
