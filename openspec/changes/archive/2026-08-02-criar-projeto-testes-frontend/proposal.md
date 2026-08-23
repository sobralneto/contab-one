## Why

O frontend não tem nenhum teste. O `package.json` tem três scripts (`dev`, `build`, `preview`) e nenhuma dependência de teste, e a única verificação automatizada hoje é o `vue-tsc` embutido no `build` — que garante tipos, não comportamento.

A lógica mais sutil da camada está justamente onde tipo nenhum ajuda: `parseCurrency` decide entre três interpretações diferentes de ponto e vírgula em pt-BR; `cnpjMask` reformata a cada tecla; `formatRelativeTime` tem quatro faixas; e o interceptor de refresh do `apiClient` coordena fila de requisições, flag de `_retry` e redirecionamento — o [PLANO_SAAS_FRONTEND.md §8](../../../PLANO_SAAS_FRONTEND.md) chama esse último de "exatamente o tipo de bug que só teste pega".

O plano já define o stack pretendido (Vitest, Testing Library, Playwright, MSW). Nada disso foi instalado.

## What Changes

- Instalar e configurar **Vitest** com ambiente jsdom, mais o tsconfig e os scripts de `package.json` correspondentes.
- **Testes unitários**: composables (`useInputMask`, `useFormatters`), utilitários de JWT (`decodeJwt`, `isJwtExpired`), stores (`auth`, `ui`) e os guards de rota.
- **Teste do interceptor de refresh** do `apiClient`: 401 dispara refresh e repete a requisição, requisições concorrentes entram na fila em vez de dispararem refreshes paralelos, e falha no refresh limpa a sessão.
- **Testes de componente** com Testing Library e **MSW** para os componentes com regra de negócio visível: KPI com valor zero, listas vazias, chips de status nos quatro estados de escritório e nos três de execução.
- **Testes E2E com Playwright** nos quatro caminhos que o plano elege como críticos: login→dashboard, cadastrar cliente, gerar chave de agente e admin suspender escritório — contra a stack real (Postgres + API + frontend), com estado preparado pelo endpoint de seed de desenvolvimento que já existe.
- Ajustar `tsconfig.app.json` para não typecheckar arquivos de teste no `npm run build`.

## Capabilities

Esta mudança é de tooling: cria infraestrutura de teste para comportamento que já existe e já está implementado. Nenhum requisito novo é introduzido e nenhum comportamento observável do produto muda. Por isso o change declara `skip_specs: true` no seu `.openspec.yaml`, pelo mesmo critério aplicado em `criar-projeto-testes-api`.

## Impact

**Frontend**

- `ContabOne.Frontend/package.json` — dependências de teste e scripts `test`, `test:ui`, `test:e2e`
- `ContabOne.Frontend/vitest.config.ts`, `ContabOne.Frontend/playwright.config.ts` — novos
- `ContabOne.Frontend/tsconfig.app.json` — excluir arquivos de teste; novo `tsconfig.vitest.json`
- `ContabOne.Frontend/src/**/*.spec.ts` — testes unitários e de componente, ao lado do código
- `ContabOne.Frontend/src/testes/` — setup do Vitest, handlers do MSW e helpers de montagem
- `ContabOne.Frontend/e2e/` — specs do Playwright e preparação de estado
- `ContabOne.Frontend/README.md` — hoje é o texto padrão do template Vue; passa a documentar como rodar as suítes

**Dependências novas (todas de desenvolvimento)**

- `vitest`, `@vitest/ui`, `jsdom`, `@vue/test-utils`, `@testing-library/vue`, `@testing-library/user-event`, `@testing-library/jest-dom`
- `msw`
- `@playwright/test`

**Pré-requisitos operacionais para o E2E**

- Postgres do `docker-compose.yml` no ar
- API rodando em `Development` (o endpoint de seed só existe fora de produção) na porta que `ContabOne.Frontend/.env.development` já aponta
- Navegadores do Playwright instalados na máquina

**Relação com outras changes**

- Independente de `criar-projeto-testes-api`. As duas podem ser aplicadas em qualquer ordem.
- CI ficou deliberadamente de fora. Quando existir, reunirá as três suítes (Python, .NET, frontend) numa change própria.
