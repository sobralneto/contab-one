## Context

Atualmente o `App.vue` seleciona o layout com base em `route.meta.layout`. O fallback é `AppLayout` (sidebar + topbar). Quando um usuário não autenticado acessa a raiz (`/`), o router redireciona para `/dashboard` (layout `app`), e o guard de rota inicia o bootstrap de refresh token. Enquanto essa chamada async está pendente, o Vue já renderiza o `AppLayout` com sidebar visível. Após o bootstrap falhar, o guard redireciona para `/login` e o layout troca para `AuthLayout`. O resultado é um flash de sidebar antes da tela de login.

Ver [proposal.md](proposal.md) para motivação completa.

## Goals / Non-Goals

**Goals:**
- Eliminar o flash do `AppLayout` antes da confirmação do status de autenticação
- Exibir estado de carregamento neutro durante o bootstrap de sessão
- Manter a experiência atual para usuários autenticados (sem regressão)

**Non-Goals:**
- Alterar o fluxo de autenticação (login/refresh/logout)
- Modificar a estrutura de rotas ou o mecanismo de guards
- Implementar skeleton screens ou animações elaboradas de loading
- Alterar o `AuthLayout` ou o `AppLayout` em si

## Decisions

### Decisão 1: Adicionar flag `isInitializing` na store de auth

**Escolha:** Adicionar uma ref `isInitializing` (boolean, default `true`) na `useAuthStore` que indica se o bootstrap de autenticação ainda está em andamento. O guard define `isInitializing = true` antes do bootstrap e `isInitializing = false` ao concluir (sucesso ou falha).

**Alternativa considerada:** Estado local no `App.vue`. Descartada porque o guard precisa acessar esse estado para sinalizar progresso, e `App.vue` não tem acesso direto ao ciclo do guard.

**Alternativa considerada:** Usar `bootstrapping` já existente no módulo `guards.ts`. Descartada porque é uma variável de módulo (não reativa) e o `App.vue` não pode observá-la reativamente.

### Decisão 2: Layout neutro durante inicialização

**Escolha:** Em `App.vue`, quando `auth.isInitializing` for `true`, renderizar um componente neutro (`InitializingLayout` ou um template inline) em vez de resolver por `route.meta.layout`. Este componente exibe apenas um spinner centralizado, sem sidebar, topbar, ou identificação do sistema.

**Alternativa considerada:** Retornar `null` ou `<div></div>` do template. Descartada — o usuário veria uma tela em branco sem feedback, causando percepção de falha no carregamento.

**Alternativa considerada:** Manter `AuthLayout` como fallback em vez de `AppLayout`. Descartada — isso só inverteria o problema (mostraria o layout de login antes de confirmar autenticação) e criaria um flash do `AuthLayout` quando o usuário já tem sessão ativa.

**Descoberta na verificação (aplicada):** além de `isInitializing`, o fallback `default: AppLayout` do `switch` também causava flash: entre o fim do bootstrap (`isInitializing = false`) e a **confirmação da navegação** para a rota alvo (que depende do `import()` lazy do componente + `enterGuards`), `route.meta.layout` ainda é vazio (rota = START_LOCATION) e o `switch` caía no fallback. Reproduzido via automação headless (`app-layout=true` por ~100ms entre o spinner e o login). Correção: quando `route.meta.layout` for vazio (rota não confirmada), manter o `InitializingLayout` em vez de resolver o layout.

### Decisão 3: Reset do `isInitializing` via guard

**Escolha:** O guard `beforeEach` é responsável por gerenciar `isInitializing`: seta `true` quando inicia o bootstrap e `false` no `finally` do bloco bootstrap. A flag só é alterada no primeiro bootstrap (controlado por `bootstrapped`).

**Alternativa considerada:** Gerenciar via hook `router.isReady()`. Descartada porque `isReady()` resolve após a primeira navegação completa, mas o flash ocorre durante, não após.

## Risks / Trade-offs

- **[Risk] Usuário com conexão lenta vê spinner por mais tempo** → Aceitável. Um spinner neutro é muito preferível a expor o menu lateral. O bootstrap de refresh token é tipicamente rápido (< 1s em conexões normais).
- **[Risk] Se o refresh nunca responder (timeout), spinner fica eternamente** → Mitigação: o `axios` usado no refresh tem timeout configurado globalmente. Além disso, o bloco `finally` garante `isInitializing = false` mesmo em caso de erro.
- **[Risk] Flash no carregamento inicial com sessão ativa** → Mitigação: o fluxo é: spinner → bootstrap conclui com sucesso → `isInitializing = false` → `AppLayout` renderiza. A transição do spinner para o AppLayout é limpa e esperada.
- **[Trade-off] Adiciona complexidade à seleção de layout** → O acréscimo é mínimo (uma condição adicional no computed). A store de auth ganha uma nova propriedade reativa simples.
