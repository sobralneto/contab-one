## Purpose

Garante que layouts de área autenticada (sidebar, topbar, navegação) jamais sejam renderizados antes da confirmação definitiva do status de autenticação do usuário, prevenindo exposição de características internas do sistema.

## ADDED Requirements

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
