## 1. Auth store — flag de inicialização

- [x] 1.1 Adicionar `ref<boolean> isInitializing` com valor inicial `true` na `useAuthStore` (`ContabOne.Frontend/src/stores/auth.ts`)
- [x] 1.2 Exportar `isInitializing` no retorno da store, ao lado de `isAuthenticated`

## 2. Router guard — controle do ciclo de bootstrap

- [x] 2.1 No `beforeEach` de `ContabOne.Frontend/src/router/guards.ts`, definir `auth.isInitializing = true` antes de iniciar o bootstrap de refresh token
- [x] 2.2 No bloco `finally` do bootstrap, definir `auth.isInitializing = false` (garante que a flag é limpa mesmo em caso de erro)
- [x] 2.3 Garantir que a flag só é alterada no primeiro bootstrap (controlado pela variável `bootstrapped` já existente)

## 3. App.vue — layout neutro durante inicialização

- [x] 3.1 Importar `useAuthStore` em `ContabOne.Frontend/src/App.vue` (se ainda não importado)
- [x] 3.2 Adicionar condição no `computed` de layout: quando `auth.isInitializing` for `true`, retornar um componente de loading neutro em vez de resolver por `route.meta.layout`
- [x] 3.3 Criar o estado visual de carregamento (spinner centralizado, sem sidebar, sem topbar, sem logotipo) — pode ser inline no template com `v-if` ou um componente dedicado mínimo

## 4. Verificação

- [x] 4.1 Testar acesso à raiz (`/`) sem sessão ativa e verificar que nenhum elemento do `AppLayout` (sidebar, topbar) é exibido antes do redirecionamento ao login (validado via automação headless: spinner → `login?redirect=/dashboard`, sem `app-layout` em nenhuma amostra)
- [x] 4.2 Testar acesso direto a `/login` sem sessão ativa e verificar que o `AuthLayout` aparece sem flash do menu lateral (validado via automação headless: spinner → login, sem `app-layout`)
- [x] 4.3 Testar acesso com sessão ativa (token em sessionStorage) e verificar que o `AppLayout` renderiza diretamente, sem flash do spinner por tempo excessivo (validado via automação headless com API mockada: spinner → dashboard)
- [x] 4.4 Testar em conexão lenta (Network throttling no DevTools) para validar que o spinner neutro aparece durante o bootstrap (equivalente validado via automação: spinner visível durante todo o bootstrap em cold load)
- [x] 4.5 Rodar `npm run build` no frontend sem erros
- [x] 4.6 Corrigir flash residual descoberto na verificação: rota ainda não confirmada (`meta.layout` vazio) caía no fallback `AppLayout` — manter `InitializingLayout` nesse caso (`ContabOne.Frontend/src/App.vue`)
