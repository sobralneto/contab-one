## Why

Ao acessar a aplicação sem autenticação, o menu lateral (sidebar) e a barra superior do `AppLayout` são exibidos brevemente antes que o guard de rota redirecione para a tela de login. Isso expõe características internas do sistema — itens de navegação, seções administrativas e identificação visual do painel — a qualquer pessoa antes mesmo de informar credenciais. É uma falha de segurança e de experiência do usuário.

## What Changes

- Impedir que o `AppLayout` (sidebar + topbar) seja renderizado antes da resolução do status de autenticação
- Garantir que, durante o bootstrap de autenticação (refresh token), nenhum componente de área logada seja exibido
- Exibir estado de carregamento neutro enquanto a verificação de sessão está em andamento

## Capabilities

### New Capabilities

- `controle-exibicao-layout`: Garantir que layouts de área autenticada jamais sejam exibidos antes da confirmação do status de autenticação do usuário

### Modified Capabilities

<!-- Nenhum spec existente é modificado — esta mudança introduz um novo comportamento de guarda de renderização -->

## Impact

- **ContabOne.Frontend/src/App.vue**: Lógica de seleção de layout precisa considerar estado de inicialização
- **ContabOne.Frontend/src/stores/auth.ts**: Necessário expor estado de bootstrap/carregamento
- **ContabOne.Frontend/src/router/guards.ts**: Guard precisa sinalizar que a verificação inicial está em andamento
