## Purpose

TBD

## Requirements

### Requirement: A página inicial é o hub das ferramentas

O sistema DEVE (MUST) abrir, na raiz da aplicação autenticada, uma página
inicial que apresenta as ferramentas em cards agrupados por domínio, cada
card levando à ferramenta correspondente.

#### Scenario: Escritório com ferramentas em dois domínios

- **WHEN** um usuário de escritório com ferramentas contratadas em dois
  domínios entra na aplicação
- **THEN** a página inicial mostra os dois domínios como seções, cada uma
  com o card das ferramentas daquele domínio

#### Scenario: Card leva à ferramenta

- **WHEN** o usuário aciona o card de uma ferramenta contratada
- **THEN** a aplicação navega para a página inicial daquela ferramenta

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
declarada no catálogo. Página não declarada não aparece no menu e não é
alcançável pelo endereço.

#### Scenario: Ferramenta sem página de configuração

- **WHEN** a ferramenta não declara a página de configuração e o usuário
  abre essa ferramenta
- **THEN** o submenu dela não oferece configuração, e o acesso direto ao
  endereço dessa página devolve o usuário à visão geral da ferramenta

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

### Requirement: Ferramenta não contratada aparece só como informativa no hub

O sistema DEVE (MUST) apresentar, na página inicial da sessão de escritório,
as ferramentas ativas não contratadas como cards meramente informativos —
nome, descrição e a marca de não contratada. O card NÃO DEVE (MUST NOT)
oferecer ação alguma: nem navegação para as páginas da ferramenta, nem
contato comercial, nem pedido de contratação.

Para o admin da plataforma o card continua navegável mesmo sem
contratação — a marca de não contratada aparece como informação, não como
bloqueio, coerente com o guard de rota já aceitar qualquer ferramenta ativa
para esse papel.

#### Scenario: Card de ferramenta não contratada

- **WHEN** existe ferramenta ativa no catálogo que o escritório não
  contratou
- **THEN** a página inicial mostra o card dela marcado como não contratada,
  sem números, sem navegação para as páginas da ferramenta e sem nenhum
  elemento acionável

#### Scenario: Admin vê card navegável mesmo sem contratação

- **WHEN** o admin da plataforma abre a página inicial e existe ferramenta
  ativa não contratada por nenhum escritório em foco
- **THEN** o card dela mostra a marca de não contratada, mas continua
  levando à ferramenta ao ser acionado

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
