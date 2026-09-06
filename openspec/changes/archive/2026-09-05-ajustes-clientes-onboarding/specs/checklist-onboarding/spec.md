## ADDED Requirements

### Requirement: "Cliente em fase de onboarding" é uma definição única

O sistema DEVE (MUST) considerar em fase de onboarding o cliente que tem modelo
de onboarding escolhido e cujo onboarding ainda não chegou a 100% — o que inclui
tanto o cliente cujo checklist ainda não foi criado quanto o cliente com
checklist abaixo de 100%. Cliente sem modelo escolhido NÃO DEVE (MUST NOT) ser
considerado em onboarding, porque não há o que implantar.

A definição DEVE (MUST) ser uma só, aplicada por igual em todo lugar que a use —
filtro de listagem, contagem de indicador ou qualquer consumidor futuro. Duas
definições que divirjam produzem um número de indicador que não bate com o
tamanho da lista que o usuário abre em seguida, e o usuário não tem como saber
qual das duas está certa.

O conjunto DEVE (MUST) respeitar o isolamento por escritório como qualquer outra
leitura de cliente: uma sessão só enxerga em onboarding os clientes do próprio
escritório.

#### Scenario: Cliente com modelo e sem checklist

- **WHEN** um cliente tem modelo de onboarding escolhido e ainda não teve o
  checklist criado
- **THEN** ele é considerado em fase de onboarding

#### Scenario: Cliente com checklist em andamento

- **WHEN** um cliente tem checklist com percentual de conclusão abaixo de 100
- **THEN** ele é considerado em fase de onboarding

#### Scenario: Cliente com onboarding concluído

- **WHEN** o percentual de conclusão do checklist de um cliente chega a 100
- **THEN** ele deixa de ser considerado em fase de onboarding

#### Scenario: Cliente sem modelo escolhido

- **WHEN** um cliente não tem modelo de onboarding escolhido
- **THEN** ele não é considerado em fase de onboarding, independentemente de
  qualquer outro dado

#### Scenario: Conclusão de tarefa muda a classificação na hora

- **WHEN** a última tarefa aberta do checklist de um cliente é marcada como
  concluída
- **THEN** o cliente deixa de aparecer entre os que estão em onboarding, sem
  depender de nenhum processamento posterior

#### Scenario: Cliente em onboarding de outro escritório

- **WHEN** uma sessão do escritório A consulta clientes em onboarding e o
  escritório B tem clientes nessa situação
- **THEN** os clientes de B não aparecem nem são contados

### Requirement: O hub lista os clientes em onboarding com o progresso de cada um

O hub DEVE (MUST) apresentar os clientes em fase de onboarding do escopo da
sessão, cada um com o nome e o percentual de conclusão do próprio checklist,
representado também de forma visual (barra de progresso) além do número.

O lugar é o hub, e NÃO a visão geral de uma ferramenta: onboarding é do cliente,
não de ferramenta alguma. Na visão geral de uma ferramenta, o escritório que não
usa aquela ferramenta nunca veria a informação.

Cliente com modelo escolhido e sem checklist criado DEVE (MUST) aparecer com 0%
— está em onboarding e não começou. A ordem DEVE (MUST) ser por progresso
decrescente, e não alfabética: quem está mais perto do fim é onde um empurrão
encerra a implantação.

A lista DEVE (MUST) ser limitada a poucos clientes para não dominar a tela
inicial, e, quando houver mais do que o exibido, DEVE (MUST) informar quantos
existem ao todo e oferecer caminho para a lista completa já filtrada por
onboarding. Não havendo truncamento, a informação de quantidade NÃO DEVE (MUST
NOT) ser exibida.

Cada cliente listado DEVE (MUST) dar acesso ao próprio checklist.

Não havendo nenhum cliente em onboarding, o hub DEVE (MUST) dizer isso
explicitamente — é uma boa notícia, não um erro nem um espaço vazio. Falhando a
carga, o cartão DEVE (MUST) sinalizar a falha sem derrubar o restante do hub,
como as demais colunas.

#### Scenario: Escritório com implantações em curso

- **WHEN** o usuário abre o hub e o escritório tem clientes em fase de onboarding
- **THEN** cada um aparece com o nome, o percentual e a barra de progresso
  correspondente

#### Scenario: Cliente que ainda não começou

- **WHEN** um cliente tem modelo escolhido e nenhum checklist criado
- **THEN** ele aparece na lista com 0%

#### Scenario: Ordem por progresso

- **WHEN** a lista tem clientes com percentuais diferentes
- **THEN** eles são apresentados do maior percentual para o menor,
  independentemente do nome

#### Scenario: Mais clientes do que o hub exibe

- **WHEN** há mais clientes em onboarding do que o hub apresenta
- **THEN** o hub informa quantos estão sendo exibidos de quantos existem, e
  oferece caminho para a listagem completa já filtrada

#### Scenario: Lista que cabe inteira

- **WHEN** todos os clientes em onboarding cabem na lista do hub
- **THEN** nenhuma informação de truncamento é exibida

#### Scenario: Acesso ao checklist a partir do hub

- **WHEN** o usuário aciona um cliente da lista
- **THEN** a aplicação abre o checklist de onboarding daquele cliente

#### Scenario: Escritório que não usa NFS-e

- **WHEN** o escritório em foco não tem a ferramenta de NFS-e contratada
- **THEN** a lista de onboarding continua visível no hub

#### Scenario: Nenhum cliente em onboarding

- **WHEN** nenhum cliente do escopo está em fase de onboarding
- **THEN** o hub informa que não há cliente em implantação, em vez de exibir um
  espaço vazio

#### Scenario: Falha ao carregar

- **WHEN** a carga da lista falha
- **THEN** o cartão sinaliza a falha e o restante do hub continua de pé

#### Scenario: Coerência com a listagem

- **WHEN** o usuário abre a listagem de clientes a partir do hub
- **THEN** a listagem já vem filtrada por onboarding, e o conjunto exibido é o
  mesmo que originou a lista do hub
