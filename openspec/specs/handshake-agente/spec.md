## Purpose

Define o contrato de identificação do agente com a plataforma: o que a API entrega em cada handshake para que o agente saiba se pode executar, com quais regras, sob quais limites de plano e com qual configuração do escritório.

## Requirements

### Requirement: A chave de ofuscação de CNPJ é sempre entregue

O sistema DEVE (MUST) garantir que o handshake **de um agente autenticado** entregue uma chave HMAC de CNPJ não-vazia. A ausência da chave na configuração da API DEVE impedir a inicialização do serviço, em vez de produzir handshakes incompletos.

A chave DEVE (MUST) ser entregue exclusivamente por essa via: nenhuma sessão humana do painel, de qualquer papel, DEVE (MUST NOT) conseguir obtê-la por endpoint algum. A chave é a mesma para toda a plataforma e o espaço de CNPJ é pequeno o bastante para ser varrido por força bruta — quem a obtém reverte todo `CnpjHash` gravado e derruba a premissa de que o CNPJ nunca é persistido.

Sem essa chave o agente não consegue calcular o identificador estável de cada cliente e deixa de enviar o relatório inteiro da execução — uma falha que hoje só aparece como aviso em log local.

#### Scenario: API sobe sem a chave configurada

- **WHEN** a API é iniciada sem a variável de ambiente da chave HMAC de CNPJ
- **THEN** a inicialização falha com mensagem explícita indicando a variável faltante

#### Scenario: Handshake bem-sucedido

- **WHEN** um agente com chave válida faz handshake em uma API corretamente configurada
- **THEN** a resposta inclui a chave HMAC de CNPJ não-vazia

#### Scenario: Usuário do painel tenta o handshake

- **WHEN** um usuário autenticado no painel, de qualquer papel, chama o handshake
- **THEN** a API responde 403 e a chave HMAC de CNPJ não aparece em resposta alguma

### Requirement: O handshake entrega a configuração do escritório

O handshake DEVE (MUST) incluir a configuração vigente do escritório do
agente, cobrindo ao menos os tipos de nota a coletar, a data inicial de
backfill para clientes novos, a pasta de saída sugerida e se o DANFSe em PDF
deve ser gerado. Esse bloco DEVE (MUST) viajar cifrado — nunca como JSON em
claro — usando uma chave simétrica que só a API e o agente conseguem
derivar, sem exigir nenhum segredo adicional configurado em `config.toml` ou
nas variáveis de ambiente da API.

#### Scenario: Escritório com configuração salva

- **WHEN** um agente de um escritório que possui configuração salva faz
  handshake
- **THEN** a resposta inclui o envelope cifrado contendo os valores dessa
  configuração, decifrável com a chave derivada da API key do agente

#### Scenario: Escritório sem configuração salva

- **WHEN** um agente de um escritório que nunca salvou configuração faz
  handshake
- **THEN** a resposta indica ausência de configuração, e o agente segue com
  os valores do seu arquivo local

### Requirement: A chave de cifragem da configuração é derivada da API key do agente

O sistema DEVE (MUST) derivar deterministicamente a chave simétrica usada
para cifrar/decifrar o bloco `configuracao` do handshake a partir da API key
do agente que fez a requisição (o mesmo segredo já usado para autenticar via
`X-Api-Key`), e NÃO DEVE (MUST NOT) usar um segredo adicional persistido ou
distribuído separadamente.

#### Scenario: API monta a resposta do handshake

- **WHEN** a API recebe um handshake autenticado com uma API key válida
- **THEN** ela deriva a chave de cifragem a partir do valor bruto dessa API
  key (disponível no request, nunca persistido em claro) e cifra o bloco de
  configuração com ela

#### Scenario: Agente decifra a resposta

- **WHEN** o agente recebe a resposta do handshake
- **THEN** ele deriva a mesma chave a partir da API key configurada
  localmente e decifra o bloco sem qualquer troca de chave adicional com o
  servidor

### Requirement: Falha ao decifrar a configuração remota não interrompe a execução

O agente DEVE (MUST) tratar falha ao decifrar ou interpretar o bloco de
configuração do handshake (chave incompatível, payload corrompido, ou campo
ausente por incompatibilidade de versão) como configuração remota ausente —
registrar um aviso em log e prosseguir com a configuração local e/ou o
último valor válido em cache — e NÃO DEVE (MUST NOT) interromper a execução
por causa disso.

#### Scenario: Payload cifrado corrompido

- **WHEN** o bloco `configuracaoCifrada` recebido não decifra com a chave
  derivada da API key local
- **THEN** o agente registra um aviso em log e usa a configuração do
  `config.toml` local para essa execução

#### Scenario: API antiga sem o campo cifrado

- **WHEN** a resposta do handshake não contém o campo de configuração
  cifrada
- **THEN** o agente segue normalmente com a configuração local, sem
  registrar erro

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
