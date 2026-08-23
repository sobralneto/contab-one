## 1. Configuração do Vitest

- [x] 1.1 Instalar `vitest`, `@vitest/ui`, `jsdom`, `@vue/test-utils`, `@testing-library/vue`, `@testing-library/user-event` e `@testing-library/jest-dom` como dependências de desenvolvimento
- [x] 1.2 Criar `ContabOne.Frontend/vitest.config.ts` com ambiente jsdom, o alias `@` igual ao do `vite.config.ts`, e **exclusão explícita de `e2e/`**
- [x] 1.3 Criar `ContabOne.Frontend/src/testes/setup.ts` registrando os matchers do jest-dom e limpando o DOM entre casos
- [x] 1.4 Criar `ContabOne.Frontend/tsconfig.vitest.json` com os tipos globais do Vitest
- [x] 1.5 Excluir `**/*.spec.ts` de `ContabOne.Frontend/tsconfig.app.json` para o `vue-tsc -b` do build não typecheckar testes
- [x] 1.6 Adicionar os scripts `test`, `test:watch` e `test:ui` ao `package.json`
- [x] 1.7 Confirmar que `npm run build` continua verde e que `npm test` roda com a suíte ainda vazia

## 2. Composables e utilitários

Lógica pura, sem DOM — a camada mais barata e a que tem os casos mais sutis.

- [x] 2.1 `useInputMask.cnpjMask`: mascaramento progressivo em cada faixa de tamanho (2, 5, 8, 12, 14 dígitos), descarte de não-dígitos e truncamento acima de 14
- [x] 2.2 `useInputMask.parseCurrency`: os três caminhos do código — com vírgula decimal (`"R$ 1.234,56"` → `1234.56`), sem vírgula mas com dois decimais (`"99.90"` → `99.9`) e só com pontos de milhar (`"1.234"` → `1234`)
- [x] 2.3 `useInputMask.parseCurrency`: entrada vazia ou sem número devolve `0` em vez de `NaN`
- [x] 2.4 `useInputMask.currencyMask`: normaliza o espaço não-separável que `toLocaleString` insere depois de `R$`
- [x] 2.5 `useFormatters.formatRelativeTime`: as quatro faixas (`agora`, minutos, horas, dias) e o retorno para data absoluta acima de 30 dias
- [x] 2.6 `useFormatters`: entrada vazia devolve `—` em `formatCnpj`, `formatDate`, `formatDateTime` e `formatRelativeTime`
- [x] 2.7 `jwt.decodeJwt`: extrai as claims, mapeia a claim de papel na URI longa do .NET para `role`, e devolve `null` para token malformado
- [x] 2.8 `jwt.isJwtExpired`: token expirado, token válido, token sem `exp` e token ilegível — os três últimos casos decidem se a sessão é restaurada

## 3. Stores e guards

- [x] 3.1 `stores/auth`: `setSession` persiste em `sessionStorage` e `clearSession` remove
- [x] 3.2 `stores/auth`: sessão é restaurada do `sessionStorage` na criação da store quando o token é válido, e ignorada quando expirado
- [x] 3.3 `stores/auth`: `isPlatformAdmin` e `isEscritorioAdmin` para os três papéis, incluindo que `PlatformAdmin` satisfaz `isEscritorioAdmin`
- [x] 3.4 `stores/auth.canAccess`: lista de papéis vazia libera, papel ausente bloqueia
- [x] 3.5 `router/guards`: rota pública é liberada sem sessão, e usuário autenticado em `/login` é redirecionado ao dashboard
- [x] 3.6 `router/guards`: rota protegida sem sessão redireciona para login preservando o `redirect` na query
- [x] 3.7 `router/guards`: papel insuficiente para uma rota admin cai no dashboard em vez de renderizar a tela
- [x] 3.8 `router/guards`: o bootstrap tenta refresh uma única vez na primeira navegação e limpa `isInitializing` tanto no sucesso quanto na falha

## 4. MSW e o interceptor de refresh

O teste de maior valor desta change — ver `PLANO_SAAS_FRONTEND.md` §8.

- [x] 4.1 Instalar `msw` com a major fixada e criar `ContabOne.Frontend/src/testes/servidor.ts` com o servidor de mock e os handlers base
- [x] 4.2 Criar helper que reinicia o estado de módulo do `apiClient` (`vi.resetModules` + reimportação) e recria o Pinia entre casos
- [x] 4.3 Teste: o interceptor de request anexa `Authorization: Bearer` quando há token, e omite o header quando não há
- [x] 4.4 Teste: 401 dispara `POST /api/auth/refresh` e repete a requisição original com o token novo
- [x] 4.5 Teste: a requisição repetida não dispara um segundo refresh se falhar de novo (a flag `_retry` corta o laço)
- [x] 4.6 Teste: três requisições concorrentes recebendo 401 disparam **um único** refresh, e as três são repetidas com o token novo
- [x] 4.7 Teste: refresh que falha limpa a sessão e redireciona para `/login` — substituindo `window.location`, já que jsdom não implementa navegação
- [x] 4.8 Teste: erro que não é 401 (403, 500) atravessa sem tentar refresh
- [x] 4.9 Teste: `refreshAccessToken` usa axios cru e não passa pelos interceptors, para uma falha de refresh não disparar refresh de novo

## 5. Componentes com regra visível

- [x] 5.1 Criar helper de montagem que instala Pinia e o router de teste
- [x] 5.2 `KpiCard`: valor zero é renderizado como `0` e não some, número grande sai formatado em pt-BR, e as três variantes aplicam a classe correspondente
- [x] 5.3 `EstadoVazio`: renderiza a mensagem recebida
- [x] 5.4 Chip de status de escritório nos quatro estados (`Ativo`, `Inadimplente`, `Suspenso`, `Cancelado`), confirmando rótulo e classe do mapa `STATUS_ESCRITORIO` — fixa que a API serializa esse enum como **string**
- [x] 5.5 Chip de status de execução nos três estados (`Sucesso`, `Parcial`, `Falha`)
- [x] 5.6 `ListaAlertas`: lista vazia mostra estado vazio; alerta resolvido e alerta aberto são distinguíveis; resolver dispara a ação
- [x] 5.7 `UltimasExecucoes` e `RankingClientes` com lista vazia e com dados
- [x] 5.8 `ConfirmarAcao`: emite `confirm` e `cancel`, e não renderiza quando invisível
- [x] 5.9 Teste de integração de view: `ClientesView` carrega a lista via MSW, filtra pela busca e exibe o estado vazio quando não há resultado

## 6. Configuração do Playwright

- [x] 6.1 Instalar `@playwright/test` e baixar os navegadores
- [x] 6.2 Criar `ContabOne.Frontend/playwright.config.ts` com `webServer` subindo `vite dev`, `testDir: 'e2e'` e o `baseURL` correspondente
- [x] 6.3 Adicionar verificação prévia que confirma Postgres e API no ar e falha com instrução do que subir, em vez de dar timeout genérico
- [x] 6.4 Criar o helper de preparação que chama `POST /api/seed/dev` e devolve as credenciais dos três papéis
- [x] 6.5 Criar o helper de login reutilizável pelos quatro caminhos
- [x] 6.6 Adicionar o script `test:e2e` ao `package.json`

## 7. Os quatro caminhos críticos

- [x] 7.1 **Login → dashboard**: credenciais válidas entram, o dashboard carrega os KPIs, e o cookie de refresh sobrevive a um reload da página — este teste também valida a premissa de `SameSite=Strict` registrada no design
- [x] 7.2 **Login**: credenciais inválidas mostram erro e permanecem na tela de login — **defeito real descoberto e corrigido**: o 401 do login disparava o interceptor de refresh, que falhava e redirecionava para /login, engolindo a mensagem de erro. Fix em `apiClient` (client.ts): 401 de requisição SEM token não tenta refresh. Coberto por teste unitário novo em client.spec.ts
- [x] 7.3 **Cadastrar cliente**: escritório cria um cliente com código único e ele aparece na listagem
- [x] 7.4 **Cadastrar cliente**: código repetido no mesmo escritório é rejeitado com mensagem
- [x] 7.5 **Gerar chave de agente**: a chave completa é exibida uma única vez, com o aviso, e o agente aparece na lista com apenas o prefixo
- [x] 7.6 **Admin suspender escritório**: admin cria um escritório próprio para o teste, suspende, e o status reflete na listagem — não usa o escritório semeado, para não bloquear os outros testes
- [x] 7.7 Confirmar que cada teste que cria dado usa sufixo único, de forma que execuções repetidas não colidam no índice único de código por escritório

## 8. Fechamento

- [x] 8.1 Substituir o `README.md` do frontend (hoje é o texto padrão do template Vue) documentando como rodar cada suíte e os pré-requisitos do E2E
- [x] 8.2 Rodar `npm test` e confirmar a suíte rápida verde sem nenhum serviço no ar
- [x] 8.3 Subir Postgres, API em `Development` e rodar `npm run test:e2e`; confirmar os quatro caminhos verdes
- [x] 8.4 Rodar `npm run build` e confirmar que o `vue-tsc` ignora os arquivos de teste e o build continua verde
- [x] 8.5 Rodar a suíte rápida duas vezes seguidas e confirmar que não há teste dependente de ordem (estado de módulo do `apiClient`, `sessionStorage`)
