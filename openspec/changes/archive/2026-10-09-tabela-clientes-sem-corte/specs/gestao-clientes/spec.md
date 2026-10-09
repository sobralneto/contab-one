## ADDED Requirements

### Requirement: A tabela de clientes usa a largura disponível e nunca oculta a coluna de ações

A tela de clientes DEVE (MUST) usar toda a largura útil da área de conteúdo para a tabela, sem um teto fixo menor que ela, de modo que os dados de uma linha caibam sem quebra desnecessária.

CNPJ, escritório (visão admin), regime e data de atualização (com a origem) NÃO DEVEM (MUST NOT) quebrar linha: cada um DEVE (MUST) ocupar uma linha só. O nome do cliente PODE (MAY) quebrar linha — é o texto de comprimento livre e é ele que absorve a falta de largura.

A coluna de ações NÃO DEVE (MUST NOT) ser cortada ou ocultada em nenhuma largura de janela. Quando a janela for estreita demais para todas as colunas, o cartão da tabela DEVE (MUST) oferecer rolagem horizontal, mantendo todas as colunas, inclusive a de ações, alcançáveis.

Esta regra vale para **todos os papéis** que enxergam a listagem, com ou sem a coluna de escritório. Colunas, ordem, ordenação, filtros e comportamento dos botões NÃO DEVEM (MUST NOT) mudar.

#### Scenario: Janela larga mostra os dados sem quebra de linha

- **WHEN** o usuário abre a tela de clientes em janela larga
- **THEN** o CNPJ aparece completo numa linha só (ex.: `07.467.651/0001-35`)
- **AND** o nome do escritório (visão admin), o regime e a data de atualização também aparecem numa linha cada

#### Scenario: Os botões da última coluna ficam visíveis

- **WHEN** o usuário abre a tela de clientes em janela larga
- **THEN** todos os botões de ação da linha (onboarding quando houver, editar, inativar ou reativar, excluir) estão inteiros dentro da área visível do cartão

#### Scenario: Janela estreita rola em vez de cortar

- **WHEN** a janela é estreita demais para caberem todas as colunas
- **THEN** o cartão da tabela exibe rolagem horizontal
- **AND** rolando até o fim o usuário alcança os botões de ação, inteiros

#### Scenario: Nome longo quebra em vez de empurrar a tabela

- **WHEN** um cliente tem razão social longa
- **THEN** o nome pode ocupar mais de uma linha
- **AND** as demais colunas e a coluna de ações continuam visíveis na mesma largura

#### Scenario: Visão do administrador com a coluna de escritório

- **WHEN** um administrador de plataforma abre a tela de clientes
- **THEN** as regras acima valem com a coluna de escritório presente, e o nome do escritório não quebra linha
