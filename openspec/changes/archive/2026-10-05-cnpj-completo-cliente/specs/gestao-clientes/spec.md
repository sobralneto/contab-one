## MODIFIED Requirements

### Requirement: O cadastro aceita o CNPJ e deriva hash e máscara no servidor

O sistema DEVE (MUST) aceitar o CNPJ completo no cadastro e na atualização de
cliente e, **no servidor**, derivar dele o hash de identificação e a versão
mascarada. O CNPJ completo informado DEVE (MUST) ser persistido junto com o
hash e a máscara.

Hash e máscara continuam existindo mesmo agora que o CNPJ completo também é
persistido: são o que permite localizar um cliente e exibir sua identidade
sem expor o valor pleno em buscas e listagens, e são o único registro que
sobra para clientes cadastrados antes desta mudança ou sincronizados por um
agente que ainda não envia o CNPJ completo. O hash é derivado com um segredo
que só o servidor tem, então quem cadastra não consegue calculá-lo por conta
própria — sem isso, cliente cadastrado pela interface nasce sem hash e nunca
é reconhecido como a mesma empresa que o agente já conhece.

#### Scenario: Cadastro informando o CNPJ

- **WHEN** um cliente é cadastrado com o CNPJ completo informado
- **THEN** o cliente é criado com hash, máscara e CNPJ completo persistidos

#### Scenario: Cadastro sem o CNPJ

- **WHEN** um cliente é cadastrado sem CNPJ
- **THEN** o cadastro é aceito como hoje, sem hash, sem máscara e sem CNPJ
  completo

#### Scenario: Atualização informando o CNPJ

- **WHEN** a edição de um cliente já existente informa o CNPJ completo
- **THEN** hash, máscara e CNPJ completo do cliente são recalculados e
  persistidos a partir do valor informado

## ADDED Requirements

### Requirement: A sincronização do agente respeita o CNPJ confirmado manualmente

Ao sincronizar um cliente **já existente**, o agente NÃO DEVE (MUST NOT)
sobrescrever CNPJ completo, hash ou máscara de um cliente cujo CNPJ tenha
sido confirmado manualmente pela tela. Para os demais clientes de origem
agente — ainda sem confirmação manual —, a sincronização continua gravando
CNPJ completo, hash e máscara normalmente, como fonte primária.

Confirmar manualmente marca que uma pessoa já verificou o CNPJ correto desse
cliente. Diferente da validade do certificado, o CNPJ não tem uma ordem
natural que diga qual valor é "melhor" — uma correção manual e o que o
agente lê do certificado são apenas diferentes, nunca um mais recente que o
outro —, então a regra de precedência não compara valores: só sabe que
alguém já confirmou, e para de escrever por cima a partir daí. Sem a regra,
a sincronização seguinte apagaria a correção sem explicação, o mesmo estrago
que a preservação do regime tributário e o avanço da validade do certificado
evitam nos campos vizinhos.

#### Scenario: Sincronização de cliente com CNPJ confirmado manualmente

- **WHEN** o agente sincroniza um cliente já existente cujo CNPJ foi
  confirmado manualmente pela tela
- **THEN** o cliente mantém o CNPJ completo, o hash e a máscara que já
  tinha, mesmo que o agente informe valores diferentes

#### Scenario: Sincronização de cliente sem confirmação manual

- **WHEN** o agente sincroniza um cliente já existente cujo CNPJ nunca foi
  confirmado manualmente
- **THEN** CNPJ completo, hash e máscara são atualizados com o que o agente
  informou, como antes desta mudança

#### Scenario: Cliente cadastrado pelo agente

- **WHEN** o agente cadastra um cliente que ainda não existia
- **THEN** o cliente nasce sem confirmação manual, e uma sincronização
  seguinte pode atualizar seu CNPJ normalmente

### Requirement: O campo de CNPJ é editável para qualquer cliente

Na edição de um cliente, o sistema DEVE (MUST) oferecer o campo de CNPJ
habilitado, qualquer que seja a origem do cliente. Salvar um CNPJ informado
pela tela DEVE (MUST) marcar o cliente como tendo o CNPJ confirmado
manualmente.

O sistema DEVE (MUST) exibir, junto ao campo de um cliente de origem agente
ainda sem confirmação manual, a informação de que o agente pode substituir o
valor na próxima sincronização até que alguém confirme pela tela.

Bloquear o campo não protegia nada: o CNPJ completo desses clientes nunca
chegava a existir na plataforma, sem caminho nenhum para alguém corrigi-lo
ou completá-lo à mão. Quem sustenta a informação agora é a regra de
precedência da sincronização, não a trava da tela.

#### Scenario: Edição de cliente de origem agente sem confirmação

- **WHEN** o usuário abre a edição de um cliente de origem agente cujo CNPJ
  nunca foi confirmado manualmente
- **THEN** o campo de CNPJ está habilitado, acompanhado da informação de que
  o agente pode substituí-lo até a confirmação manual

#### Scenario: CNPJ confirmado pela tela

- **WHEN** o usuário informa um CNPJ na edição de um cliente e salva
- **THEN** o CNPJ completo é gravado, e o cliente passa a ser tratado como
  confirmado manualmente nas sincronizações seguintes do agente

#### Scenario: Edição por usuário sem papel de administração

- **WHEN** um usuário do escritório sem papel de administração abre a edição
  de um cliente
- **THEN** o campo de CNPJ está habilitado para ele como para os demais
  papéis
