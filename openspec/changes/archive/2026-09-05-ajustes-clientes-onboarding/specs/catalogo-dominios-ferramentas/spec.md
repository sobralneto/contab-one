## MODIFIED Requirements

### Requirement: A ordem de exibição vem do catálogo

O sistema DEVE (MUST) ordenar a apresentação por ordem do domínio e, dentro
do domínio, por ordem da ferramenta, com o nome como desempate. A ordem vale
para o menu lateral, que é onde as ferramentas são apresentadas agrupadas por
domínio — a página inicial deixou de apresentar ferramentas.

#### Scenario: Duas ferramentas no mesmo domínio

- **WHEN** duas ferramentas do mesmo domínio têm ordens diferentes
- **THEN** ambas aparecem no menu lateral sob o mesmo título de domínio, na
  ordem declarada no catálogo

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
- **THEN** a ferramenta continua aparecendo normalmente no menu lateral para
  quem a contratou, e some apenas do seletor de chaves

#### Scenario: Agente em campo de ferramenta marcada sem agente

- **WHEN** uma ferramenta que tem agentes em campo é marcada como sem agente
  por engano
- **THEN** os agentes existentes continuam autenticando normalmente, e só a
  emissão de chaves novas para ela é interrompida
