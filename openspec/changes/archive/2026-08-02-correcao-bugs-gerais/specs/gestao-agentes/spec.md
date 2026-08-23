## Purpose

Corrige a tela de agentes para que, na visão admin, a geração de nova chave solicite a seleção do escritório e a tabela exiba o nome do escritório.

## ADDED Requirements

### Requirement: Modal de seleção de escritório ao gerar chave

Na visão admin da tela de agentes, ao clicar em "Nova Chave", o sistema DEVE abrir um modal para que o admin selecione o escritório ao qual a chave será vinculada antes de gerá-la.

#### Scenario: Admin gera nova chave com seleção de escritório

- **WHEN** o admin clica em "Nova Chave" na tela de agentes
- **THEN** um modal é exibido com a lista de escritórios para seleção

#### Scenario: Admin confirma geração de chave

- **WHEN** o admin seleciona um escritório e confirma no modal
- **THEN** a chave é gerada e vinculada ao escritório selecionado

### Requirement: Nome do escritório na tabela de agentes

Na visão admin da tela de agentes, o sistema DEVE exibir o nome do escritório associado a cada agente na tabela.

#### Scenario: Tabela de agentes como admin

- **WHEN** um admin acessa a tela de agentes
- **THEN** a tabela exibe uma coluna com o nome do escritório de cada agente

### Requirement: Data de criação e ordenação da tabela de agentes

A tabela de agentes DEVE exibir a data de criação de cada chave, com a listagem ordenada da chave mais recente para a mais antiga.

#### Scenario: Visualização da tabela de agentes

- **WHEN** um usuário acessa a tela de agentes
- **THEN** a tabela exibe uma coluna "Criado em" com a data de criação de cada chave, ordenada da mais recente para a mais antiga
