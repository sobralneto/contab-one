## Context

Ver [proposal.md](proposal.md) para a motivação. As restrições que moldam a abordagem:

- **`tsconfig.app.json` inclui `src/**/*.ts`** e liga `noUnusedLocals`/`noUnusedParameters`. Arquivos de teste colocados ao lado do código entram no `vue-tsc -b` do `npm run build` e o quebram por falta dos tipos globais do Vitest.
- **`VITE_API_URL` é embutida no build, não lida em runtime** — gotcha documentado no [PLANO_SAAS_FRONTEND.md §9](../../../PLANO_SAAS_FRONTEND.md). `.env.development` aponta para `http://localhost:5139`, que é exatamente o perfil `http` do `launchSettings.json` da API.
- **O cookie de refresh é `HttpOnly`, `Secure`, `SameSite=Strict`.** Front e API em portas diferentes do mesmo `localhost` continuam sendo *same-site* (porta não conta para same-site), e navegadores tratam `localhost` como contexto seguro mesmo em `http`. O E2E funciona nessas condições — mas é frágil o bastante para merecer verificação explícita logo no primeiro teste.
- **`/api/seed/dev` já existe** e cria escritório + três usuários com senhas conhecidas, um por papel. É `AllowAnonymous` e só existe fora de produção.
- **O `apiClient` guarda estado de módulo** (`isRefreshing`, `failedQueue`). Testes que exercitam concorrência precisam desse estado limpo entre casos.
- **`stores/auth.ts` lê `sessionStorage` na criação da store**, então a ordem entre popular o storage e instanciar a store é significativa.
- **Não existe CI.** Esta change assume execução local.

## Goals / Non-Goals

**Goals:**

- Cobrir a lógica onde tipo não ajuda: as três interpretações de separador em `parseCurrency`, as faixas de `formatRelativeTime`, o mascaramento progressivo de `cnpjMask`.
- Testar o interceptor de refresh como sistema, com concorrência real, não com o axios stubado.
- Amarrar os quatro caminhos que não podem quebrar, contra a stack de verdade.
- Manter a suíte rápida separada da lenta, de forma que a rápida seja rodada durante o desenvolvimento.

**Non-Goals:**

- CI. Fica para uma change própria, reunindo as três suítes.
- Cobertura de todas as views. Views são majoritariamente composição e estilo; o valor está nos composables, no cliente HTTP, nos guards e nos poucos componentes com regra visível.
- Testes de regressão visual. Ferramenta e custo de manutenção diferentes.
- Reescrever qualquer código de produção para facilitar teste. Se algo for difícil de testar, isso é registrado, não contornado com mudança de comportamento.

## Decisions

### 1. MSW no lugar de stub do axios

A alternativa óbvia é `vi.mock('axios')` ou stubar o adapter.

Escolha: MSW, interceptando no nível de rede.

Razão: o que mais se quer testar é o `apiClient` — interceptor de request que anexa o token, interceptor de response que faz refresh, e a fila de concorrência. Stubar o axios remove exatamente esse código do caminho. Com MSW, a requisição percorre os interceptors de verdade e só o transporte é substituído, então o teste falha se alguém quebrar a fila.

O mesmo mock serve aos testes de componente, que passam a exercitar `endpoints/*.ts` reais em vez de funções dubladas.

### 2. jsdom, não happy-dom

happy-dom é mais rápido. jsdom é mais completo e é o ambiente que a documentação de Testing Library e Vue assume.

Escolha: jsdom. A diferença de velocidade não é o gargalo desta suíte, e o código sob teste toca `atob`, `sessionStorage` e `navigator.clipboard` — áreas onde uma implementação incompleta gera falha confusa que parece bug do código, não da ferramenta.

Consequência conhecida: jsdom não implementa navegação, e o interceptor faz `window.location.href = '/login'` quando o refresh falha. O teste desse caminho substitui `window.location` por um duplo, e isso fica comentado no próprio teste — sem a explicação, o próximo a mexer acha que é ruído e remove.

### 3. Arquivos de teste ao lado do código, E2E em pasta separada

`src/**/*.spec.ts` para unitário e componente; `e2e/` para Playwright.

Duas configurações precisam saber dessa fronteira, e errar qualquer uma gera falha confusa:

- **Vitest** precisa excluir `e2e/`. Sem isso ele coleta as specs do Playwright, tenta rodá-las e falha com erro que não menciona a causa.
- **`tsconfig.app.json`** precisa excluir os `*.spec.ts`. Sem isso o `vue-tsc -b` do `npm run build` typechecka os testes sem os tipos globais do Vitest e quebra o build de produção por causa de arquivo de teste.

Um `tsconfig.vitest.json` separado dá aos testes os tipos que eles precisam sem contaminar o build.

Alternativa considerada: pasta `tests/` espelhando `src/`. Descartado — teste longe do código é teste que não é atualizado junto.

### 4. Estado de módulo do `apiClient` é reiniciado entre testes

`isRefreshing` e `failedQueue` vivem no escopo do módulo. Um teste que deixe `isRefreshing: true` faz o seguinte parecer travado, e o sintoma não aponta para a causa.

Escolha: `vi.resetModules()` com reimportação dinâmica do `client.ts` em cada caso que toca refresh, mais Pinia recriado a cada teste.

Alternativa considerada: exportar uma função `__reset()` do `client.ts` só para teste. Descartado — é código de produção existindo para o teste, o oposto do que os Non-Goals estabelecem.

### 5. E2E roda contra a stack real, com `vite dev`

O `VITE_API_URL` embutido no build torna tentador construir um bundle só para teste. Não é necessário: `.env.development` já aponta para `http://localhost:5139`, o perfil `http` da API.

Escolha: Playwright sobe `vite dev` pelo `webServer` da própria configuração e assume Postgres e API já no ar, falhando com mensagem clara se não estiverem. A API **não** é subida pelo Playwright — ela precisa de Postgres migrado e de `ASPNETCORE_ENVIRONMENT=Development`, e esconder isso dentro do runner de teste torna a falha mais difícil de diagnosticar do que um pré-requisito explícito.

Alternativa considerada: mockar a API no E2E. Descartado — aí o teste vira um teste de componente caro. O valor do E2E é justamente cobrir a integração real, incluindo o cookie de refresh e a serialização de enum que difere entre os endpoints do agente e os do frontend.

### 6. Estado do E2E vem de `/api/seed/dev`, e cada teste cria o que precisa

`/api/seed/dev` é idempotente e dá o ponto de partida: um escritório e três usuários, um por papel. O que cada teste cria além disso (cliente, agente) usa nome com sufixo único, para dois testes em paralelo não colidirem no índice único de código de cliente por escritório.

O teste de suspender escritório cria o próprio escritório em vez de suspender o semeado — suspender o compartilhado bloquearia os outros testes, já que `ApiKeyAuthenticationHandler` e os endpoints de agente rejeitam escritório não-Ativo.

Não há limpeza entre execuções: o banco de teste acumula. É aceitável para uma suíte local e evita a complexidade de transação por teste, que não funciona com processo separado de qualquer forma.

### 7. Componentes testados são os que têm regra visível

Testar toda view daria cobertura alta e valor baixo — a maior parte é composição e CSS. Os alvos são os que decidem algo:

- `KpiCard` com valor zero e as três variantes
- `EstadoVazio` e as listas do dashboard sem dados
- Chip de status de escritório nos quatro estados e de execução nos três — o mapa `STATUS_ESCRITORIO` depende da API serializar o enum como **string**, contrato que os testes fixam
- `ConfirmarAcao`, que fica entre o usuário e ações destrutivas

## Risks / Trade-offs

- **E2E exige três processos no ar** → Mitigação: `playwright.config.ts` verifica Postgres e API antes de rodar e falha com instrução do que subir, em vez de dar timeout genérico. O README documenta a sequência.
- **Cookie `SameSite=Strict` pode não sobreviver ao ambiente E2E** → Same-site vale entre portas do mesmo host, então funciona em `localhost`. Mas é a suposição mais frágil da configuração, e o plano §10 já registra o `SameSite` como questão em aberto para domínios de produção. Mitigação: o primeiro teste E2E a rodar é o de login, que exercita o cookie — se essa premissa cair, a falha é imediata e óbvia, não intermitente.
- **Suíte E2E acumula dados no banco de desenvolvimento** → Aceito para execução local. Se incomodar, a saída é um banco separado apontado por `DATABASE_URL`, sem mudar nenhum teste.
- **MSW e a versão do Node** → MSW depende de APIs de interceptação que mudaram entre versões maiores. O ambiente tem Node 24; fixar a major do MSW no `package.json` evita que uma atualização automática quebre a suíte inteira de uma vez.
- **Testes de componente acoplados a texto em português** → Buscar por texto visível é o que Testing Library recomenda e o que torna o teste legível, mas prende o teste à cópia da interface. Aceito conscientemente: a interface é monolíngue e a cópia raramente muda; onde mudar, o teste falha de forma óbvia e barata de corrigir.
- **Playwright baixa navegadores na primeira execução** → Alguns minutos e centenas de MB. Fica documentado no README como passo único de preparação.

## Migration Plan

Não há migração — a change só adiciona arquivos e dependências de desenvolvimento. As duas alterações em arquivos existentes (`package.json` e `tsconfig.app.json`) são aditivas, e a exclusão dos testes do tsconfig protege o build de produção em vez de mudá-lo.

**Rollback**: remover as dependências, os arquivos de teste e as duas configurações. Nenhum código de produção foi alterado.
