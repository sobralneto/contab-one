## MODIFIED Requirements

### Requirement: Troca de sessão descarta o catálogo anterior

O sistema DEVE (MUST) descartar o catálogo carregado ao encerrar a sessão **e ao trocar o
escritório em foco**, de modo que o menu de um escritório nunca seja exibido para o
escritório seguinte.

A troca de foco tem o mesmo efeito do logout sobre o catálogo: o catálogo pertence ao
escritório, não ao usuário. Ver [[escritorio-em-foco]].

#### Scenario: Logout seguido de login de outro escritório

- **WHEN** um usuário sai e outro usuário, de escritório diferente, entra na mesma aba
- **THEN** o menu exibido é o do catálogo do segundo escritório, sem nenhum item
  remanescente do primeiro

#### Scenario: Troca de escritório em foco na mesma sessão

- **WHEN** um usuário vinculado a dois escritórios troca o foco sem sair do sistema
- **THEN** o menu exibido é o do catálogo do novo escritório, sem nenhum item remanescente
  do anterior

## ADDED Requirements

### Requirement: A barra superior identifica o escritório da sessão

O sistema DEVE (MUST) incluir na barra superior da área autenticada a identificação do
escritório em foco, com o mesmo tratamento de exibição das demais partes do `AppLayout`:
ela NÃO DEVE (MUST NOT) aparecer antes de a autenticação estar confirmada, e NÃO DEVE
(MUST NOT) exibir nome de escritório vindo de resíduo de sessão anterior.

#### Scenario: Bootstrap antes da confirmação de sessão

- **WHEN** a verificação inicial de sessão está em andamento
- **THEN** nenhuma identificação de escritório é exibida, coerente com o estado neutro do
  layout

#### Scenario: Sessão confirmada

- **WHEN** a autenticação é confirmada e o `AppLayout` é renderizado
- **THEN** a barra superior exibe a identificação do escritório em foco junto aos demais
  elementos do topo
