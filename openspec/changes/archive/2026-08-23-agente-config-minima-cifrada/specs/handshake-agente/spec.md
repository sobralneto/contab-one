## MODIFIED Requirements

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

## ADDED Requirements

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
