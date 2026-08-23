## Purpose

Ajusta a tela de execuções para exibir agrupamento por escritório (visão admin) com detalhamento expansível e métricas por cliente (visão escritório).

## Requirements

### Requirement: Agrupamento por escritório na visão admin

Na visão admin da tela de execuções, o sistema DEVE (MUST) agrupar as execuções por escritório e permitir expandir cada grupo para ver o detalhamento.

#### Scenario: Admin visualiza execuções agrupadas

- **WHEN** um admin acessa a tela de execuções
- **THEN** as execuções são exibidas agrupadas por escritório, com indicadores sumarizados por grupo

#### Scenario: Admin expande detalhamento de um escritório

- **WHEN** o admin clica para expandir um grupo de escritório
- **THEN** o sistema exibe as execuções detalhadas daquele escritório

### Requirement: Métricas por cliente na visão escritório

Na visão escritório da tela de execuções, o sistema DEVE (MUST) exibir métricas agregadas por cliente.

#### Scenario: Escritório visualiza métricas por cliente

- **WHEN** um escritório acessa a tela de execuções
- **THEN** as métricas de execução (total, sucesso, falha) são exibidas por cliente
