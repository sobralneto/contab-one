## MODIFIED Requirements

### Requirement: A página inicial é o hub das ferramentas

O sistema DEVE (MUST) abrir, na raiz da aplicação autenticada, uma página
inicial que apresenta as ferramentas em cards agrupados por domínio, cada
card levando à ferramenta correspondente.

A página inicial DEVE (MUST) apresentar os grupos de domínio em uma **faixa
horizontal no topo**, ocupando a largura da página, e abaixo dela **três
colunas**: a primeira com as tarefas do dia do usuário, a segunda com os
certificados a vencer e vencidos, e a terceira reservada, sem conteúdo.

Cada área DEVE (MUST) carregar e falhar de forma independente — a falha de uma
NÃO DEVE (MUST NOT) impedir a exibição das outras.

Em larguras que não comportem as três colunas, elas DEVEM (MUST) empilhar
preservando essa mesma ordem, e a trilha reservada DEVE (MUST) ser a primeira a
sair.

#### Scenario: Escritório com ferramentas em dois domínios

- **WHEN** um usuário de escritório com ferramentas contratadas em dois
  domínios entra na aplicação
- **THEN** a página inicial mostra os dois domínios como seções lado a lado na
  faixa horizontal do topo, cada uma com o card das ferramentas daquele domínio

#### Scenario: Card leva à ferramenta

- **WHEN** o usuário aciona o card de uma ferramenta contratada
- **THEN** a aplicação navega para a página inicial daquela ferramenta

#### Scenario: Hub em tela larga

- **WHEN** um usuário abre a página inicial em uma tela larga
- **THEN** os grupos de domínio ocupam a faixa do topo, e abaixo dela as tarefas do
  dia aparecem na primeira coluna e os certificados na segunda

#### Scenario: Hub em tela estreita

- **WHEN** um usuário abre a página inicial em uma tela estreita
- **THEN** o conteúdo é empilhado na ordem ferramentas, tarefas do dia e certificados

#### Scenario: Nenhum certificado a vencer

- **WHEN** um usuário sem certificado vencido ou a vencer abre a página inicial
- **THEN** a coluna de certificados aparece sem card, e o restante do hub é exibido
  normalmente

#### Scenario: Uma das colunas falha ao carregar

- **WHEN** a carga dos dados de uma das colunas falha
- **THEN** as demais colunas continuam sendo exibidas normalmente
