## Purpose

Corrige os gráficos e o escopo de dados da tela de dashboard para que cada papel de usuário (admin, escritório, usuário final) visualize as informações corretas e com os rótulos adequados nos eixos.

## Requirements

### Requirement: Gráfico de notas por mês exibe rótulo contextual

O sistema DEVE (MUST) exibir no eixo X do gráfico de notas por mês o nome da entidade relevante conforme o papel do usuário logado, e NÃO a data.

#### Scenario: Admin visualiza dashboard

- **WHEN** um usuário com papel admin acessa o dashboard
- **THEN** o gráfico de notas por mês exibe o nome de cada escritório no eixo X

#### Scenario: Escritório visualiza dashboard

- **WHEN** um usuário com papel escritório acessa o dashboard
- **THEN** o gráfico de notas por mês exibe o nome de cada cliente no eixo X

#### Scenario: Usuário final visualiza dashboard

- **WHEN** um usuário com papel usuário acessa o dashboard
- **THEN** o gráfico de notas por mês exibe o nome de cada cliente no eixo X

### Requirement: Dados do dashboard com escopo por papel

O sistema DEVE (MUST) agregar todos os dados exibidos no dashboard conforme o papel do usuário: admin visualiza dados por escritório, escritório e usuário visualizam dados por cliente.

#### Scenario: Dashboard admin agrega por escritório

- **WHEN** um admin acessa o dashboard
- **THEN** todos os indicadores (cards, gráficos, tabelas) exibem dados agregados por escritório

#### Scenario: Dashboard escritório agrega por cliente

- **WHEN** um escritório acessa o dashboard
- **THEN** todos os indicadores exibem dados agregados por cliente daquele escritório

#### Scenario: Dashboard usuário agrega por cliente

- **WHEN** um usuário final acessa o dashboard
- **THEN** todos os indicadores exibem dados agregados por cliente vinculado ao usuário

### Requirement: Filtro de escritório na visão admin

Na visão admin do dashboard, o sistema DEVE (MUST) oferecer um filtro por escritório (em vez de por cliente) que restringe os dados do gráfico.

#### Scenario: Admin filtra por escritório

- **WHEN** o admin seleciona um escritório no filtro do dashboard
- **THEN** o gráfico exibe apenas as notas daquele escritório

#### Scenario: Admin filtra por período e escritório

- **WHEN** o admin seleciona um período e um escritório no filtro do dashboard
- **THEN** o gráfico reflete o período e o escritório selecionados

### Requirement: Ranking por escritório na visão admin

Na visão admin do dashboard, o sistema DEVE (MUST) exibir o ranking agregado por escritório, com os escritórios ordenados pelo total de notas.

#### Scenario: Admin visualiza o ranking

- **WHEN** um admin acessa o dashboard
- **THEN** o card de ranking exibe "Ranking de escritórios" com os escritórios ordenados pelo total de notas baixadas
