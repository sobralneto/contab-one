## ADDED Requirements

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

## MODIFIED Requirements

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
