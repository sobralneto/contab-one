## ADDED Requirements

### Requirement: Leiaute da dashboard é escolhido no cadastro do escritório

O sistema DEVE (MUST) permitir que o admin da plataforma escolha, no cadastro e
na edição de um escritório, qual dos leiautes da dashboard de apuração será
usado nos documentos daquele escritório. Os leiautes são três e fixos: o neutro
da plataforma, o da L&J e o da MUDAHR.

A escolha DEVE (MUST) ser persistida como atributo do próprio escritório, junto
com nome, CNPJ, plano e status, e DEVE (MUST) sobreviver ao fechamento e à
reabertura do modal.

#### Scenario: Admin escolhe um leiaute de marca ao editar

- **WHEN** o admin abre a edição de um escritório, escolhe o leiaute da MUDAHR e
  salva
- **THEN** o escritório passa a ter esse leiaute, e reabrir o modal mostra a
  MUDAHR selecionada

#### Scenario: Modal de edição carrega o leiaute atual

- **WHEN** o admin abre a edição de um escritório que já tem um leiaute gravado
- **THEN** o campo já vem com esse leiaute selecionado, não com o padrão

### Requirement: A criação de escritório já nasce no leiaute neutro

O campo de leiaute DEVE (MUST) vir preenchido com o leiaute neutro da
plataforma ao abrir o cadastro de um escritório novo, de modo que o admin possa
salvar sem tocar nele.

Escritório criado sem que o leiaute seja informado DEVE (MUST) ficar com o
leiaute neutro — nunca sem leiaute, e nunca com o leiaute de uma marca.

#### Scenario: Admin cadastra sem mexer no campo

- **WHEN** o admin preenche apenas nome e salva um escritório novo
- **THEN** o escritório é criado com o leiaute neutro da plataforma

#### Scenario: Escritório criado antes deste campo existir

- **WHEN** um escritório cadastrado antes da introdução do campo é carregado
- **THEN** ele é tratado como estando no leiaute neutro, sem erro

### Requirement: O leiaute é ajustável apenas pelo admin da plataforma

O campo de leiaute DEVE (MUST) aparecer somente no CRUD de escritórios, que é
restrito ao perfil admin da plataforma. O sistema NÃO DEVE (MUST NOT) oferecer
esse campo em nenhuma tela de configuração acessível ao próprio escritório, e
NÃO DEVE (MUST NOT) aceitar alteração do leiaute por requisição que não venha de
um admin da plataforma.

#### Scenario: Usuário do escritório não encontra o campo

- **WHEN** um usuário do perfil de escritório percorre as telas de configuração
  disponíveis a ele
- **THEN** não existe campo de leiaute da dashboard em nenhuma delas

#### Scenario: Requisição sem perfil de admin

- **WHEN** uma requisição autenticada como usuário de escritório tenta alterar o
  leiaute pelo endpoint de escritórios
- **THEN** a alteração é recusada por falta de autorização

### Requirement: Leiaute inválido é recusado com erro

O sistema DEVE (MUST) recusar, com erro de validação, pedido de gravação cujo
leiaute não seja um dos três valores conhecidos, em vez de aceitar a requisição e
ignorar o campo.

#### Scenario: Valor desconhecido no pedido de atualização

- **WHEN** chega um pedido de atualização de escritório com um leiaute que não
  existe
- **THEN** a requisição é recusada com erro de validação e o leiaute gravado
  permanece o anterior
