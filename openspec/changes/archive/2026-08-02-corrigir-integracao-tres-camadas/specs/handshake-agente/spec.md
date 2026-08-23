## Purpose

Define o contrato de identificação do agente com a plataforma: o que a API entrega em cada handshake para que o agente saiba se pode executar, com quais regras, sob quais limites de plano e com qual configuração do escritório.

## ADDED Requirements

### Requirement: A chave de ofuscação de CNPJ é sempre entregue

O sistema DEVE (MUST) garantir que o handshake entregue uma chave HMAC de CNPJ não-vazia. A ausência da chave na configuração da API DEVE impedir a inicialização do serviço, em vez de produzir handshakes incompletos.

Sem essa chave o agente não consegue calcular o identificador estável de cada cliente e deixa de enviar o relatório inteiro da execução — uma falha que hoje só aparece como aviso em log local.

#### Scenario: API sobe sem a chave configurada

- **WHEN** a API é iniciada sem a variável de ambiente da chave HMAC de CNPJ
- **THEN** a inicialização falha com mensagem explícita indicando a variável faltante

#### Scenario: Handshake bem-sucedido

- **WHEN** um agente com chave válida faz handshake em uma API corretamente configurada
- **THEN** a resposta inclui a chave HMAC de CNPJ não-vazia

### Requirement: O handshake entrega a configuração do escritório

O handshake DEVE (MUST) incluir a configuração vigente do escritório do agente, cobrindo ao menos os tipos de nota a coletar, a data inicial de backfill para clientes novos, a pasta de saída sugerida e se o DANFSe em PDF deve ser gerado.

#### Scenario: Escritório com configuração salva

- **WHEN** um agente de um escritório que possui configuração salva faz handshake
- **THEN** a resposta inclui os valores dessa configuração

#### Scenario: Escritório sem configuração salva

- **WHEN** um agente de um escritório que nunca salvou configuração faz handshake
- **THEN** a resposta indica ausência de configuração, e o agente segue com os valores do seu arquivo local

### Requirement: O agente aplica a configuração recebida sobre a local

O agente DEVE (MUST) aplicar a configuração recebida no handshake por cima da configuração do seu arquivo local, mantendo o arquivo local como origem dos valores que o servidor não informar.

#### Scenario: Servidor informa tipos diferentes do arquivo local

- **WHEN** o handshake informa tipos de nota diferentes dos configurados localmente
- **THEN** a execução usa os tipos informados pelo servidor e registra em log que a configuração remota foi aplicada

#### Scenario: Agente opera em carência offline

- **WHEN** o agente não consegue contato com a API e opera dentro da carência offline
- **THEN** a execução usa a última configuração recebida do servidor, e o arquivo local supre o que não estiver em cache

#### Scenario: Agente sem seção de API configurada

- **WHEN** o agente roda sem credenciais de API configuradas
- **THEN** nenhuma chamada de rede à plataforma é feita e a configuração local é usada integralmente

### Requirement: O agente respeita os limites do plano

O agente DEVE (MUST) deixar de coletar notas emitidas quando o plano informado no handshake não permitir esse tipo, mesmo que a configuração local ou remota o solicite.

#### Scenario: Plano não cobre notas emitidas

- **WHEN** o handshake informa um plano sem permissão para emitidas e a configuração pede emitidas
- **THEN** o agente coleta apenas recebidas e registra em log que emitidas foi descartada por limite de plano

#### Scenario: Plano cobre notas emitidas

- **WHEN** o handshake informa um plano com permissão para emitidas e a configuração pede emitidas
- **THEN** o agente coleta os dois tipos normalmente

#### Scenario: Handshake não informa plano

- **WHEN** o handshake não traz informação de plano
- **THEN** o agente não aplica restrição adicional e segue a configuração vigente
