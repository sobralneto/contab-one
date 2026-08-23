## Purpose

Define os tetos e as listas de valores aceitos nas entradas que hoje a API recebe sem limite, para que um pedido isolado não consiga inchar o banco, derrubar o serviço nem plantar conteúdo arbitrário no que é repassado ao agente.

## ADDED Requirements

### Requirement: A configuração do escritório aceita apenas chaves conhecidas

O sistema DEVE (MUST) recusar chaves de configuração fora do conjunto reconhecido pela plataforma, e DEVE (MUST) limitar o tamanho de cada valor gravado.

A configuração salva é repassada ao agente no handshake; aceitar chave e valor arbitrários é entregar conteúdo não validado a um programa que roda na máquina do escritório.

#### Scenario: Configuração com chave desconhecida

- **WHEN** um administrador de escritório salva configuração incluindo uma chave fora do conjunto reconhecido
- **THEN** a gravação é recusada indicando a chave não reconhecida, e nenhuma configuração é alterada

#### Scenario: Configuração com valor acima do tamanho permitido

- **WHEN** um administrador salva uma configuração cujo valor excede o tamanho máximo
- **THEN** a gravação é recusada indicando o campo e o limite

#### Scenario: Configuração válida

- **WHEN** um administrador salva apenas chaves reconhecidas com valores dentro do limite
- **THEN** a configuração é gravada e passa a valer no próximo handshake do escritório

### Requirement: As listas enviadas pelo agente têm teto

O sistema DEVE (MUST) impor um número máximo de itens por pedido nos endpoints que recebem listas do agente — clientes e métricas de execução — e DEVE (MUST) recusar de forma explícita o pedido que exceder esse limite, informando o teto.

#### Scenario: Agente envia lista acima do teto

- **WHEN** um agente envia uma lista de clientes ou de métricas com mais itens que o máximo permitido
- **THEN** a API recusa o pedido informando o limite, e nada é gravado

#### Scenario: Agente envia lista dentro do teto

- **WHEN** um agente envia uma lista dentro do máximo permitido
- **THEN** os itens são processados normalmente

### Requirement: O custo de processar uma lista cresce com a lista, não com o banco

O sistema DEVE (MUST) processar uma lista recebida do agente com um número de consultas ao banco que não cresça proporcionalmente ao número de itens da lista.

#### Scenario: Envio de lista cheia no teto

- **WHEN** um agente envia uma lista de itens no limite permitido
- **THEN** o pedido é concluído dentro do tempo normal de resposta da API, sem uma consulta por item
