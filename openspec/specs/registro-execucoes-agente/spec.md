## Purpose

Cobre o registro de uma execução do agente na plataforma — abertura, envio de métricas por cliente e finalização com status — e os alertas derivados dela, de forma que o painel reflita fielmente o que aconteceu na máquina do escritório.

## Requirements

### Requirement: Execução pode ser finalizada em qualquer status

A API DEVE (MUST) aceitar a finalização de uma execução em qualquer status válido, incluindo falha, registrando o status, a mensagem de erro e o instante de término.

#### Scenario: Agente finaliza execução com falha

- **WHEN** o agente finaliza uma execução informando status de falha e uma mensagem de erro
- **THEN** a execução é persistida com esse status, a mensagem e o instante de término, e a resposta é bem-sucedida

#### Scenario: Agente finaliza execução com sucesso

- **WHEN** o agente finaliza uma execução informando status de sucesso
- **THEN** a execução é persistida com esse status e o instante de término

#### Scenario: Agente finaliza execução parcial

- **WHEN** o agente finaliza uma execução informando status parcial
- **THEN** a execução é persistida com esse status e a mensagem de erro correspondente

### Requirement: Falha de execução abre alerta sem duplicar

Ao receber a finalização de uma execução com falha, o sistema DEVE (MUST) abrir um alerta crítico para o escritório, e DEVE evitar criar um segundo alerta do mesmo tipo enquanto já houver um aberto.

#### Scenario: Primeira falha do escritório

- **WHEN** uma execução é finalizada com falha e não há alerta de execução falhada aberto para o escritório
- **THEN** um alerta crítico de execução falhada é criado

#### Scenario: Falha subsequente com alerta já aberto

- **WHEN** uma execução é finalizada com falha e já existe alerta de execução falhada aberto para o escritório
- **THEN** nenhum alerta novo é criado e a finalização continua sendo bem-sucedida

#### Scenario: Falha após o alerta anterior ter sido resolvido

- **WHEN** uma execução é finalizada com falha e o alerta anterior do mesmo tipo já foi resolvido
- **THEN** um novo alerta crítico é criado

### Requirement: A varredura diária de alertas percorre todos os escritórios

O job diário de alertas DEVE (MUST) percorrer todos os escritórios ativos e avaliar certificados vencidos, certificados a vencer em até 30 dias e agentes silenciosos, sem interromper a varredura por conta da avaliação de um escritório.

#### Scenario: Varredura com certificados em estados variados

- **WHEN** o job diário roda sobre escritórios com certificados vencidos, a vencer e válidos
- **THEN** alertas são criados para os vencidos e para os a vencer, e nenhum alerta é criado para os válidos

#### Scenario: Escritório sem execução recente

- **WHEN** um escritório com agentes ativos não registra execução há mais de três dias
- **THEN** um alerta de agente silencioso é aberto para esse escritório

#### Scenario: Job roda duas vezes no mesmo dia

- **WHEN** o job diário roda novamente sobre um estado inalterado
- **THEN** nenhum alerta duplicado é criado

### Requirement: Falha no envio do relatório não perde métricas nem duplica execuções

O agente DEVE (MUST) preservar localmente o relatório que não conseguiu enviar e reenviá-lo na execução seguinte, e o reenvio não DEVE deixar execuções abertas acumuladas no painel quando a falha se repetir.

#### Scenario: Envio falha e é retomado na execução seguinte

- **WHEN** o envio do relatório falha por indisponibilidade da API e a execução seguinte encontra a API disponível
- **THEN** o relatório pendente é enviado e removido da fila local

#### Scenario: Falha persistente por mais de trinta dias

- **WHEN** um relatório pendente não consegue ser enviado por mais de trinta dias
- **THEN** ele é descartado com registro em log, sem interromper a execução corrente
