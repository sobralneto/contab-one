## Purpose

Garante que layouts de área autenticada (sidebar, topbar, navegação) jamais sejam renderizados antes da confirmação definitiva do status de autenticação do usuário, prevenindo exposição de características internas do sistema.

## Requirements

### Requirement: Layout padrão é neutro durante inicialização

O sistema DEVE (MUST) renderizar um estado neutro (sem sidebar, sem topbar, sem navegação) enquanto a verificação inicial de sessão está em andamento. Nenhum componente do `AppLayout` DEVE ser visível até que a autenticação seja confirmada.

#### Scenario: Acesso inicial sem sessão ativa

- **WHEN** um usuário acessa qualquer rota da aplicação pela primeira vez e a verificação de token de refresh está em andamento
- **THEN** o sistema exibe um estado visual neutro e mínimo (sem menu lateral, sem barra superior, sem itens de navegação)

#### Scenario: Acesso inicial com sessão ativa restaurada

- **WHEN** a verificação de token de refresh conclui com sucesso e a sessão é restaurada
- **THEN** o sistema transiciona do estado neutro para o `AppLayout` com sidebar e topbar

### Requirement: AppLayout só renderiza com autenticação confirmada

O sistema DEVE (MUST) renderizar o `AppLayout` (sidebar, barra superior, área de conteúdo autenticado) somente após o status de autenticação ser confirmado como positivo.

#### Scenario: Usuário autenticado acessa rota protegida

- **WHEN** o status de autenticação está confirmado como positivo e o usuário acessa uma rota protegida
- **THEN** o sistema renderiza o `AppLayout` completo com sidebar, topbar e conteúdo da rota

#### Scenario: Usuário não autenticado é redirecionado ao login

- **WHEN** a verificação de sessão conclui que o usuário não está autenticado
- **THEN** o sistema redireciona para `/login` e renderiza o `AuthLayout` (layout centrado, sem sidebar)

### Requirement: Componente de carregamento é visualmente neutro

O sistema DEVE (MUST) exibir um componente de carregamento durante a verificação de sessão que seja visualmente neutro — sem logotipo, nome do sistema, navegação ou qualquer elemento estrutural que revele o design interno da aplicação.

#### Scenario: Exibição do estado de carregamento

- **WHEN** o sistema está verificando a sessão durante o bootstrap
- **THEN** a tela exibe apenas um indicador de progresso mínimo (como um spinner) sem revelar elementos estruturais do painel administrativo

### Requirement: Menu de ferramentas só aparece com o catálogo resolvido

O sistema DEVE (MUST) manter o menu de ferramentas ausente enquanto o
catálogo da sessão não tiver sido resolvido. Nenhum item de ferramenta pode
ser renderizado a partir de suposição, valor padrão ou resíduo de sessão
anterior — só a partir do catálogo daquela sessão.

#### Scenario: Layout montado antes do catálogo chegar

- **WHEN** a sessão já está confirmada e a carga do catálogo ainda está em
  andamento
- **THEN** o layout exibe a área de navegação sem nenhum item de ferramenta
  e sem título de domínio, e passa a exibi-los quando o catálogo chega

#### Scenario: Catálogo não carrega

- **WHEN** a carga do catálogo da sessão falha
- **THEN** a aplicação mantém o acesso à página inicial e aos itens que não
  dependem de ferramenta, sinaliza a falha e oferece nova tentativa, sem
  encerrar a sessão

### Requirement: Troca de sessão descarta o catálogo anterior

O sistema DEVE (MUST) descartar o catálogo carregado ao encerrar a sessão **e ao trocar o
escritório em foco**, de modo que o menu de um escritório nunca seja exibido para o
escritório seguinte.

A troca de foco tem o mesmo efeito do logout sobre o catálogo: o catálogo pertence ao
escritório, não ao usuário. Ver [[escritorio-em-foco]].

#### Scenario: Logout seguido de login de outro escritório

- **WHEN** um usuário sai e outro usuário, de escritório diferente, entra na
  mesma aba
- **THEN** o menu exibido é o do catálogo do segundo escritório, sem nenhum
  item remanescente do primeiro

#### Scenario: Troca de escritório em foco na mesma sessão

- **WHEN** um usuário vinculado a dois escritórios troca o foco sem sair do sistema
- **THEN** o menu exibido é o do catálogo do novo escritório, sem nenhum item remanescente
  do anterior

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
