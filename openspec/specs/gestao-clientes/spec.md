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

Na tela de clientes, o sistema DEVE (MUST) oferecer um controle único para
filtrar por situação do certificado digital, disponível para **todos os papéis
que enxergam a listagem** — não apenas para a visão escritório. Vencimento de
certificado é assunto do cliente, não do papel de quem olha; e o painel oferece
essas contagens a todo mundo, então restringir o filtro a um papel deixaria
parte dos usuários sem como chegar ao que o painel mostrou.

O controle DEVE (MUST) oferecer exatamente as **mesmas três faixas que o painel
conta**, com os mesmos limites e os mesmos rótulos:

- **vencidos**, cujo certificado tem validade anterior a hoje;
- **vencendo em até 3 dias**;
- **vencendo de 4 a 30 dias**.

Um vocabulário só nas duas telas: quem lê uma contagem no painel e abre a
listagem reencontra o mesmo rótulo no seletor, em vez de ter de traduzir a faixa
para um período em dias. Os períodos avulsos que o controle oferecia antes (1,
2, 7 e 15 dias) saem — eram uma segunda maneira de dizer a mesma coisa, sem
correspondência com nada que o painel mostre.

As opções DEVEM (MUST) ser mutuamente exclusivas: escolher uma substitui a
anterior. Sem escolha alguma, a listagem NÃO DEVE (MUST NOT) ser restringida por
certificado.

O filtro DEVE (MUST) combinar com os demais controles da tela — busca,
escritório e onboarding —, restringindo o resultado a quem atende a todos ao
mesmo tempo, e a paginação e o total exibido DEVEM (MUST) refletir o conjunto
filtrado.

As três faixas DEVEM (MUST) ser as **mesmas** que o painel conta em seus
indicadores, de modo que abrir a listagem a partir de uma contagem produza
exatamente aquele conjunto.

#### Scenario: Filtro de vencendo em até 3 dias

- **WHEN** o usuário seleciona "vencendo em até 3 dias"
- **THEN** a tabela exibe apenas clientes cujo certificado vence de hoje até o
  terceiro dia, inclusive

#### Scenario: As faixas são as do painel

- **WHEN** o usuário abre o seletor de certificado
- **THEN** as opções oferecidas são exatamente as três faixas que o painel conta,
  e nenhum período avulso

#### Scenario: Filtro de vencidos

- **WHEN** o usuário seleciona "vencidos" no filtro de certificado
- **THEN** a tabela exibe apenas clientes cujo certificado já venceu, e nenhum
  cujo certificado ainda esteja válido

#### Scenario: Filtro da faixa de 4 a 30 dias

- **WHEN** o usuário seleciona a faixa de 4 a 30 dias
- **THEN** a tabela exibe apenas clientes cujo certificado vence nesse intervalo,
  excluindo os que vencem nos próximos 3 dias e os que vencem depois de 30

#### Scenario: Filtro disponível para o administrador

- **WHEN** um administrador de plataforma abre a tela de clientes
- **THEN** o filtro de certificado está disponível para ele como para os demais
  papéis, e é aplicado ao resultado

#### Scenario: Cliente sem certificado

- **WHEN** qualquer faixa de certificado está selecionada
- **THEN** clientes sem validade de certificado registrada não aparecem

#### Scenario: Usuário limpa filtro de vencimento

- **WHEN** o usuário remove o filtro de vencimento de certificado
- **THEN** a tabela volta a exibir todos os clientes do escopo

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

### Requirement: O cadastro do cliente registra o regime tributário

O cadastro e a edição de um cliente DEVEM (MUST) permitir escolher o regime
tributário da empresa entre um conjunto **fechado** de cinco opções: Simples
Nacional, Lucro Presumido, Lucro Real, MEI e Outros.

A escolha é **opcional**. Cliente sem regime informado é um cadastro válido, e
não é o mesmo que "Outros": "Outros" é a empresa cujo regime é conhecido e não
está entre os quatro nomeados, enquanto a ausência é a empresa cujo regime
ninguém informou ainda. O sistema NÃO DEVE (MUST NOT) tratar uma como a outra,
nem preencher a ausência com um valor por conta própria.

O conjunto é fechado no servidor: o sistema DEVE (MUST) recusar por validação a
gravação com um valor que não esteja entre os cinco, e NÃO DEVE (MUST NOT)
aceitá-lo gravando qualquer coisa em seu lugar. Regime tributário decide qual
obrigação o escritório apura; valor livre aqui viraria dado fiscal errado
gravado em silêncio.

A edição DEVE (MUST) permitir tanto trocar o regime quanto **limpar** a escolha,
voltando o cliente ao estado de regime não informado.

#### Scenario: Cadastro escolhendo o regime

- **WHEN** o usuário cadastra um cliente e escolhe um dos cinco regimes
- **THEN** o cliente é gravado com aquele regime, e a listagem passa a exibi-lo

#### Scenario: Cadastro sem escolher regime

- **WHEN** o usuário cadastra um cliente sem escolher regime
- **THEN** o cadastro é aceito, e o cliente fica com o regime não informado —
  não com "Outros"

#### Scenario: Troca de regime na edição

- **WHEN** o usuário edita um cliente e escolhe um regime diferente do que ele
  tinha
- **THEN** o regime novo é gravado, e nenhum outro dado do cliente é alterado

#### Scenario: Limpar a escolha na edição

- **WHEN** o usuário edita um cliente que tem regime e remove a escolha
- **THEN** o cliente volta ao estado de regime não informado

#### Scenario: Valor fora do conjunto

- **WHEN** a gravação informa um regime que não está entre os cinco
- **THEN** o pedido é recusado por validação, e o cliente não é gravado nem
  alterado

#### Scenario: Cliente já cadastrado antes do campo existir

- **WHEN** o usuário abre a edição de um cliente cadastrado antes de o regime
  existir
- **THEN** o campo aparece sem escolha alguma, e ele pode informar o regime sem
  precisar mexer em nenhum outro campo

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
  que nome, CNPJ e validade do certificado tenham sido atualizados

#### Scenario: Cliente cadastrado pelo agente

- **WHEN** o agente cadastra um cliente que ainda não existia
- **THEN** o cliente nasce com o regime não informado, disponível para alguém
  informar pela tela

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
escritório e situação do certificado — restringindo o resultado a quem atende a
todos ao mesmo tempo, e a paginação e o total exibido DEVEM (MUST) refletir o
conjunto filtrado, não o conjunto inteiro.

Estando desligado, o filtro NÃO DEVE (MUST NOT) alterar a listagem: a tela abre
mostrando todos os clientes, como hoje.

A tela DEVE (MUST) aceitar que a escolha de filtro venha do endereço, para que
um indicador do painel possa abrir a listagem já filtrada pelo conjunto que ele
contou.

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

#### Scenario: Filtro vindo do endereço

- **WHEN** a tela de clientes é aberta por um endereço que já indica uma faixa de
  certificado ou o onboarding
- **THEN** a listagem abre com aquele filtro aplicado e o controle correspondente
  refletindo a escolha

#### Scenario: Nenhum cliente em onboarding

- **WHEN** o usuário liga o filtro de onboarding e nenhum cliente do escopo está
  nessa situação
- **THEN** a tela apresenta o estado vazio, sem erro

### Requirement: A listagem de clientes exibe o regime tributário

A tela de clientes DEVE (MUST) exibir o regime tributário de cada cliente em
coluna própria, com o mesmo rótulo que o formulário oferece — quem escolhe
"Lucro Presumido" no cadastro reencontra "Lucro Presumido" na tabela, não uma
sigla nem um número.

Cliente sem regime informado DEVE (MUST) ser exibido com o mesmo marcador de
ausência que a tela já usa nas demais colunas ("—"), e NÃO DEVE (MUST NOT)
aparecer como "Outros" nem com a célula em branco, que se confundiria com falha
de carregamento.

A coluna vale para **todos os papéis** que enxergam a listagem: o regime é
atributo da empresa, não do papel de quem olha.

#### Scenario: Cliente com regime informado

- **WHEN** o usuário vê na listagem um cliente cujo regime foi informado
- **THEN** a coluna de regime mostra o nome daquele regime, por extenso

#### Scenario: Cliente sem regime informado

- **WHEN** o usuário vê na listagem um cliente sem regime informado
- **THEN** a coluna de regime mostra "—", e não "Outros"

#### Scenario: Coluna visível para o administrador

- **WHEN** um administrador de plataforma abre a tela de clientes
- **THEN** a coluna de regime aparece para ele como para os demais papéis

### Requirement: A listagem de clientes filtra por regime tributário

A tela de clientes DEVE (MUST) oferecer um controle para restringir a listagem a
um regime tributário, com as **mesmas cinco opções** que o cadastro oferece e os
mesmos rótulos — quem escolhe "Lucro Presumido" no formulário reencontra "Lucro
Presumido" no filtro.

O controle DEVE (MUST) oferecer também a opção **"Não informado"**, que restringe
a listagem aos clientes sem regime. É a consulta que o escritório faz para saber
quem ainda falta classificar; sem ela, os clientes que mais precisam de atenção
são justamente os únicos que o filtro não alcança.

As opções DEVEM (MUST) ser mutuamente exclusivas: escolher uma substitui a
anterior. Sem escolha alguma, a listagem NÃO DEVE (MUST NOT) ser restringida por
regime.

O filtro DEVE (MUST) estar disponível para **todos os papéis** que enxergam a
listagem, e DEVE (MUST) combinar com os demais controles da tela — busca,
escritório, certificado e onboarding —, restringindo o resultado a quem atende a
todos ao mesmo tempo. A paginação e o total exibido DEVEM (MUST) refletir o
conjunto filtrado, e a escolha DEVE (MUST) levar de volta à primeira página.

O sistema DEVE (MUST) resolver a opção pedida a partir de um conjunto fechado
definido no servidor. Pedido com valor desconhecido NÃO DEVE (MUST NOT) filtrar
por regime e NÃO DEVE (MUST NOT) devolver erro — mesma regra das faixas de
certificado e da coluna de ordenação: endereço antigo ou digitado à mão mostra a
lista, não uma falha.

#### Scenario: Filtrar por um regime

- **WHEN** o usuário escolhe um regime no filtro
- **THEN** a listagem exibe apenas os clientes daquele regime, e o total exibido
  acompanha

#### Scenario: Filtrar por quem não tem regime

- **WHEN** o usuário escolhe "Não informado"
- **THEN** a listagem exibe apenas os clientes sem regime informado, e nenhum dos
  que já foram classificados — inclusive nenhum dos marcados como "Outros"

#### Scenario: Filtro desligado

- **WHEN** o usuário não escolhe regime algum
- **THEN** a listagem exibe todos os clientes do escopo, com e sem regime

#### Scenario: Filtro combinado com a busca

- **WHEN** o usuário digita um termo de busca e escolhe um regime
- **THEN** a listagem exibe apenas os clientes que atendem ao termo E estão
  naquele regime

#### Scenario: Filtro disponível para o administrador

- **WHEN** um administrador de plataforma abre a tela de clientes
- **THEN** o filtro de regime está disponível para ele como para os demais
  papéis, e combina com o filtro de escritório

#### Scenario: Valor desconhecido

- **WHEN** a listagem é pedida com um regime que não existe
- **THEN** o resultado sai sem filtro de regime, e nenhum erro é devolvido

#### Scenario: Troca de filtro volta à primeira página

- **WHEN** o usuário está numa página adiante e escolhe um regime
- **THEN** a listagem volta para a primeira página do conjunto filtrado

### Requirement: A listagem de clientes é ordenável pelo usuário

A tela de clientes DEVE (MUST) permitir escolher por qual coluna a listagem é
ordenada e em que direção, acionando o cabeçalho da própria coluna.

DEVEM (MUST) ser ordenáveis: código, nome, regime tributário, validade do
certificado e data da última atualização; e, para quem enxerga a coluna de
escritório, também o escritório. O CNPJ NÃO DEVE (MUST NOT) ser ordenável — o
valor guardado é mascarado, e ordenar por ele ordenaria por um texto
parcialmente oculto, parecendo um recurso sem ser um.

Acionar o cabeçalho da coluna já ordenada DEVE (MUST) inverter a direção;
acionar o de outra coluna DEVE (MUST) passar a ordenar por ela, em ordem
crescente.

**Toda coluna ordenável DEVE (MUST) se anunciar como tal**, esteja ou não
ordenando no momento, e DEVE (MUST) ser distinguível à primeira vista de uma
coluna que não ordena. Indicar apenas a coluna ativa não basta: as demais ficam
idênticas às que não ordenam, e a única pista de que são acionáveis aparece
depois que o usuário já levou o ponteiro até lá — ou seja, só para quem já
desconfiava.

A coluna e a direção vigentes DEVEM (MUST) ficar visíveis no cabeçalho, com
destaque distinto do que marca as demais como ordenáveis, para que a ordem
exibida nunca seja adivinhada. Isso vale **desde a abertura da tela**: a ordem
padrão DEVE (MUST) estar indicada antes de o usuário acionar qualquer coisa.

Os cabeçalhos DEVEM (MUST) ser acionáveis também por teclado, e receber foco
visível — ordenação que só responde a clique fica inalcançável para quem não usa
mouse.

Sem escolha alguma, a listagem DEVE (MUST) sair ordenada por **nome, crescente**
— o comportamento que já existia.

A ordenação DEVE (MUST) se aplicar ao conjunto inteiro que passou pelos filtros,
e não apenas à página exibida.

Trocar a ordenação DEVE (MUST) levar de volta à primeira página: a página em que
o usuário estava não tem relação com a lista reordenada.

O sistema DEVE (MUST) resolver a coluna pedida a partir de um conjunto fechado,
definido no servidor. Pedido com coluna desconhecida DEVE (MUST) cair no padrão,
sem erro — endereço antigo ou digitado à mão mostra a lista, não uma falha.

#### Scenario: Ordenar por uma coluna

- **WHEN** o usuário aciona o cabeçalho de uma coluna ordenável
- **THEN** a listagem passa a sair ordenada por ela em ordem crescente, e o
  cabeçalho indica a coluna e a direção

#### Scenario: Inverter a direção

- **WHEN** o usuário aciona o cabeçalho da coluna que já ordena a listagem
- **THEN** a direção se inverte, e a indicação no cabeçalho acompanha

#### Scenario: Trocar de coluna

- **WHEN** o usuário aciona o cabeçalho de uma coluna diferente da atual
- **THEN** a listagem passa a ser ordenada pela coluna nova, em ordem crescente

#### Scenario: Ordem padrão

- **WHEN** o usuário abre a tela sem escolher ordenação
- **THEN** a listagem sai ordenada por nome, em ordem crescente, e o cabeçalho
  de nome já indica que é ele quem ordena, e em que direção

#### Scenario: Coluna ordenável que não está ordenando

- **WHEN** o usuário olha o cabeçalho de uma coluna ordenável que não é a ativa
- **THEN** ela se apresenta como ordenável, distinguível da coluna que não
  ordena, e sem se confundir com a que está ordenando

#### Scenario: Ordenar pelo teclado

- **WHEN** o usuário leva o foco a um cabeçalho ordenável e o aciona pelo teclado
- **THEN** a listagem é reordenada por aquela coluna, como no acionamento por
  clique

#### Scenario: Ordenação alcança além da página

- **WHEN** o usuário ordena uma listagem que ocupa várias páginas
- **THEN** a ordem vale para todos os clientes filtrados, e a primeira página
  traz os primeiros dessa ordem — não os primeiros da página anterior
  reordenados

#### Scenario: Troca de ordenação volta à primeira página

- **WHEN** o usuário está numa página adiante e troca a ordenação
- **THEN** a listagem volta para a primeira página da ordem nova

#### Scenario: Coluna desconhecida

- **WHEN** a listagem é pedida com uma coluna de ordenação que não existe
- **THEN** o resultado sai na ordem padrão, e nenhum erro é devolvido

#### Scenario: CNPJ não é ordenável

- **WHEN** o usuário percorre os cabeçalhos da tabela
- **THEN** o de CNPJ não oferece ordenação

#### Scenario: Ordenar por regime tributário

- **WHEN** o usuário aciona o cabeçalho da coluna de regime tributário
- **THEN** a listagem passa a sair ordenada por regime, com os clientes de um
  mesmo regime juntos

### Requirement: A ordenação da listagem é estável entre páginas

O sistema DEVE (MUST) garantir que clientes empatados na coluna escolhida
tenham entre si uma ordem **determinística**, igual a cada pedido, aplicando um
critério de desempate próprio depois da coluna escolhida.

Sem esse desempate, o banco fica livre para ordenar o empate como quiser a cada
consulta, e a paginação passa a mentir: com nomes repetidos ou vários
certificados nulos, o mesmo cliente pode aparecer em duas páginas enquanto outro
não aparece em nenhuma — e o usuário não tem como perceber.

#### Scenario: Empate na coluna ordenada

- **WHEN** vários clientes têm o mesmo valor na coluna escolhida e a listagem é
  pedida mais de uma vez
- **THEN** eles saem sempre na mesma ordem relativa

#### Scenario: Paginação sobre empate

- **WHEN** o usuário percorre todas as páginas de uma listagem ordenada por uma
  coluna com muitos valores repetidos
- **THEN** cada cliente aparece exatamente uma vez no conjunto das páginas,
  nenhum é repetido e nenhum é omitido

### Requirement: Cliente sem certificado não encabeça a ordenação por certificado

Ao ordenar pela validade do certificado, o sistema DEVE (MUST) colocar os
clientes **sem certificado registrado** no fim do resultado, **nas duas
direções**.

Ordem decrescente que começasse pelos ausentes abriria a lista com quem não tem
certificado nenhum, empurrando para baixo justamente o que a coluna existe para
mostrar. Ausência não é o maior valor nem o menor: é ausência, e vai para o fim.

#### Scenario: Ordem crescente por certificado

- **WHEN** o usuário ordena por certificado em ordem crescente
- **THEN** os clientes aparecem do vencimento mais próximo ao mais distante, e
  os sem certificado vêm depois de todos eles

#### Scenario: Ordem decrescente por certificado

- **WHEN** o usuário ordena por certificado em ordem decrescente
- **THEN** os clientes aparecem do vencimento mais distante ao mais próximo, e
  os sem certificado continuam depois de todos eles

### Requirement: Cliente sem regime não encabeça a ordenação por regime

Ao ordenar pelo regime tributário, o sistema DEVE (MUST) colocar os clientes
**sem regime informado** no fim do resultado, **nas duas direções** — a mesma
regra que já vale para a ordenação por certificado.

Ausência não é o primeiro regime nem o último: é ausência, e vai para o fim.
Duas colunas da mesma tabela tratando o vazio de maneiras opostas obrigariam o
usuário a decorar qual é qual.

#### Scenario: Ordem crescente por regime

- **WHEN** o usuário ordena por regime em ordem crescente
- **THEN** os clientes com regime informado aparecem primeiro, agrupados por
  regime, e os sem regime vêm depois de todos eles

#### Scenario: Ordem decrescente por regime

- **WHEN** o usuário ordena por regime em ordem decrescente
- **THEN** a ordem dos regimes se inverte, e os clientes sem regime continuam
  depois de todos eles
