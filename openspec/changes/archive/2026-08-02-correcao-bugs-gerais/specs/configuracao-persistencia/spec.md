## Purpose

Corrige o erro que impede o salvamento de configurações na visão admin, garantindo que as alterações sejam persistidas com sucesso.

## ADDED Requirements

### Requirement: Salvamento de configuração funcional

O sistema DEVE permitir que um admin salve as configurações da plataforma sem erros, persistindo os valores corretamente.

#### Scenario: Admin salva configuração com sucesso

- **WHEN** o admin altera uma configuração e clica em salvar
- **THEN** a configuração é persistida e uma mensagem de sucesso é exibida

#### Scenario: Admin tenta salvar configuração inválida

- **WHEN** o admin insere um valor inválido em um campo de configuração e tenta salvar
- **THEN** o sistema exibe uma mensagem de erro indicando o campo problemático
