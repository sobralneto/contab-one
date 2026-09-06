## MODIFIED Requirements

### Requirement: A página inicial é o hub das ferramentas

A página inicial da aplicação autenticada DEVE (MUST) ser o **painel do
escritório**: o que ela apresenta é o trabalho em aberto do escritório, e NÃO
mais um lançador de ferramentas. Os cards de ferramenta agrupados por domínio
saem dela — a navegação por ferramenta é responsabilidade do **menu lateral**,
que continua agrupando por domínio e é o único lugar que precisa dela.

A página DEVE (MUST) se organizar em **duas colunas**: a primeira com as
tarefas do dia do usuário, ocupando-a por inteiro; a segunda com o **cartão de
certificados** acima e os **clientes em onboarding** abaixo.

Tarefas fica sozinha na própria coluna por ser a lista que mais cresce — dividir
a coluna com ela empurraria o vizinho para fora da primeira tela conforme o dia
enche.

O cartão de certificados DEVE (MUST) agrupar, sob um título único, três
contagens que não se sobrepõem e que DEVEM (MUST) dividir em partes iguais a
largura do cartão, sem sobra à direita: **vencidos** (a validade já passou), **vencendo
em até 3 dias** e **vencendo de 4 a 30 dias**. As três são recortes do mesmo
assunto e DEVEM (MUST) ser lidas como um conjunto, não como indicadores
independentes competindo entre si na página.

Como o título do cartão já identifica o assunto, cada contagem DEVE (MUST) ser
rotulada apenas pela faixa que representa, sem repetir o substantivo
"certificados" em cada uma.

Cada contagem DEVE (MUST) levar à listagem de clientes com a faixa
correspondente já aplicada, e o conjunto aberto DEVE (MUST) ser exatamente o que
a contagem somou — contagem que abre uma lista de outro tamanho é pior do que
contagem sem link, porque o usuário não tem como saber qual dos dois números
vale.

Cada contagem DEVE (MUST) ser distinguível das outras à primeira vista, e as
três DEVEM (MUST) ser exibidas mesmo valendo zero — o zero é a confirmação de
que não há pendência, e ocultar o contador deixaria o usuário sem saber se não
há nada ou se a informação não carregou.

As contagens DEVEM (MUST) ser apuradas sobre todos os clientes do escopo, e não
sobre uma amostra ou uma lista truncada: um contador que erra em escritório
grande é pior do que contador nenhum.

Certificado que vence depois de 30 dias NÃO DEVE (MUST NOT) entrar em nenhuma
das três faixas.

Nenhum conteúdo da página depende do catálogo de ferramentas. Falhando a carga
do catálogo, a página DEVE (MUST) sinalizar a falha e oferecer nova tentativa —
porque é o menu lateral que fica vazio —, mas NÃO DEVE (MUST NOT) esconder o
painel atrás dessa falha: contadores, tarefas e onboarding continuam visíveis e
utilizáveis.

Cada área DEVE (MUST) carregar e falhar de forma independente — a falha de uma
NÃO DEVE (MUST NOT) impedir a exibição das outras.

Em larguras que não comportem o arranjo completo, as colunas DEVEM (MUST)
empilhar — tarefas, certificados e onboarding, nessa ordem — e os contadores
DEVEM (MUST) quebrar em mais de uma linha dentro do próprio cartão.

#### Scenario: Página inicial em tela larga

- **WHEN** um usuário abre a página inicial em uma tela larga
- **THEN** as tarefas do dia ocupam a primeira coluna, e a segunda traz o cartão
  de certificados acima — com as três contagens lado a lado, dividindo a largura
  dele — e o onboarding abaixo

#### Scenario: Página inicial em tela estreita

- **WHEN** um usuário abre a página inicial em uma tela estreita
- **THEN** o conteúdo é empilhado na ordem tarefas do dia, cartão de
  certificados e onboarding

#### Scenario: Nenhum card de ferramenta na página inicial

- **WHEN** um usuário de escritório com ferramentas contratadas abre a página
  inicial
- **THEN** a página não apresenta card de ferramenta algum, e as ferramentas
  continuam acessíveis pelo menu lateral, agrupadas por domínio

#### Scenario: Nenhum certificado a vencer

- **WHEN** um usuário sem certificado vencido ou a vencer abre a página inicial
- **THEN** o cartão de certificados aparece com as três contagens em zero, e o
  restante do painel é exibido normalmente

#### Scenario: Abrir a listagem a partir de uma contagem

- **WHEN** o usuário aciona uma das três contagens do cartão de certificados
- **THEN** a listagem de clientes abre com aquela faixa aplicada, e a quantidade
  de clientes listados corresponde ao número que estava no cartão

#### Scenario: Contagem em zero

- **WHEN** o usuário aciona uma contagem que está em zero
- **THEN** a listagem abre com a faixa aplicada e apresenta o estado vazio, sem
  erro

#### Scenario: Certificado fora do horizonte

- **WHEN** um cliente tem certificado que vence daqui a mais de 30 dias
- **THEN** ele não é somado em nenhum dos três contadores

#### Scenario: Cliente sem certificado

- **WHEN** um cliente não tem validade de certificado registrada
- **THEN** ele não é somado em nenhum dos três contadores

#### Scenario: Catálogo não carrega

- **WHEN** a carga do catálogo de ferramentas falha
- **THEN** a página inicial sinaliza a falha e oferece nova tentativa, e ainda
  assim exibe o cartão de certificados, as tarefas do dia e o onboarding

#### Scenario: Uma das áreas falha ao carregar

- **WHEN** a carga dos dados de uma das áreas falha
- **THEN** as demais continuam sendo exibidas normalmente
