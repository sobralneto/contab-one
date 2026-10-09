## ADDED Requirements

### Requirement: A sincronização do agente respeita o nome editado manualmente

Ao sincronizar um cliente **já existente**, o agente NÃO DEVE (MUST NOT)
sobrescrever o nome de um cliente cujo nome tenha sido editado manualmente
pela tela. Para os demais clientes — nunca editados pela tela —, a
sincronização continua gravando o nome informado pelo agente, como fonte
primária. Um cliente cadastrado pelo agente DEVE (MUST) nascer com o nome
informado por ele e sem a marca de edição manual.

O nome que o agente informa é tirado do nome do arquivo do certificado e,
quando o arquivo foge do padrão, pode ser o nome do arquivo inteiro. Uma
correção feita à mão e esse valor são apenas diferentes, nunca um mais
recente que o outro — então, como no CNPJ, a regra não compara valores: só
sabe que alguém já definiu o nome, e para de escrever por cima a partir
daí.

#### Scenario: Sincronização de cliente com nome editado manualmente

- **WHEN** o agente sincroniza um cliente já existente cujo nome foi editado
  manualmente pela tela
- **THEN** o cliente mantém o nome que já tinha, mesmo que o agente informe
  um nome diferente

#### Scenario: Sincronização de cliente sem edição manual do nome

- **WHEN** o agente sincroniza um cliente já existente cujo nome nunca foi
  editado manualmente
- **THEN** o nome é atualizado com o que o agente informou, como antes desta
  mudança

#### Scenario: Cliente cadastrado pelo agente

- **WHEN** o agente cadastra um cliente que ainda não existia
- **THEN** o cliente nasce com o nome informado pelo agente e sem a marca de
  edição manual

#### Scenario: Demais campos seguem a sincronização

- **WHEN** o agente sincroniza um cliente com nome editado manualmente e
  informa uma validade de certificado mais nova
- **THEN** o nome é preservado e a validade é atualizada pelas regras já
  existentes

### Requirement: Editar o nome pela tela marca o nome como editado manualmente

Na edição de um cliente, o sistema DEVE (MUST) marcar o nome como editado
manualmente somente quando o nome informado for diferente do nome gravado.
Salvar o cliente sem alterar o nome NÃO DEVE (MUST NOT) ligar a marca, e
NÃO DEVE (MUST NOT) desligá-la caso já esteja ligada.

Sem a condição "apenas quando muda", qualquer edição de outro campo —
regime tributário, validade, situação — travaria o nome do cliente sem que
ninguém o tivesse escolhido, e o agente deixaria de corrigir nomes que
ninguém tocou.

#### Scenario: Nome alterado pela tela

- **WHEN** o usuário altera o nome de um cliente na edição e salva
- **THEN** o novo nome é gravado, e o cliente passa a ser tratado como de
  nome editado manualmente nas sincronizações seguintes do agente

#### Scenario: Edição sem mudar o nome

- **WHEN** o usuário altera outro campo do cliente (por exemplo o regime
  tributário) e salva sem mexer no nome
- **THEN** a marca de nome editado manualmente permanece como estava

#### Scenario: Cliente já marcado salvo novamente

- **WHEN** o usuário salva um cliente de nome editado manualmente sem alterar
  o nome
- **THEN** a marca continua ligada
