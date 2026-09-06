## Purpose

TBD

## Requirements

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

### Requirement: O menu lateral agrupa ferramentas por domínio

O sistema DEVE (MUST) montar o menu lateral a partir do catálogo da sessão,
agrupando as ferramentas sob o título do domínio a que pertencem. Ferramenta
nova no catálogo aparece no menu sem alteração de código do frontend.

#### Scenario: Ferramenta acrescentada ao catálogo

- **WHEN** uma ferramenta é cadastrada e contratada para o escritório, e o
  usuário inicia uma nova sessão
- **THEN** ela aparece no menu lateral, sob o título do domínio dela, sem
  que nenhum item de menu tenha sido escrito no template

### Requirement: O submenu mostra só as páginas que a ferramenta declara

O sistema DEVE (MUST) montar as páginas de cada ferramenta a partir da lista
declarada no catálogo. Página do conjunto conhecido que a ferramenta não
declara não aparece no menu e não é alcançável pelo endereço.

Isso vale para as páginas do conjunto fechado do catálogo. Endereços de
detalhe de uma ferramenta — o registro específico aberto a partir de uma
lista — não são páginas declaráveis e seguem a regra própria: fora do menu,
sujeitos ao mesmo gate de contratação.

#### Scenario: Ferramenta sem página de configuração

- **WHEN** a ferramenta não declara a página de configuração e o usuário
  abre essa ferramenta
- **THEN** o submenu dela não oferece configuração, e o acesso direto ao
  endereço dessa página devolve o usuário à visão geral da ferramenta

#### Scenario: Ferramenta com página de importação

- **WHEN** a ferramenta declara importação e o usuário a abre
- **THEN** o submenu dela oferece a importação, ao lado das demais páginas
  declaradas

### Requirement: Ferramenta pode ter rota de detalhe fora do menu

O sistema DEVE (MUST) permitir que uma ferramenta tenha endereços de detalhe
além das páginas que declara — a visualização de um registro específico
alcançada a partir de uma lista. Rota de detalhe NÃO DEVE (MUST NOT) aparecer
no menu, e DEVE (MUST) estar sujeita ao mesmo gate de ferramenta existente e
contratada que vale para as páginas declaradas.

#### Scenario: Detalhe aberto a partir da lista

- **WHEN** o usuário aciona um registro na lista de uma ferramenta contratada
- **THEN** a aplicação abre o endereço de detalhe daquele registro, e o
  submenu da ferramenta continua exibindo apenas as páginas declaradas

#### Scenario: Detalhe de ferramenta não contratada

- **WHEN** um usuário de escritório abre direto o endereço de detalhe de uma
  ferramenta que o escritório não contratou
- **THEN** a aplicação o devolve à página inicial, e nenhuma requisição de
  dado daquela ferramenta é disparada

#### Scenario: Detalhe guardado como favorito

- **WHEN** o usuário abre direto um endereço de detalhe de ferramenta que ele
  contratou
- **THEN** a página é exibida normalmente, sem passar pela lista

### Requirement: Domínio sem ferramenta contratada não aparece para o escritório

O sistema DEVE (MUST) omitir do menu lateral, na sessão de escritório, todo
domínio que não tenha ao menos uma ferramenta contratada. O admin da
plataforma enxerga todos os domínios do catálogo.

#### Scenario: Escritório sem nenhuma ferramenta do domínio Contábil

- **WHEN** o escritório não contratou nenhuma ferramenta do domínio Contábil
- **THEN** o menu lateral não exibe o título desse domínio nem qualquer item
  sob ele

#### Scenario: Admin da plataforma

- **WHEN** o admin da plataforma navega na aplicação
- **THEN** o menu lateral exibe todos os domínios e todas as ferramentas
  ativas do catálogo

### Requirement: O endereço da página carrega a ferramenta

O sistema DEVE (MUST) identificar a ferramenta no próprio endereço das
páginas dela, de modo que o mesmo tipo de página de duas ferramentas tenha
endereços distintos e possa ser aberto direto ou guardado como favorito.

#### Scenario: Mesma página em duas ferramentas

- **WHEN** o usuário abre as execuções da ferramenta de NFS-e e as execuções
  da ferramenta de DET
- **THEN** cada uma tem endereço próprio, e abrir esse endereço direto no
  navegador leva à página daquela ferramenta

#### Scenario: Ferramenta inexistente no endereço

- **WHEN** o endereço aponta para uma ferramenta que não existe no catálogo
- **THEN** a aplicação devolve o usuário à página inicial

### Requirement: Ferramenta não contratada não é alcançável pelo endereço

O sistema DEVE (MUST) recusar a navegação para páginas de ferramenta que a
sessão não contratou, devolvendo o usuário à página inicial em vez de exibir
tela vazia ou com erro de permissão.

#### Scenario: Acesso direto a ferramenta não contratada

- **WHEN** um usuário de escritório digita o endereço de uma página de
  ferramenta que o escritório não contratou
- **THEN** a aplicação o devolve à página inicial, e nenhuma requisição de
  dado daquela ferramenta é disparada

#### Scenario: Admin acessa qualquer ferramenta

- **WHEN** o admin da plataforma abre o endereço de qualquer ferramenta
  ativa do catálogo
- **THEN** a página é exibida normalmente

### Requirement: Os endereços anteriores continuam chegando na tela certa

O sistema DEVE (MUST) redirecionar os endereços das páginas de ferramenta
anteriores (visão geral, execuções, configuração) para a página equivalente
da ferramenta de NFS-e, preservando o que estiver na query string. Clientes
e Agentes NÃO são redirecionados — seus endereços (`/clientes`, `/agentes`)
já eram os corretos antes desta mudança e continuam sendo, porque as duas
telas nunca dependeram de qual ferramenta está na URL.

#### Scenario: Link antigo guardado pelo usuário

- **WHEN** o usuário abre um endereço de página de ferramenta no formato
  anterior, com ou sem query string
- **THEN** a aplicação o leva à mesma página sob a ferramenta de NFS-e, com
  a query string preservada

#### Scenario: Endereço de Clientes ou Agentes não é redirecionado

- **WHEN** o usuário abre `/clientes` ou `/agentes`
- **THEN** a aplicação exibe a página diretamente, sem redirecionar para
  nenhum endereço sob `/f/:produto/`

### Requirement: Toda página de ferramenta identifica a ferramenta

O sistema DEVE (MUST) exibir, no cabeçalho de qualquer página de ferramenta,
o nome da ferramenta a que os dados da tela pertencem, além do título da
própria página.

#### Scenario: Página de execuções de uma ferramenta

- **WHEN** o usuário abre as execuções de uma ferramenta
- **THEN** o cabeçalho identifica a ferramenta e a página, deixando claro a
  qual produto os números da tela se referem

### Requirement: Página de ferramenta pode ter restrição de papel mais estrita que a ferramenta

O sistema DEVE (MUST) permitir que uma página declarada por uma ferramenta
tenha exigência de papel mais restrita do que as demais páginas da mesma
ferramenta — em particular, o cadastro de regras de coleta é exclusivo de
PlatformAdmin, mesmo quando a ferramenta também tem páginas abertas a
EscritorioAdmin.

#### Scenario: EscritorioAdmin tenta acessar o cadastro de regras

- **WHEN** um usuário EscritorioAdmin abre o endereço do cadastro de regras
  de uma ferramenta que o declara
- **THEN** a aplicação devolve o usuário à página inicial, mesmo que aquele
  usuário acesse normalmente as outras páginas da mesma ferramenta

#### Scenario: PlatformAdmin acessa o cadastro de regras

- **WHEN** o admin da plataforma abre o endereço do cadastro de regras de
  uma ferramenta que o declara
- **THEN** a página é exibida normalmente, abaixo do item de Configuração
  no submenu daquela ferramenta
