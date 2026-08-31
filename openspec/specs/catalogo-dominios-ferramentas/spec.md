## Purpose

TBD

## Requirements

### Requirement: Toda ferramenta do catálogo pertence a um domínio

O sistema DEVE (MUST) associar cada ferramenta do hub a exatamente um
domínio do catálogo. Domínio é dado — vive em tabela, com código, nome e
ordem — e não uma lista fixa no código da API ou do frontend.

#### Scenario: Cadastro de ferramenta sem domínio

- **WHEN** o admin da plataforma tenta cadastrar ou atualizar uma ferramenta
  sem informar o domínio, ou com um código de domínio que não existe
- **THEN** o cadastro é recusado com o motivo, e nenhuma ferramenta sem
  domínio passa a existir no catálogo

#### Scenario: Ferramenta cadastrada em domínio existente

- **WHEN** o admin cadastra uma ferramenta informando um domínio já
  existente
- **THEN** a ferramenta passa a aparecer agrupada naquele domínio para todos
  os papéis que a enxergam, sem exigir alteração de código no frontend

### Requirement: A ordem de exibição vem do catálogo

O sistema DEVE (MUST) ordenar a apresentação por ordem do domínio e, dentro
do domínio, por ordem da ferramenta, com o nome como desempate. A ordem é a
mesma no menu lateral e na página inicial.

#### Scenario: Duas ferramentas no mesmo domínio

- **WHEN** duas ferramentas do mesmo domínio têm ordens diferentes
- **THEN** ambas aparecem sob o mesmo título de domínio, na ordem declarada
  no catálogo, tanto no menu quanto na página inicial

### Requirement: Cada ferramenta declara as páginas que possui

O sistema DEVE (MUST) armazenar, junto da ferramenta, quais páginas ela
oferece dentro do conjunto conhecido pela aplicação (visão geral, importação,
execuções, configuração, regras de coleta). Página fora desse conjunto é
recusada no cadastro.

Clientes e Agentes não fazem parte desse conjunto: as duas telas mostram
dado do escritório inteiro, não particionado por ferramenta, e vivem em
rotas transversais fora do catálogo por produto.

#### Scenario: Ferramenta que não oferece todas as páginas

- **WHEN** uma ferramenta declara apenas visão geral e execuções
- **THEN** o catálogo entregue à sessão lista somente essas duas páginas
  para aquela ferramenta

#### Scenario: Página desconhecida no cadastro

- **WHEN** o admin tenta declarar uma página que a aplicação não conhece
- **THEN** o cadastro é recusado com o motivo, indicando os valores aceitos

#### Scenario: Ferramenta de importação de documento

- **WHEN** uma ferramenta declara visão geral e importação
- **THEN** o submenu dela oferece as duas, e nem execuções nem configuração
  são alcançáveis pelo endereço

### Requirement: O catálogo traz sempre o ativo inteiro, marcado por contratação

O sistema DEVE (MUST) entregar, tanto à sessão de escritório quanto ao admin
da plataforma, o catálogo de ferramentas ativas **inteiro** — nunca só o que
foi contratado —, com o domínio e as páginas de cada uma, e cada ferramenta
marcada como contratada ou não pelo escopo resolvido. A navegação por
domínio depende de conhecer a ferramenta não contratada para apresentá-la
como indisponível; omiti-la do catálogo impediria isso.

Sem escopo resolvido (admin da plataforma sem escritório em foco), toda
ferramenta vem marcada como não contratada.

Um consumidor que precise só do contratado — como o seletor de nova chave de
agente — filtra pela marca, em vez de depender do servidor omitir o resto.

#### Scenario: Escritório com uma ferramenta de dois domínios contratada

- **WHEN** um usuário de escritório com apenas a ferramenta de NFS-e
  contratada pede o catálogo da sessão
- **THEN** a resposta traz todas as ferramentas ativas — incluindo as não
  contratadas —, e só a de NFS-e vem marcada como contratada

#### Scenario: Admin com escritório em foco

- **WHEN** o admin pede o catálogo indicando um escritório
- **THEN** a resposta traz todas as ferramentas ativas, e cada uma indica se
  aquele escritório a contratou

#### Scenario: Admin sem escritório em foco

- **WHEN** o admin pede o catálogo sem indicar escritório
- **THEN** a resposta traz todas as ferramentas ativas, nenhuma marcada como
  contratada, e nenhum erro é devolvido

### Requirement: A ferramenta declara se tem agente

O sistema DEVE (MUST) registrar, junto da ferramenta do catálogo, se ela é
operada por um agente instalado na máquina do escritório. Ferramenta sem
agente NÃO DEVE (MUST NOT) ser oferecida como destino de uma chave de API
nova, porque nenhum binário vai usá-la.

Este atributo governa apenas a **oferta** de chave, na mesma família de
`Ativo`. Ele NÃO DEVE (MUST NOT) participar da autenticação: o handshake
continua comparando o código da chave apresentada com o da ferramenta do
próprio agente, sem consultar o catálogo.

#### Scenario: Seletor de nova chave de agente

- **WHEN** o usuário abre a geração de uma chave nova e o escritório contratou
  ferramentas com e sem agente
- **THEN** apenas as ferramentas com agente aparecem como destino possível da
  chave

#### Scenario: Ferramenta sem agente marcada no cadastro

- **WHEN** o admin da plataforma cadastra ou edita uma ferramenta indicando
  que ela não tem agente
- **THEN** a ferramenta continua aparecendo normalmente no menu e no hub para
  quem a contratou, e some apenas do seletor de chaves

#### Scenario: Agente em campo de ferramenta marcada sem agente

- **WHEN** uma ferramenta que tem agentes em campo é marcada como sem agente
  por engano
- **THEN** os agentes existentes continuam autenticando normalmente, e só a
  emissão de chaves novas para ela é interrompida
