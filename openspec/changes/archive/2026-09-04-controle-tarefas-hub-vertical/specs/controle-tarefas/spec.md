## ADDED Requirements

### Requirement: A tarefa exige título e ao menos um responsável

O sistema DEVE (MUST) recusar a criação ou a atualização de uma tarefa sem título
preenchido ou sem ao menos um responsável. Data de vencimento, recorrência,
observação e cliente vinculado são opcionais e PODEM (MAY) ficar vazios.

Uma tarefa é uma linha única compartilhada: ela NÃO DEVE (MUST NOT) ser duplicada
por responsável.

#### Scenario: Criação com o mínimo obrigatório

- **WHEN** um usuário cria uma tarefa informando apenas título e um responsável
- **THEN** a tarefa é criada em estado aberto, sem vencimento, sem recorrência, sem
  observação e sem cliente

#### Scenario: Criação sem título

- **WHEN** um usuário tenta salvar uma tarefa com o título vazio
- **THEN** o sistema recusa a operação e indica que o título é obrigatório

#### Scenario: Criação sem responsável

- **WHEN** um usuário tenta salvar uma tarefa com a lista de responsáveis vazia
- **THEN** o sistema recusa a operação e indica que ao menos um responsável é
  obrigatório

#### Scenario: Tarefa com dois responsáveis é uma só

- **WHEN** um usuário cria uma tarefa atribuída a dois responsáveis
- **THEN** existe uma única tarefa, e os dois responsáveis enxergam a mesma tarefa,
  com o mesmo estado

### Requirement: O seletor de responsável lista só o escritório em foco

O sistema DEVE (MUST) oferecer, como opções de responsável, apenas os usuários
**ativos** vinculados ao escritório em foco da sessão — tanto `EscritorioUsuario`
quanto `EscritorioAdmin` — e DEVE (MUST) recusar a gravação de um responsável que
não esteja vinculado àquele escritório.

O campo DEVE (MUST) vir preenchido com o **próprio usuário logado** como valor
padrão sempre que uma tarefa nova é iniciada.

#### Scenario: Abertura do formulário de tarefa nova

- **WHEN** um usuário abre o formulário de uma tarefa nova
- **THEN** o campo de responsável já vem preenchido com o próprio usuário logado, e
  ele pode acrescentar ou trocar responsáveis

#### Scenario: Opções restritas ao escritório em foco

- **WHEN** um usuário vinculado a dois escritórios abre o seletor de responsável
- **THEN** aparecem apenas os usuários vinculados ao escritório em foco naquela
  sessão, e nenhum usuário do outro escritório

#### Scenario: Usuário desativado não é oferecido

- **WHEN** um usuário do escritório está desativado
- **THEN** ele não aparece entre as opções de responsável

#### Scenario: Responsável de outro escritório enviado direto à API

- **WHEN** um pedido de gravação informa como responsável um usuário sem vínculo com
  o escritório da tarefa
- **THEN** o sistema recusa a operação e indica que o responsável precisa ser um
  usuário daquele escritório

### Requirement: A tarefa é visível a quem participa dela

O sistema DEVE (MUST) apresentar a um usuário apenas as tarefas em que ele é
responsável ou que ele mesmo criou, e NÃO DEVE (MUST NOT) apresentar as demais
tarefas do escritório.

Essa restrição vale para **todos os papéis**: `EscritorioAdmin` NÃO DEVE (MUST NOT)
enxergar as tarefas em que não participa, e `PlatformAdmin` — mesmo sem escritório
em foco, quando enxerga todos os escritórios — também NÃO DEVE (MUST NOT).

A restrição por participação é aplicada **além** do isolamento por escritório, nunca
no lugar dele: tarefa de um escritório jamais aparece em outro.

#### Scenario: Colega não vê a tarefa alheia

- **WHEN** o usuário A cria uma tarefa atribuída somente a si mesmo e o usuário B, do
  mesmo escritório, abre a lista de tarefas
- **THEN** a tarefa não aparece para B

#### Scenario: Admin do escritório não vê a tarefa alheia

- **WHEN** um `EscritorioAdmin` abre a lista de tarefas do escritório que administra
- **THEN** aparecem apenas as tarefas em que ele é responsável ou que ele criou

#### Scenario: Criador continua enxergando o que delegou

- **WHEN** o usuário A cria uma tarefa e atribui como responsável apenas o usuário B
- **THEN** a tarefa aparece tanto para B quanto para A

#### Scenario: PlatformAdmin sem foco

- **WHEN** um `PlatformAdmin` sem escritório em foco abre a lista de tarefas
- **THEN** aparecem apenas as tarefas em que ele é responsável ou que ele criou, e
  nenhuma tarefa dos escritórios que ele administra

#### Scenario: Isolamento entre escritórios

- **WHEN** um usuário vinculado a dois escritórios está com o escritório A em foco
- **THEN** nenhuma tarefa do escritório B aparece, mesmo que ele seja responsável por
  ela

### Requirement: A conclusão vale para todos os responsáveis

O sistema DEVE (MUST) tratar a conclusão como estado da tarefa, e não do
responsável: quando um dos responsáveis conclui, a tarefa passa a aparecer concluída
para todos os que a enxergam. O sistema DEVE (MUST) registrar quando e por quem a
tarefa foi concluída.

Reabrir uma tarefa concluída DEVE (MUST) ser possível e limpa o registro de
conclusão.

#### Scenario: Conclusão por um dos responsáveis

- **WHEN** o usuário A conclui uma tarefa cujos responsáveis são A e B
- **THEN** B também passa a ver a tarefa como concluída, com a indicação de que foi A
  quem concluiu

#### Scenario: Reabertura

- **WHEN** um responsável reabre uma tarefa concluída
- **THEN** a tarefa volta ao estado aberto para todos os responsáveis e o registro de
  quem concluiu deixa de valer

### Requirement: Concluir uma tarefa recorrente gera a próxima ocorrência

O sistema DEVE (MUST) criar, ao concluir uma tarefa cuja recorrência seja diária,
semanal, mensal ou anual, uma tarefa nova e aberta com o mesmo título, observação,
cliente, responsáveis e recorrência, e com o vencimento avançado **a partir do
vencimento da ocorrência concluída** — nunca a partir da data em que foi concluída.

A ocorrência concluída DEVE (MUST) permanecer registrada como concluída, e a nova
DEVE (MUST) manter rastreável a ocorrência que a originou.

O avanço mensal e o anual DEVEM (MUST) saturar no último dia do mês de destino
quando o dia não existir.

#### Scenario: Recorrência mensal concluída no prazo

- **WHEN** um responsável conclui uma tarefa mensal com vencimento em 10/03
- **THEN** a tarefa de 10/03 fica concluída e surge uma tarefa aberta idêntica com
  vencimento em 10/04

#### Scenario: Recorrência mensal concluída com atraso

- **WHEN** um responsável conclui, em 25/03, uma tarefa mensal com vencimento em 10/03
- **THEN** a próxima ocorrência vence em 10/04, e não em 25/04

#### Scenario: Dia inexistente no mês seguinte

- **WHEN** uma tarefa mensal com vencimento em 31/01 é concluída
- **THEN** a próxima ocorrência vence no último dia de fevereiro

#### Scenario: Recorrência anual em 29 de fevereiro

- **WHEN** uma tarefa anual com vencimento em 29/02 de um ano bissexto é concluída
- **THEN** a próxima ocorrência vence em 28/02 do ano seguinte

#### Scenario: Tarefa sem recorrência

- **WHEN** um responsável conclui uma tarefa cuja recorrência é "nenhuma"
- **THEN** nenhuma tarefa nova é criada

### Requirement: Recorrência exige data de vencimento

O sistema DEVE (MUST) recusar a gravação de uma tarefa com recorrência diferente de
"nenhuma" e sem data de vencimento, porque não haveria de onde avançar a ocorrência
seguinte.

#### Scenario: Recorrência sem vencimento

- **WHEN** um usuário tenta salvar uma tarefa semanal sem informar a data de
  vencimento
- **THEN** o sistema recusa a operação e indica que a data de vencimento é obrigatória
  para tarefas recorrentes

### Requirement: A página de tarefas organiza a lista em visões

O sistema DEVE (MUST) oferecer uma página de tarefas com as visões **Hoje**,
**Próximas**, **Atrasadas**, **Sem prazo** e **Concluídas**, cada uma exibindo a
quantidade de tarefas que contém. A visão "Próximas" DEVE (MUST) separar as tarefas
em blocos por proximidade do vencimento, e a visão "Sem prazo" DEVE (MUST) reunir as
tarefas abertas que não têm data de vencimento.

Uma tarefa é considerada atrasada quando está aberta e o vencimento é anterior ao dia
corrente do usuário. Tarefa aberta sem vencimento NÃO DEVE (MUST NOT) aparecer como
atrasada nem como do dia.

A página DEVE (MUST) permitir criar uma tarefa diretamente na lista, sem sair da
visão, e DEVE (MUST) oferecer filtro por responsável e por cliente.

A criação na lista DEVE (MUST) se resolver por teclado: um clique em qualquer
ponto da linha de captura põe o cursor no campo, e **a tecla Enter grava** — o
sistema NÃO DEVE (MUST NOT) exigir o acionamento de um botão para confirmar.
Depois de gravar, o campo DEVE (MUST) ficar vazio e ainda com o foco, para que a
captura seguinte seja apenas continuar digitando.

#### Scenario: Tarefa vencendo hoje

- **WHEN** uma tarefa aberta do usuário vence no dia corrente
- **THEN** ela aparece na visão "Hoje" e é contada no total daquela visão

#### Scenario: Tarefa vencida ontem

- **WHEN** uma tarefa aberta do usuário venceu no dia anterior
- **THEN** ela aparece na visão "Atrasadas", e não na visão "Hoje"

#### Scenario: Tarefa sem vencimento

- **WHEN** uma tarefa aberta do usuário não tem data de vencimento
- **THEN** ela não aparece em "Hoje" nem em "Atrasadas", e aparece na visão
  "Sem prazo"

#### Scenario: Criação inline por teclado

- **WHEN** o usuário clica na linha de captura, digita um título e aperta Enter
- **THEN** a tarefa é criada com ele próprio como responsável e passa a aparecer na
  visão correspondente ao seu vencimento, sem recarregar a página e sem que nenhum
  botão precise ser acionado

#### Scenario: Capturas em sequência

- **WHEN** o usuário grava uma tarefa pela linha de captura
- **THEN** o campo volta vazio e mantém o foco, pronto para a próxima sem novo
  clique

#### Scenario: Sessão sem escritório em foco

- **WHEN** um `PlatformAdmin` sem escritório em foco abre a página de tarefas
- **THEN** a linha de captura fica indisponível e a página explica que é preciso
  escolher um escritório, em vez de aceitar o texto e não gravar

#### Scenario: Falha ao carregar os usuários do escritório

- **WHEN** a consulta dos usuários do escritório falha
- **THEN** a linha de captura fica indisponível, a página informa a falha e oferece
  nova tentativa

#### Scenario: Filtro por cliente

- **WHEN** o usuário filtra a lista por um cliente
- **THEN** aparecem apenas as tarefas vinculadas àquele cliente, dentro das que ele já
  poderia enxergar

### Requirement: O hub mostra as tarefas do dia do usuário

O sistema DEVE (MUST) exibir na página inicial uma coluna com as tarefas abertas do
usuário que vencem no dia corrente ou que já estão atrasadas, permitindo concluir,
**editar e excluir** uma tarefa e criar uma tarefa nova sem sair do hub, além de um
acesso à página completa de tarefas.

As ações de linha DEVEM (MUST) ser as mesmas nas duas listas — a do hub e a da
página —, apresentadas como ícones e não como botões de texto, e a exclusão DEVE
(MUST) passar pela mesma confirmação nos dois lugares, com o mesmo aviso sobre o
encerramento de série recorrente.

A criação no hub DEVE (MUST) seguir a mesma regra da página — clicar na linha,
digitar e apertar Enter, sem botão de confirmação, com o campo mantendo o foco
depois de gravar.

O card DEVE (MUST) oferecer também um acesso ao cadastro completo, para as tarefas
que precisam de prazo, recorrência, cliente ou outros responsáveis — o que a linha
de captura não cobre.

A falha ao carregar essa coluna NÃO DEVE (MUST NOT) impedir o restante do hub de ser
exibido.

#### Scenario: Usuário com tarefas do dia

- **WHEN** um usuário com tarefas abertas vencendo hoje acessa a página inicial
- **THEN** a coluna de tarefas lista essas tarefas e oferece o acesso à página
  completa

#### Scenario: Edição a partir do hub

- **WHEN** o usuário aciona a edição de uma tarefa na coluna do hub
- **THEN** abre o formulário completo já preenchido com aquela tarefa, sem que ele
  precise ir até a página de tarefas

#### Scenario: Exclusão a partir do hub

- **WHEN** o usuário aciona a exclusão de uma tarefa na coluna do hub
- **THEN** a mesma confirmação da página de tarefas é apresentada, e nada é excluído
  antes de ela ser confirmada

#### Scenario: Conclusão a partir do hub

- **WHEN** o usuário conclui uma tarefa direto na coluna do hub
- **THEN** a tarefa sai da lista do dia e passa a constar como concluída também na
  página de tarefas

#### Scenario: Criação avançada a partir do hub

- **WHEN** o usuário aciona o acesso ao cadastro completo no card do hub
- **THEN** abre o formulário com vencimento, recorrência, cliente e seleção de
  responsáveis, sem que ele precise ir até a página de tarefas

#### Scenario: Usuário sem tarefas do dia

- **WHEN** um usuário sem tarefas para hoje acessa a página inicial
- **THEN** a coluna exibe um estado vazio com a ação de criar a primeira tarefa

#### Scenario: Falha ao carregar as tarefas

- **WHEN** a carga das tarefas do dia falha
- **THEN** o hub continua exibindo as ferramentas e os certificados, e a coluna de
  tarefas sinaliza a falha

### Requirement: A nota rápida cria uma tarefa sem pedir campo nenhum

O sistema DEVE (MUST) oferecer, na página de tarefas e na página inicial, uma forma
de anotar em texto livre que grava uma tarefa **sem exigir o preenchimento de
campo algum**: o responsável é sempre o próprio usuário que está escrevendo, e a
tarefa nasce **sem data de vencimento** e sem recorrência.

A primeira linha do texto DEVE (MUST) virar o título da tarefa e o restante, a
observação. Quando a primeira linha excede o tamanho de título aceito, o sistema
DEVE (MUST) transferir o excedente para a observação, e NÃO DEVE (MUST NOT) recusar
a gravação por causa do tamanho.

Como a nota nasce sem prazo, ela não aparece entre as tarefas do dia; o sistema
DEVE (MUST) indicar onde ela foi parar em vez de deixá-la sumir de vista.

Quando o usuário não pode ser responsável no escritório em foco — caso possível
apenas para `PlatformAdmin` sem vínculo —, o sistema DEVE (MUST) avisar antes de
tentar gravar e apontar o cadastro completo, onde há escolha de responsável.

#### Scenario: Nota de duas linhas

- **WHEN** o usuário escreve uma nota cuja primeira linha é "Ligar para a Padaria
  Central" e a segunda, "confirmar o balancete de março"
- **THEN** é criada uma tarefa aberta com aquele título, aquela observação, sem
  vencimento e com o próprio usuário como responsável

#### Scenario: Nota de uma linha só

- **WHEN** o usuário escreve uma nota de uma única linha
- **THEN** a tarefa é criada com aquele título e sem observação

#### Scenario: Nota criada a partir da página inicial

- **WHEN** o usuário salva uma nota rápida na página inicial
- **THEN** a tarefa é criada sem prazo e a página indica que a nota está na visão
  "Sem prazo", em vez de simplesmente não exibi-la

#### Scenario: Nota salva na página de tarefas

- **WHEN** o usuário salva uma nota rápida na página de tarefas
- **THEN** a página passa a exibir a visão "Sem prazo", onde a nota está

#### Scenario: Usuário sem vínculo com o escritório em foco

- **WHEN** um `PlatformAdmin` sem vínculo com o escritório em foco tenta salvar uma
  nota rápida
- **THEN** o sistema avisa que ele não é usuário daquele escritório e aponta o
  cadastro completo, sem gravar nada

### Requirement: Excluir uma tarefa recorrente aberta encerra a série

O sistema DEVE (MUST) avisar, antes de excluir uma tarefa aberta com recorrência, que
nenhuma ocorrência seguinte será gerada, e DEVE (MUST) exigir confirmação explícita.

Excluir uma tarefa NÃO DEVE (MUST NOT) apagar as ocorrências anteriores já concluídas.

#### Scenario: Exclusão de ocorrência aberta de série recorrente

- **WHEN** o usuário exclui uma tarefa aberta com recorrência mensal
- **THEN** o sistema pede confirmação informando que a série termina ali, e ao
  confirmar nenhuma ocorrência nova é gerada

#### Scenario: Ocorrências concluídas sobrevivem

- **WHEN** a ocorrência aberta de uma série é excluída
- **THEN** as ocorrências anteriores já concluídas continuam registradas

### Requirement: Tarefas são transversais, não uma ferramenta contratável

O sistema DEVE (MUST) oferecer o controle de tarefas a todo escritório ativo,
independentemente das ferramentas contratadas, por endereço próprio fora da família
de endereços de ferramenta. As tarefas NÃO DEVEM (MUST NOT) constar do catálogo de
ferramentas nem depender de contratação.

#### Scenario: Escritório sem ferramenta contratada

- **WHEN** um usuário de um escritório sem nenhuma ferramenta contratada acessa a
  página de tarefas
- **THEN** a página abre normalmente e ele pode criar e concluir tarefas

#### Scenario: Catálogo de ferramentas

- **WHEN** o catálogo de ferramentas da sessão é carregado
- **THEN** nenhuma ferramenta chamada "tarefas" aparece entre as ferramentas
  contratáveis
