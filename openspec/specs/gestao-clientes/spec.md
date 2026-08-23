## Purpose

Corrige o fluxo de cadastro de clientes e adiciona filtros e colunas contextuais por papel (admin vê escritório responsável, escritório filtra por vencimento de certificado).

## Requirements

### Requirement: Cadastro de novo cliente funcional

O sistema DEVE (MUST) permitir que um usuário cadastre um novo cliente com sucesso, persistindo todos os campos do formulário.

#### Scenario: Cadastro de cliente com dados válidos

- **WHEN** o usuário preenche todos os campos obrigatórios do formulário de novo cliente e clica em salvar
- **THEN** o cliente é criado e aparece na listagem de clientes

#### Scenario: Cadastro com campos obrigatórios ausentes

- **WHEN** o usuário tenta salvar um cliente sem preencher campos obrigatórios
- **THEN** o sistema exibe mensagens de validação indicando os campos faltantes

### Requirement: Coluna de escritório na visão admin

Na listagem de clientes da visão admin, o sistema DEVE (MUST) exibir uma coluna com o nome do escritório responsável por cada cliente.

#### Scenario: Tabela de clientes como admin

- **WHEN** um admin acessa a tela de clientes
- **THEN** a tabela exibe uma coluna "Escritório" com o nome do escritório vinculado a cada cliente

### Requirement: Filtro por escritório na visão admin

Na visão admin da tela de clientes, o sistema DEVE (MUST) oferecer um filtro para selecionar um escritório específico e filtrar a listagem.

#### Scenario: Admin filtra clientes por escritório

- **WHEN** o admin seleciona um escritório no filtro
- **THEN** a tabela exibe apenas os clientes vinculados ao escritório selecionado

### Requirement: Filtro por vencimento de certificado na visão escritório

Na visão escritório da tela de clientes, o sistema DEVE (MUST) oferecer um controle de dias para filtrar clientes cujo certificado digital vencerá dentro do período selecionado (1, 2, 3, 7 ou 15 dias).

#### Scenario: Escritório filtra por vencimento em 7 dias

- **WHEN** o escritório seleciona "7 dias" no filtro de vencimento de certificado
- **THEN** a tabela exibe apenas clientes cujo certificado vence nos próximos 7 dias

#### Scenario: Escritório limpa filtro de vencimento

- **WHEN** o escritório remove o filtro de vencimento de certificado
- **THEN** a tabela volta a exibir todos os clientes do escritório
