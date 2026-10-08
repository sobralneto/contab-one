## ADDED Requirements

### Requirement: A página permite ler o texto de uma mensagem

A página de mensagens DET DEVE (MUST) permitir abrir uma mensagem da lista e
ler o seu texto completo, junto com cliente, assunto, remetente, data de
envio e prazo. Quando a mensagem não tem texto armazenado, a página DEVE
(MUST) dizer isso explicitamente, em vez de mostrar uma área vazia.

A página NÃO DEVE (MUST NOT) exibir a situação de leitura da mensagem.

#### Scenario: Usuário abre uma mensagem com texto

- **WHEN** o usuário aciona a leitura de uma mensagem que tem texto
- **THEN** o texto completo é exibido, preservando as quebras de linha

#### Scenario: Usuário abre uma mensagem sem texto

- **WHEN** o usuário aciona a leitura de uma mensagem sem texto armazenado
- **THEN** a página informa que o texto não foi capturado

#### Scenario: Lista sem a situação

- **WHEN** o usuário abre a página de mensagens
- **THEN** a lista não tem coluna de situação
