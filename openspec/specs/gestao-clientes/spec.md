## Purpose

Corrige o fluxo de cadastro de clientes e adiciona filtros e colunas contextuais por papel (admin vê escritório responsável, escritório filtra por vencimento de certificado).

## Requirements

### Requirement: Cadastro de novo cliente funcional

O sistema DEVE (MUST) permitir que um usuário cadastre um novo cliente com sucesso, persistindo todos os campos do formulário.

#### Scenario: Cadastro de cliente com dados válidos

- **WHEN** o usuário preenche todos os campos obrigatórios do formulário de novo cliente e clica em salvar
- **THEN** o cliente é criado e aparece na listagem de clientes

#### Scenario: Cadastro com campos obrigatórios ausentes

- **WHEN** o usuário tenta salvar um cliente sem preencher campos obrigatórios
- **THEN** o sistema exibe mensagens de validação indicando os campos faltantes

### Requirement: Coluna de escritório na visão admin

Na listagem de clientes da visão admin, o sistema DEVE (MUST) exibir uma coluna com o nome do escritório responsável por cada cliente.

#### Scenario: Tabela de clientes como admin

- **WHEN** um admin acessa a tela de clientes
- **THEN** a tabela exibe uma coluna "Escritório" com o nome do escritório vinculado a cada cliente

### Requirement: Filtro por escritório na visão admin

Na visão admin da tela de clientes, o sistema DEVE (MUST) oferecer um filtro para selecionar um escritório específico e filtrar a listagem.

#### Scenario: Admin filtra clientes por escritório

- **WHEN** o admin seleciona um escritório no filtro
- **THEN** a tabela exibe apenas os clientes vinculados ao escritório selecionado

### Requirement: Filtro por vencimento de certificado na visão escritório

Na visão escritório da tela de clientes, o sistema DEVE (MUST) oferecer um controle de dias para filtrar clientes cujo certificado digital vencerá dentro do período selecionado (1, 2, 3, 7 ou 15 dias).

#### Scenario: Escritório filtra por vencimento em 7 dias

- **WHEN** o escritório seleciona "7 dias" no filtro de vencimento de certificado
- **THEN** a tabela exibe apenas clientes cujo certificado vence nos próximos 7 dias

#### Scenario: Escritório limpa filtro de vencimento

- **WHEN** o escritório remove o filtro de vencimento de certificado
- **THEN** a tabela volta a exibir todos os clientes do escritório

### Requirement: O cadastro aceita o CNPJ e deriva hash e máscara no servidor

O sistema DEVE (MUST) aceitar o CNPJ completo no cadastro e na atualização de
cliente, derivar dele o hash de identificação e a versão mascarada **no
servidor**, e descartar o CNPJ completo em seguida. O CNPJ completo NÃO DEVE
(MUST NOT) ser persistido.

O hash é derivado com um segredo que só o servidor tem, então quem cadastra
não consegue calculá-lo — sem isso, cliente cadastrado pela interface nasce
sem hash e nunca é reconhecido como a mesma empresa que o agente já conhece.

#### Scenario: Cadastro informando o CNPJ

- **WHEN** um cliente é cadastrado com o CNPJ completo informado
- **THEN** o cliente é criado com hash e máscara derivados, e o CNPJ completo
  não é guardado em lugar nenhum

#### Scenario: Cadastro sem o CNPJ

- **WHEN** um cliente é cadastrado sem CNPJ
- **THEN** o cadastro é aceito como hoje, sem hash e sem máscara

### Requirement: Cliente é identificado pelo CNPJ do documento

O sistema DEVE (MUST) localizar, dentro do escritório da sessão, o cliente
correspondente a um CNPJ informado — primeiro pelo hash de identificação e,
não achando, pela versão mascarada. Ao localizar pela máscara um cliente sem
hash, o sistema DEVE (MUST) preencher o hash que faltava.

Não localizando ninguém, DEVE (MUST) devolver uma sugestão de cadastro com os
dados disponíveis, sem criar cliente algum por conta própria.

#### Scenario: Cliente já cadastrado pelo agente

- **WHEN** o CNPJ informado corresponde a um cliente que já tem hash
- **THEN** esse cliente é devolvido, e nenhum cliente novo é criado

#### Scenario: Cliente cadastrado à mão, sem hash

- **WHEN** o CNPJ informado não casa por hash, mas casa pela versão mascarada
  de um cliente sem hash
- **THEN** esse cliente é devolvido e passa a ter o hash preenchido

#### Scenario: Empresa ainda não cadastrada

- **WHEN** o CNPJ informado não corresponde a nenhum cliente do escritório
- **THEN** o sistema devolve uma sugestão de cadastro, e nenhum cliente é
  criado antes da confirmação

#### Scenario: CNPJ de cliente de outro escritório

- **WHEN** o CNPJ informado corresponde a um cliente de outro escritório
- **THEN** o resultado é o de empresa não cadastrada, sem revelar a
  existência do cliente alheio

### Requirement: O código do novo cliente é sugerido, não imposto

O sistema DEVE (MUST) oferecer o próximo código livre do escritório ao
cadastrar um cliente a partir de um documento, e DEVE (MUST) permitir que o
usuário o altere antes de confirmar.

O código é a chave que o escritório usa para casar o cliente com as próprias
pastas; gerá-lo em silêncio produziria divergência que ninguém percebe na
hora.

#### Scenario: Sugestão de código

- **WHEN** o usuário vai cadastrar um cliente identificado a partir de um
  documento
- **THEN** o formulário vem com o próximo código livre preenchido e editável

#### Scenario: Código escolhido já em uso

- **WHEN** o usuário confirma o cadastro com um código já usado por outro
  cliente do escritório
- **THEN** o cadastro é recusado indicando o conflito, e o usuário pode
  escolher outro

### Requirement: Cliente criado a partir de documento tem origem própria

O sistema DEVE (MUST) registrar como origem distinta o cliente criado a
partir da importação de um documento, separando-o do cadastro manual e do
cadastro feito pelo agente.

#### Scenario: Origem na listagem de clientes

- **WHEN** um cliente foi criado durante a importação de um documento
- **THEN** a listagem de clientes mostra essa origem, distinta de manual e de
  agente

### Requirement: O cadastro do cliente escolhe o modelo de onboarding

O cadastro e a edição de um cliente DEVEM (MUST) oferecer a escolha de qual modelo
de onboarding aquele cliente usa, entre os modelos disponíveis para o escritório.
A escolha é OPCIONAL: o cliente pode ficar sem modelo, e nesse caso simplesmente
não tem onboarding.

O sistema DEVE (MUST) recusar a gravação quando o modelo informado não existir ou
não estiver disponível para o escritório do cliente, e DEVE (MUST) permitir limpar
a escolha (voltar a "sem onboarding") na edição.

#### Scenario: Escolher modelo ao cadastrar

- **WHEN** o usuário cadastra um cliente e escolhe um modelo de onboarding
- **THEN** o cliente é gravado apontando para aquele modelo

#### Scenario: Cadastrar sem escolher modelo

- **WHEN** o usuário cadastra um cliente sem escolher modelo
- **THEN** o cliente é gravado sem modelo, e nenhuma ação de onboarding é oferecida
  para ele

#### Scenario: Trocar o modelo na edição

- **WHEN** o usuário edita um cliente e troca (ou limpa) o modelo de onboarding
- **THEN** a escolha nova é gravada, e o checklist do cliente passa a refletir o
  modelo atual

#### Scenario: Modelo inexistente

- **WHEN** a gravação informa um modelo que não existe ou não está disponível para o
  escritório
- **THEN** o pedido é recusado por validação, e o cliente não é gravado com esse
  modelo

### Requirement: A listagem de clientes dá acesso ao onboarding de quem tem modelo

Na coluna de ações da listagem de clientes, o sistema DEVE (MUST) oferecer a ação de
onboarding APENAS para clientes que já têm modelo escolhido. Para cliente sem
modelo, nenhuma ação de onboarding DEVE (MUST) aparecer — não há o que montar.

Quando a ação aparece, o efeito dela depende de o cliente já ter checklist: sem
checklist, a ação o cria e leva à página dele; com checklist, apenas abre a página.
As duas nunca aparecem juntas na mesma linha.

#### Scenario: Cliente sem modelo

- **WHEN** o usuário vê na listagem um cliente sem modelo de onboarding escolhido
- **THEN** a linha dele não oferece ação de onboarding alguma, mantendo as demais
  ações (editar, excluir)

#### Scenario: Cliente com modelo e sem checklist

- **WHEN** o usuário aciona a ação de onboarding na linha de um cliente que tem
  modelo mas ainda não tem checklist
- **THEN** o checklist é criado para aquele cliente e a aplicação abre a página de
  onboarding dele

#### Scenario: Cliente com checklist

- **WHEN** o usuário aciona a ação de onboarding na linha de um cliente que já tem
  checklist
- **THEN** a aplicação abre a página de onboarding existente daquele cliente, sem
  criar um novo

### Requirement: O código do cliente é editável depois do cadastro

O sistema DEVE (MUST) permitir alterar o código de um cliente já cadastrado, pela
mesma tela e pelo mesmo pedido que alteram os demais campos, e DEVE (MUST)
persistir o código novo.

O código é a chave que o escritório usa para casar o cliente com as próprias
pastas. Sem edição, um dígito errado no cadastro só se corrige excluindo e
recriando o cliente — o que descarta junto o checklist de onboarding e o
histórico de execuções daquele cliente.

A alteração DEVE (MUST) obedecer à mesma unicidade por escritório que vale no
cadastro: dois clientes do mesmo escritório não podem ficar com o mesmo código.
O sistema DEVE (MUST) recusar a alteração que colida com o código de OUTRO
cliente do escritório, indicando o conflito, e NÃO DEVE (MUST NOT) tratar como
conflito o pedido que mantém o código que o próprio cliente já tem. Código vazio
DEVE (MUST) ser recusado por validação, como no cadastro.

Alterar o código NÃO DEVE (MUST NOT) afetar nenhum outro dado do cliente — o
checklist de onboarding, as execuções e as métricas continuam apontando para o
mesmo cliente.

O código é também a chave pela qual o agente reconhece o cliente na
sincronização, e o agente a deriva do nome do arquivo do certificado na máquina
do escritório. Por isso, ao editar um cliente cuja origem é o agente, o sistema
DEVE (MUST) avisar, na própria tela, que mudar o código sem renomear o
certificado correspondente faz a próxima sincronização cadastrar o cliente
de novo sob o código antigo. O aviso NÃO DEVE (MUST NOT) impedir a alteração:
renomear os dois lados é exatamente o caso de uso que justifica a edição.

#### Scenario: Alteração para um código livre

- **WHEN** o usuário edita um cliente e informa um código ainda não usado no
  escritório
- **THEN** o código novo é gravado e passa a aparecer na listagem

#### Scenario: Alteração para um código já usado

- **WHEN** o usuário edita um cliente e informa um código que já pertence a outro
  cliente do mesmo escritório
- **THEN** a gravação é recusada indicando o conflito, e o cliente permanece com o
  código que tinha

#### Scenario: Gravação mantendo o próprio código

- **WHEN** o usuário salva a edição de um cliente sem mexer no código
- **THEN** a gravação é aceita normalmente, sem acusar conflito com ele mesmo

#### Scenario: Código igual ao de cliente de outro escritório

- **WHEN** o usuário edita um cliente e informa um código que já é usado por um
  cliente de OUTRO escritório
- **THEN** a gravação é aceita, porque a unicidade é por escritório

#### Scenario: Código vazio

- **WHEN** o usuário tenta salvar a edição com o código em branco
- **THEN** a gravação é recusada por validação, e o cliente permanece como estava

#### Scenario: Aviso ao editar cliente de origem agente

- **WHEN** o usuário abre a edição de um cliente cuja origem é o agente
- **THEN** o campo de código é editável e acompanhado do aviso de que o
  certificado na máquina do escritório precisa ser renomeado junto

#### Scenario: Vínculos preservados

- **WHEN** o código de um cliente que já tem checklist de onboarding é alterado
- **THEN** o checklist continua sendo o mesmo daquele cliente, agora exibido sob o
  código novo

### Requirement: A listagem de clientes filtra por quem está em onboarding

A tela de clientes DEVE (MUST) oferecer um filtro que restrinja a listagem aos
clientes em fase de onboarding, conforme a definição única de
[[checklist-onboarding]]. O filtro DEVE (MUST) estar disponível para todos os
papéis que enxergam a listagem, e não apenas para administradores.

O filtro DEVE (MUST) combinar com os demais controles da tela — busca por texto,
escritório e vencimento de certificado — restringindo o resultado a quem atende a
todos ao mesmo tempo, e a paginação e o total exibido DEVEM (MUST) refletir o
conjunto filtrado, não o conjunto inteiro.

Estando desligado, o filtro NÃO DEVE (MUST NOT) alterar a listagem: a tela abre
mostrando todos os clientes, como hoje.

#### Scenario: Filtrar por clientes em onboarding

- **WHEN** o usuário liga o filtro de onboarding na tela de clientes
- **THEN** a listagem passa a exibir apenas os clientes em fase de onboarding, e o
  total exibido acompanha

#### Scenario: Filtro desligado

- **WHEN** o usuário não liga o filtro de onboarding
- **THEN** a listagem exibe todos os clientes do escopo, em onboarding ou não

#### Scenario: Filtro combinado com a busca

- **WHEN** o usuário digita um termo de busca e liga o filtro de onboarding
- **THEN** a listagem exibe apenas os clientes que atendem ao termo E estão em
  onboarding

#### Scenario: Filtro na visão de administrador

- **WHEN** um administrador liga o filtro de onboarding e também escolhe um
  escritório no filtro de escritório
- **THEN** a listagem exibe apenas os clientes em onboarding daquele escritório

#### Scenario: Nenhum cliente em onboarding

- **WHEN** o usuário liga o filtro de onboarding e nenhum cliente do escopo está
  nessa situação
- **THEN** a tela apresenta o estado vazio, sem erro
