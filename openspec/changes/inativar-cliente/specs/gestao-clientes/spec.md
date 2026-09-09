## ADDED Requirements

### Requirement: Cliente pode ser inativado e reativado sem exclusão

O sistema DEVE (MUST) manter, para cada cliente, uma situação booleana
ativo/inativo, independente da exclusão. Cliente novo, sem escolha explícita,
NASCE (MUST) ativo.

Na coluna de ações da listagem/busca de clientes, o sistema DEVE (MUST)
oferecer a ação "Inativar" para um cliente ativo, e a ação simétrica
"Reativar" para um cliente inativo — nunca as duas juntas na mesma linha.
Inativar ou reativar NÃO DEVE (MUST NOT) apagar nem alterar checklist de
onboarding, execuções ou qualquer outro dado do cliente.

#### Scenario: Inativar um cliente ativo

- **WHEN** o usuário aciona "Inativar" na linha de um cliente ativo
- **THEN** o cliente passa a ser inativo, continua existindo com todo o seu
  histórico, e a linha passa a oferecer "Reativar" em vez de "Inativar"

#### Scenario: Reativar um cliente inativo

- **WHEN** o usuário aciona "Reativar" na linha de um cliente inativo
- **THEN** o cliente volta a ser ativo, e a linha volta a oferecer
  "Inativar"

#### Scenario: Cliente novo nasce ativo

- **WHEN** um cliente é cadastrado, manualmente ou pelo agente, sem nenhuma
  escolha de situação
- **THEN** o cliente é criado como ativo

#### Scenario: Inativar preserva onboarding e execuções

- **WHEN** um cliente com checklist de onboarding e execuções registradas é
  inativado
- **THEN** o checklist e as execuções continuam associados a ele, inalterados

### Requirement: A listagem de clientes filtra por situação, e por padrão mostra só ativos

A tela de clientes DEVE (MUST) oferecer um controle de situação com três
opções mutuamente exclusivas: **Ativos**, **Inativos** e **Todos**.

Sem escolha explícita do usuário, a listagem DEVE (MUST) se comportar como se
"Ativos" estivesse selecionado — cliente inativo NÃO DEVE (MUST NOT) aparecer
por padrão. Este é o único controle da tela cuja ausência de escolha já
restringe o resultado; os demais filtros (busca, escritório, certificado,
regime, onboarding, 2FA), sem escolha, não restringem nada.

O controle DEVE (MUST) combinar com os demais filtros da tela, restringindo o
resultado a quem atende a todos ao mesmo tempo, e DEVE (MUST) estar
disponível para todos os papéis que enxergam a listagem. A paginação e o
total exibido DEVEM (MUST) refletir o conjunto filtrado, e escolher uma opção
DEVE (MUST) levar de volta à primeira página.

#### Scenario: Listagem sem filtro de situação escolhido

- **WHEN** o usuário abre a tela de clientes sem tocar no controle de situação
- **THEN** a listagem exibe apenas clientes ativos, e o total exibido reflete
  só eles

#### Scenario: Filtrar por inativos

- **WHEN** o usuário seleciona "Inativos"
- **THEN** a listagem exibe apenas os clientes inativos

#### Scenario: Filtrar por todos

- **WHEN** o usuário seleciona "Todos"
- **THEN** a listagem exibe clientes ativos e inativos juntos

#### Scenario: Situação combinada com a busca

- **WHEN** o usuário digita um termo de busca com "Inativos" selecionado
- **THEN** a listagem exibe apenas os clientes inativos cujo nome, código ou
  CNPJ mascarado atendem ao termo

#### Scenario: Situação disponível para o administrador

- **WHEN** um administrador de plataforma abre a tela de clientes
- **THEN** o controle de situação está disponível para ele como para os
  demais papéis, e combina com o filtro de escritório

#### Scenario: Troca de situação volta à primeira página

- **WHEN** o usuário está numa página adiante e troca a opção de situação
- **THEN** a listagem volta para a primeira página do conjunto filtrado

### Requirement: Cliente inativo não conta nos indicadores do painel

Os indicadores do painel (`DashboardEndpoints`) DEVEM (MUST) contar apenas
clientes ativos ao somar certificado a vencer ou onboarding, usando o mesmo
predicado que a listagem aplica por padrão. Um cliente inativo NÃO DEVE (MUST
NOT) ser contado nem aparecer na lista aberta ao clicar em um desses
indicadores.

#### Scenario: Certificado vencido de cliente inativo

- **WHEN** um cliente inativo tem certificado já vencido
- **THEN** o indicador de certificados vencidos do painel não conta esse
  cliente

#### Scenario: Onboarding de cliente inativo

- **WHEN** um cliente inativo está em fase de onboarding
- **THEN** o indicador de onboarding do painel não conta esse cliente

### Requirement: Cliente inativo continua contando para o limite de clientes do plano

Inativar um cliente NÃO DEVE (MUST NOT) liberar vaga no limite de clientes do
plano do escritório (`plano.MaxClientes`). O sistema DEVE (MUST) continuar
contando clientes inativos junto com os ativos ao verificar esse limite —
inativar não é excluir, e o registro continua ocupando espaço no escritório.

#### Scenario: Cadastro no limite com clientes inativos

- **WHEN** um escritório tem clientes inativos e ativos somando o limite do
  plano, e tenta cadastrar mais um cliente
- **THEN** o cadastro é recusado por limite atingido, do mesmo jeito que se
  todos fossem ativos

### Requirement: A sincronização do agente preserva a situação do cliente

A sincronização de clientes feita pelo agente NÃO DEVE (MUST NOT) alterar a
situação (ativo/inativo) de um cliente já existente, nem definir a situação
ao cadastrar um cliente novo além do padrão ativo.

O agente deriva o que sabe do nome e do conteúdo dos certificados na máquina
do escritório; a decisão de inativar é humana, tomada na tela. Se a
sincronização reativasse um cliente automaticamente ao encontrar o
certificado dele de novo, inativar deixaria de ser confiável — o cliente
reapareceria sozinho na próxima execução do agente.

#### Scenario: Sincronização de cliente inativo

- **WHEN** o agente sincroniza um cliente que já existe e está inativo
- **THEN** o cliente continua inativo depois da sincronização, ainda que
  nome, CNPJ ou validade do certificado tenham sido atualizados

#### Scenario: Cliente novo cadastrado pelo agente

- **WHEN** o agente cadastra um cliente que ainda não existia
- **THEN** o cliente nasce ativo, como qualquer outro cadastro novo
