## ADDED Requirements

### Requirement: A visão geral filtra por cliente escolhido numa lista

A visão geral do PGDAS-D (`/f/pgdas`) DEVE (MUST) oferecer o filtro "Cliente"
como um campo de seleção (select), e NÃO DEVE (MUST NOT) mais oferecer um
campo de texto livre para buscar cliente. As opções DEVEM (MUST) ser:

- "Todos os clientes", selecionada por padrão, que não restringe a lista;
- um item por cliente do escritório da sessão que tenha ao menos uma
  apuração gravada, exibido como "código — nome" e ordenado por nome.

Escolher um cliente DEVE (MUST) recarregar a lista principal a partir do
servidor restrita a esse cliente (`GET /api/pgdas/apuracoes?clienteId=…`),
combinando com os filtros de competência inicial e final. O filtro de cliente
NÃO DEVE (MUST NOT) depender das apurações já carregadas em memória: um
cliente cujas apurações ficaram fora da amostra truncada da lista geral DEVE
(MUST) aparecer no select e, quando escolhido, ter suas apurações listadas.

Os indicadores do topo (KPIs do resumo) continuam refletindo o escritório
inteiro, independentemente do cliente escolhido. A sidebar de detalhe continua
carregando todas as competências do cliente, como definido em "A sidebar
mostra a identidade do cliente e o histórico de competências".

#### Scenario: Select lista os clientes com apuração

- **WHEN** o escritório tem os clientes "ALFA" e "BETA" com apurações gravadas
  e o cliente "GAMA" sem nenhuma apuração, e o usuário abre a visão geral
- **THEN** o filtro "Cliente" é um select com "Todos os clientes", "ALFA" e
  "BETA", nessa ordem, e não lista "GAMA"

#### Scenario: Padrão mostra todos

- **WHEN** o usuário abre a visão geral sem mexer no filtro
- **THEN** o select está em "Todos os clientes" e a lista mostra uma linha por
  cliente com apuração

#### Scenario: Escolher um cliente restringe a lista

- **WHEN** o usuário escolhe "ALFA" no select
- **THEN** a lista é recarregada do servidor com `clienteId` de ALFA e mostra
  só a linha de ALFA

#### Scenario: Cliente combinado com competência

- **WHEN** o usuário escolhe "ALFA" e define a competência de 2026-06 a 2026-08
- **THEN** a lista considera só as apurações de ALFA nesse intervalo, e mostra
  o estado vazio se ALFA não tem apuração nele

#### Scenario: Voltar para todos

- **WHEN** com "ALFA" escolhido, o usuário volta o select para "Todos os
  clientes"
- **THEN** a lista volta a mostrar uma linha por cliente com apuração

#### Scenario: Cliente fora da amostra truncada

- **WHEN** a lista geral está truncada e o cliente "ZETA" só tem apurações
  antigas que ficaram fora da amostra
- **THEN** "ZETA" aparece no select e, quando escolhido, suas apurações são
  listadas

#### Scenario: KPIs não seguem o filtro de cliente

- **WHEN** o usuário escolhe um cliente no select
- **THEN** os indicadores do topo continuam mostrando os totais do escritório

### Requirement: A API lista os clientes com apuração do escritório

O sistema DEVE (MUST) expor `GET /api/pgdas/clientes`, que devolve os clientes
do escritório da sessão com ao menos uma apuração gravada, cada um com `id`,
`codigo` e `nome`, ordenados por nome, sem paginação e sem repetição. O
escopo DEVE (MUST) vir sempre do escritório da sessão, nunca de parâmetro do
pedido; sem escritório na sessão, o endpoint DEVE (MUST) responder 403, como
os demais endpoints da ferramenta. A resposta NÃO DEVE (MUST NOT) incluir CNPJ
nem qualquer valor fiscal.

#### Scenario: Lista sem repetição e ordenada

- **WHEN** o escritório tem "BETA" com três competências e "ALFA" com uma
- **THEN** a resposta traz exatamente dois itens, "ALFA" antes de "BETA"

#### Scenario: Cliente sem apuração fica de fora

- **WHEN** o escritório tem um cliente sem nenhuma apuração gravada
- **THEN** esse cliente não aparece na resposta

#### Scenario: Isolamento por escritório

- **WHEN** um usuário do escritório A chama o endpoint e o escritório B tem
  clientes com apuração
- **THEN** a resposta não contém nenhum cliente do escritório B

#### Scenario: Sessão sem escritório

- **WHEN** um administrador da plataforma sem escritório em foco chama o
  endpoint
- **THEN** a resposta é 403
