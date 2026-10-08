## REMOVED Requirements

### Requirement: O CNPJ do documento nunca é persistido inteiro

**Reason**: Revertido pela change `cnpj-completo-cliente` — a plataforma
passa a persistir o CNPJ completo do cliente quando ele está disponível, em
vez de descartá-lo depois de derivar hash e máscara.

**Migration**: Ver o requirement ADDED "O CNPJ completo é persistido e a
dashboard o exibe quando disponível", nesta mesma capability.

## ADDED Requirements

### Requirement: O CNPJ completo é persistido e a dashboard o exibe quando disponível

Ao gravar uma competência a partir de um documento, o sistema DEVE (MUST)
persistir o CNPJ completo lido do documento no cliente correspondente, junto
com o hash de identificação e a versão mascarada.

A dashboard do cliente (`/f/pgdas/dashboard/{clienteId}`) DEVE (MUST) exibir
o CNPJ completo do cliente quando ele estiver disponível, e DEVE (MUST) cair
de volta para a versão mascarada quando não estiver. Nem todo cliente tem o
CNPJ completo disponível: os cadastrados antes desta mudança, e os só
sincronizados por um agente que ainda não envia o CNPJ completo, continuam
apenas com hash e máscara — não há como completá-los retroativamente.

A exportação em HTML e em PDF, por serem o mesmo documento que a tela (ver
"A identidade visual da dashboard vem do escritório"), seguem a mesma regra:
CNPJ completo quando disponível, máscara como fallback.

#### Scenario: Documento gravado para cliente com CNPJ completo disponível

- **WHEN** uma competência é gravada a partir de um documento cujo cliente já
  tem o CNPJ completo persistido
- **THEN** a dashboard desse cliente exibe o CNPJ completo

#### Scenario: Documento traz o CNPJ completo pela primeira vez

- **WHEN** uma competência é gravada a partir de um documento, e o CNPJ lido
  bate com um cliente que ainda não tinha o CNPJ completo persistido
- **THEN** o CNPJ completo passa a ser persistido nesse cliente

#### Scenario: Cliente sem CNPJ completo disponível

- **WHEN** a dashboard é montada para um cliente que só tem hash e máscara
  gravados, sem o CNPJ completo
- **THEN** a dashboard exibe a versão mascarada, sem erro

#### Scenario: Exportação segue a mesma regra de exibição

- **WHEN** o usuário exporta em HTML ou em PDF a dashboard de um cliente com
  CNPJ completo disponível
- **THEN** o arquivo exportado exibe o CNPJ completo, igual à tela
