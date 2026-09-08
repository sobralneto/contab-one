## ADDED Requirements

### Requirement: A página de onboarding do cliente exporta o checklist em PDF

A página de onboarding de um cliente DEVE (MUST) oferecer uma ação que gere e
baixe um arquivo PDF com o checklist daquele cliente. A ação DEVE (MUST) estar
disponível a qualquer usuário que já consiga abrir a página — ler e imprimir o
próprio checklist não é ato de administração —, e NÃO DEVE (MUST NOT) aparecer
nos estados em que não há checklist a exportar: cliente sem modelo escolhido e
cliente com modelo mas sem checklist criado.

O nome do arquivo DEVE (MUST) identificar o cliente, para que vários PDFs
baixados na mesma pasta não se confundam entre si.

Enquanto o arquivo é gerado, a ação DEVE (MUST) sinalizar que está em curso e
NÃO DEVE (MUST NOT) aceitar um segundo acionamento — gerar o mesmo documento
duas vezes em paralelo só produz dois downloads iguais.

#### Scenario: Exportação a partir de um checklist existente

- **WHEN** o usuário aciona a exportação na página de onboarding de um cliente
  que tem checklist
- **THEN** um arquivo PDF do checklist daquele cliente é baixado, com nome que
  identifica o cliente

#### Scenario: Usuário comum exporta

- **WHEN** um `EscritorioUsuario` abre o checklist de um cliente e aciona a
  exportação
- **THEN** o PDF é gerado normalmente, sem exigir papel de administrador

#### Scenario: Cliente sem checklist criado

- **WHEN** a página é aberta para um cliente com modelo escolhido mas sem
  checklist criado
- **THEN** a ação de exportar não é oferecida, e a página continua oferecendo a
  criação do checklist

#### Scenario: Cliente sem modelo escolhido

- **WHEN** a página é aberta para um cliente sem modelo de onboarding escolhido
- **THEN** a ação de exportar não é oferecida

#### Scenario: Acionamento durante a geração

- **WHEN** o usuário aciona a exportação e volta a acionar antes de o arquivo
  ficar pronto
- **THEN** o segundo acionamento é ignorado, e um único arquivo é produzido

### Requirement: O PDF apresenta o checklist inteiro, independente do estado da tela

O PDF DEVE (MUST) conter todos os grupos e todas as tarefas do checklist do
cliente, inclusive os grupos que estão recolhidos na tela no momento da
exportação. O que está aberto ou fechado é conveniência de leitura na tela e NÃO
DEVE (MUST NOT) alterar o documento exportado — quem imprime o checklist quer o
checklist, não o recorte que estava visível.

Cada tarefa DEVE (MUST) aparecer no PDF com o nome, o status (aberta ou
concluída), a indicação de segundo fator quando o site exigir, o link quando
houver, os responsáveis atribuídos e a observação escrita para aquele cliente.
Tarefa concluída DEVE (MUST) trazer também o momento da conclusão e quem
concluiu, quando esses dados existirem. Cada grupo DEVE (MUST) trazer o próprio
título e quantas das suas tarefas estão concluídas.

O documento exportado é um documento de leitura: os controles interativos da
página — a caixa de marcação, a seleção de responsáveis, o campo de observação,
o botão de recolher grupo, a navegação e qualquer aviso de erro — NÃO DEVEM
(MUST NOT) aparecer no PDF. O conteúdo que esses controles carregam aparece como
texto.

Uma observação que o usuário acabou de digitar e que ainda não terminou de ser
gravada DEVE (MUST) aparecer no PDF como está na tela: o documento reflete o
checklist que o usuário está vendo.

#### Scenario: Grupo recolhido entra no PDF

- **WHEN** o usuário recolhe um grupo e em seguida exporta o checklist
- **THEN** o PDF contém aquele grupo e todas as tarefas dele

#### Scenario: Tarefa com link, 2FA, responsáveis e observação

- **WHEN** uma tarefa tem link cadastrado, exige segundo fator, tem responsáveis
  atribuídos e uma observação escrita
- **THEN** o PDF apresenta os quatro dados junto do nome da tarefa

#### Scenario: Tarefa concluída

- **WHEN** uma tarefa está concluída e há registro de quando e por quem
- **THEN** o PDF apresenta a tarefa como concluída, com o momento da conclusão e
  o nome de quem concluiu

#### Scenario: Tarefa sem link, sem responsável e sem observação

- **WHEN** uma tarefa não tem link, não tem responsável atribuído e não tem
  observação
- **THEN** o PDF apresenta a tarefa apenas com o nome e o status, sem campos
  vazios pendurados e sem erro

#### Scenario: Controles interativos ficam de fora

- **WHEN** o checklist é exportado
- **THEN** o PDF não contém caixa de marcação clicável, seleção de responsáveis,
  campo de observação editável, botão de recolher grupo nem link de navegação

#### Scenario: Observação recém-digitada

- **WHEN** o usuário digita uma observação e exporta antes de a gravação
  terminar
- **THEN** o PDF traz a observação como digitada

#### Scenario: Modelo sem tarefas

- **WHEN** o checklist exportado vem de um modelo sem nenhum grupo ou tarefa
- **THEN** o PDF é gerado assim mesmo, com o cabeçalho e a indicação de que não
  há tarefas, sem erro

### Requirement: O conteúdo exportado ocupa a largura inteira da página do PDF

O conteúdo do checklist DEVE (MUST) ocupar a largura útil da página do PDF por
inteiro, em todas as páginas do documento e para qualquer volume de conteúdo. O
sistema NÃO DEVE (MUST NOT) reduzir o conteúdo para fazê-lo caber na altura de
uma página, porque reduzir pela altura estreita junto a largura e deixa faixas
brancas nas laterais — o defeito que este requisito existe para impedir.

A largura de renderização do documento DEVE (MUST) ser fixa e conhecida, e o
mapeamento dessa largura para a largura útil da página DEVE (MUST) ser o mesmo
em todos os blocos do documento: dois blocos do mesmo PDF não podem sair em
escalas diferentes, sob pena de o texto de um sair maior que o do outro.

Uma margem lateral uniforme, igual dos dois lados e igual em todas as páginas, é
admitida — "largura inteira" quer dizer sem sobra irregular e sem centralização
de bloco encolhido, não a proibição de margem.

#### Scenario: Checklist curto, de uma página

- **WHEN** o checklist exportado cabe em uma única página
- **THEN** o conteúdo ocupa a largura útil da página, sem faixa branca lateral
  além da margem uniforme

#### Scenario: Checklist longo, de várias páginas

- **WHEN** o checklist exportado ocupa várias páginas
- **THEN** todas as páginas apresentam o conteúdo na mesma largura útil e na
  mesma escala, sem que nenhuma delas apareça encolhida ou centralizada

#### Scenario: Bloco mais alto que a página

- **WHEN** um grupo de tarefas sozinho é mais alto que uma página do PDF
- **THEN** ele é distribuído por páginas mantendo a largura inteira, em vez de
  ser reduzido para caber na altura

### Requirement: A quebra de página respeita os blocos do documento

O documento exportado DEVE (MUST) ser paginado por blocos — o cabeçalho com o
progresso e cada grupo de tarefas —, começando um bloco em página nova sempre
que ele não couber no espaço restante da página corrente. Só o bloco que sozinho
não cabe em uma página inteira DEVE (MUST) ser partido, e a quebra de uma tarefa
ao meio é aceitável apenas nesse caso.

Cortar um grupo no meio da primeira tarefa quando ele caberia inteiro na página
seguinte é o que torna o documento difícil de ler em reunião — é isso que a
regra evita.

#### Scenario: Grupo que não cabe no restante da página

- **WHEN** o próximo grupo não cabe no espaço que sobrou na página corrente, mas
  caberia em uma página inteira
- **THEN** ele começa em página nova, inteiro

#### Scenario: Grupos que cabem juntos

- **WHEN** dois grupos cabem juntos na mesma página
- **THEN** os dois são apresentados na mesma página, sem página em branco entre
  eles

#### Scenario: Grupo maior que uma página inteira

- **WHEN** um grupo sozinho é mais alto que uma página inteira
- **THEN** ele é partido entre páginas, e a continuação segue na página seguinte

### Requirement: O PDF se identifica sozinho

O documento exportado DEVE (MUST) trazer, no início, os dados que permitem
identificá-lo fora do painel: o código e o nome do cliente, o percentual de
conclusão, quantas tarefas estão concluídas de quantas existem, e a data e a
hora em que o arquivo foi gerado.

O documento é lido depois, longe da tela que o originou — sem o momento da
geração, quem recebe o PDF não tem como saber se está olhando o andamento de
hoje ou o do mês passado.

Os valores impressos DEVEM (MUST) ser os mesmos que a página apresenta no
momento da exportação, inclusive marcações feitas e ainda não confirmadas pelo
servidor.

#### Scenario: Cabeçalho do documento

- **WHEN** o checklist de um cliente é exportado
- **THEN** o PDF começa com o código e o nome do cliente, o percentual de
  conclusão, a contagem de tarefas concluídas e do total, e a data-hora da
  geração

#### Scenario: Marcação feita momentos antes da exportação

- **WHEN** o usuário marca uma tarefa como concluída e exporta em seguida
- **THEN** o percentual e a contagem impressos já consideram essa marcação, de
  acordo com o que a página exibe

### Requirement: Falha ao gerar o PDF não derruba a página

Falhando a geração do arquivo, o sistema DEVE (MUST) sinalizar a falha ao
usuário e DEVE (MUST) deixar a página de onboarding intacta e operável — o
checklist carregado continua na tela, e a ação de exportar volta a ficar
disponível para nova tentativa.

#### Scenario: Erro durante a geração

- **WHEN** a geração do PDF falha
- **THEN** o usuário é avisado da falha, o checklist continua na tela como
  estava, e a ação de exportar pode ser acionada de novo
