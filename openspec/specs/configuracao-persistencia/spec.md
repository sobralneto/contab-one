## Purpose

Corrige o erro que impede o salvamento de configurações na visão admin, garantindo que as alterações sejam persistidas com sucesso.

## Requirements

### Requirement: Salvamento de configuração funcional

O sistema DEVE (MUST) permitir que um admin salve as configurações da plataforma sem erros, persistindo os valores corretamente.

#### Scenario: Admin salva configuração com sucesso

- **WHEN** o admin altera uma configuração e clica em salvar
- **THEN** a configuração é persistida e uma mensagem de sucesso é exibida

#### Scenario: Admin tenta salvar configuração inválida

- **WHEN** o admin insere um valor inválido em um campo de configuração e tenta salvar
- **THEN** o sistema exibe uma mensagem de erro indicando o campo problemático

### Requirement: Configuração salva é entregue ao agente

A configuração persistida na tela de configuração DEVE (MUST) ser entregue ao agente do escritório e aplicada a partir da execução seguinte. A tela DEVE descrever com precisão quando as alterações passam a valer.

Hoje a tela afirma que o agente lê essas configurações no handshake, mas nenhum valor salvo chega até ele — os campos são dados somente de escrita.

#### Scenario: Escritório altera os tipos de nota

- **WHEN** um escritório salva a configuração alterando os tipos de nota a coletar
- **THEN** o próximo handshake de um agente desse escritório entrega os novos tipos, e a execução seguinte os utiliza

#### Scenario: Escritório desliga a geração de PDF

- **WHEN** um escritório salva a configuração desligando a geração de DANFSe em PDF
- **THEN** a execução seguinte do agente baixa os XML sem gerar os PDF correspondentes

#### Scenario: Configuração de um escritório não afeta outro

- **WHEN** dois escritórios distintos possuem configurações diferentes
- **THEN** cada agente recebe no handshake apenas a configuração do seu próprio escritório

### Requirement: Limites do plano visíveis na tela são efetivos

Os limites de plano exibidos na tela de configuração DEVEM (MUST) corresponder ao que é efetivamente aplicado na coleta, e não apenas desabilitar controles na interface.

#### Scenario: Plano sem permissão para emitidas

- **WHEN** a tela exibe o plano como não permitindo notas emitidas
- **THEN** o agente desse escritório não coleta notas emitidas, independentemente do que estiver salvo na configuração ou no arquivo local
