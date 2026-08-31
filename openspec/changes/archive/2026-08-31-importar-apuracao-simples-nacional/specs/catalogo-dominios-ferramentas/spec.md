## ADDED Requirements

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

## MODIFIED Requirements

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
