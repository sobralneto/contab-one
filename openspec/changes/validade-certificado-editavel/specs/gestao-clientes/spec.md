## ADDED Requirements

### Requirement: A sincronização do agente só avança a validade do certificado

Ao sincronizar um cliente **já existente**, o agente DEVE (MUST) gravar a
validade do certificado APENAS quando a data recebida for posterior à que já
está registrada. Quando a data recebida for anterior, igual, ou vier ausente, o
sistema NÃO DEVE (MUST NOT) alterar a validade registrada.

Quando o cliente ainda não tem validade registrada, qualquer data recebida DEVE
(MUST) ser gravada — inclusive uma já vencida. É o primeiro registro do campo,
não um retrocesso, e é o que mantém o cliente visível nos alertas e no filtro de
certificado vencido.

Ao **cadastrar** um cliente novo, o agente DEVE (MUST) gravar a validade que
enviar, sem comparação — não há valor anterior contra o qual comparar.

A regra existe porque a validade agora também é informada pela tela. O agente lê
o `.pfx` que está na máquina do escritório; quem renovou o certificado e ainda
não o instalou lá sabe de uma data que o agente não tem como saber. Sem a regra,
a sincronização seguinte gravaria a data do arquivo antigo por cima da correção,
e ela sumiria sem ninguém entender por quê — o mesmo estrago que a preservação
do regime tributário evita no campo vizinho.

#### Scenario: Agente envia validade mais recente que a registrada

- **WHEN** o agente sincroniza um cliente já existente informando uma validade
  de certificado posterior à registrada
- **THEN** o cliente passa a ter a validade recebida

#### Scenario: Agente envia validade anterior à registrada

- **WHEN** o agente sincroniza um cliente já existente informando uma validade
  de certificado anterior à registrada
- **THEN** o cliente permanece com a validade que já tinha, ainda que nome e
  CNPJ tenham sido atualizados na mesma sincronização

#### Scenario: Agente envia a mesma validade já registrada

- **WHEN** o agente sincroniza um cliente já existente informando exatamente a
  validade que já está registrada
- **THEN** o cliente permanece com essa validade

#### Scenario: Agente não envia validade

- **WHEN** o agente sincroniza um cliente já existente sem informar validade de
  certificado
- **THEN** o cliente permanece com a validade que já tinha, que não é apagada

#### Scenario: Cliente ainda sem validade registrada

- **WHEN** o agente sincroniza um cliente já existente que não tem validade
  registrada, informando uma validade — mesmo já vencida
- **THEN** o cliente passa a ter a validade recebida

#### Scenario: Cliente novo cadastrado pelo agente

- **WHEN** o agente cadastra um cliente que ainda não existia, informando uma
  validade de certificado já vencida
- **THEN** o cliente nasce com essa validade, e aparece normalmente entre os de
  certificado vencido

### Requirement: A validade do certificado é editável para qualquer cliente

Na edição de um cliente, o sistema DEVE (MUST) oferecer o campo de validade do
certificado habilitado, qualquer que seja a origem do cliente e qualquer que
seja o papel do usuário do escritório.

O sistema DEVE (MUST) exibir, junto ao campo de um cliente de origem agente, a
informação de que o agente atualiza esse campo sozinho quando encontra um
certificado com validade mais longa — para que quem digita uma data saiba o que
acontece com ela depois.

Bloquear o campo não protegia nada: a data ficava congelada na do `.pfx` que
está na máquina do escritório, sem caminho nenhum para registrar um certificado
já renovado. Quem sustenta a informação agora é a regra de precedência da
sincronização, não a trava da tela.

#### Scenario: Edição de cliente de origem agente

- **WHEN** o usuário abre a edição de um cliente cuja origem é o agente
- **THEN** o campo de validade do certificado está habilitado, acompanhado da
  informação de que o agente pode atualizá-lo depois

#### Scenario: Edição por usuário sem papel de administração

- **WHEN** um usuário do escritório sem papel de administração abre a edição de
  um cliente
- **THEN** o campo de validade do certificado está habilitado para ele como para
  os demais papéis

#### Scenario: Validade informada pela tela

- **WHEN** o usuário informa uma validade de certificado na edição e salva
- **THEN** a data é gravada no cliente e passa a valer para os alertas e para o
  filtro por faixa de vencimento

## MODIFIED Requirements

### Requirement: A sincronização do agente preserva o regime tributário

A sincronização de clientes feita pelo agente NÃO DEVE (MUST NOT) alterar o
regime tributário de um cliente já existente, nem preenchê-lo ao cadastrar um
cliente novo.

O agente deriva o que sabe do nome e do conteúdo dos certificados na máquina do
escritório — código, nome, CNPJ e validade. O regime tributário não está em
lugar nenhum desse material: só uma pessoa informa. Se a sincronização
escrevesse nesse campo, escreveria "não informado" por cima da escolha feita na
tela, e o regime sumiria sozinho na próxima execução do agente, sem ninguém
entender por quê.

#### Scenario: Sincronização de cliente com regime informado

- **WHEN** o agente sincroniza um cliente que já existe e cujo regime foi
  informado pela tela
- **THEN** o cliente continua com o mesmo regime depois da sincronização, ainda
  que nome e CNPJ tenham sido atualizados

#### Scenario: Cliente cadastrado pelo agente

- **WHEN** o agente cadastra um cliente que ainda não existia
- **THEN** o cliente nasce com o regime não informado, disponível para alguém
  informar pela tela
